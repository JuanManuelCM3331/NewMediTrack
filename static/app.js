function unescapeHtml(text) {
  if (text === null || text === undefined) return '';
  return String(text)
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#x27;/g, "'")
    .replace(/&#039;/g, "'")
    .replace(/&amp;/g, '&');
}

function escapeHtml(text) {
  if (text === null || text === undefined) return '';
  return unescapeHtml(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatTime(isoString) {
  if (!isoString) return '--:--';
  const date = new Date(isoString);
  return isNaN(date.getTime()) ? '--:--' : date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
}

// Cliente API con soporte nativo para Cookies HttpOnly seguras
const api = async (path, options = {}) => {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const response = await fetch(`/api${path}`, {
    ...options,
    headers,
    credentials: 'same-origin', // Envía cookies HttpOnly automáticamente en el mismo origen
  });
  const body = await response.json().catch(() => ({ message: 'Respuesta inválida del servidor' }));
  if (response.status === 401) {
    if (!location.pathname.endsWith('/')) {
      location.href = '/';
    }
  }
  if (!response.ok) {
    throw new Error(body.message || body.detail || 'No se pudo completar la operación');
  }
  return body;
};

const showMessage = (message, error = false) => {
  const node = document.querySelector('#app-message');
  if (!node) return;
  node.textContent = message;
  node.classList.toggle('visible', true);
  node.style.background = error ? '#a54b40' : '';
  setTimeout(() => node.classList.remove('visible'), 3600);
};

async function handleLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = document.querySelector('#login-button');
  const error = document.querySelector('#login-error');
  error.textContent = '';
  if (!form.reportValidity()) return;
  button.disabled = true;
  button.innerHTML = 'Ingresando... <span>•</span>';
  try {
    await api('/sessions', {
      method: 'POST',
      body: JSON.stringify({ email: form.email.value, password: form.password.value })
    });
    // El token de autenticación se gestiona en Cookie HttpOnly (inmune a XSS)
    location.href = '/app';
  } catch (err) {
    error.textContent = err.message;
    button.disabled = false;
    button.innerHTML = 'Entrar a MediTrack <span>→</span>';
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = document.querySelector('#register-button');
  const error = document.querySelector('#register-error');
  error.textContent = '';
  if (!form.reportValidity()) return;
  button.disabled = true;
  button.innerHTML = 'Creando cuenta... <span>•</span>';
  try {
    await api('/users', {
      method: 'POST',
      body: JSON.stringify({ full_name: form.full_name.value, email: form.email.value, password: form.password.value })
    });
    location.href = '/app';
  } catch (err) {
    error.textContent = err.message;
    button.disabled = false;
    button.innerHTML = 'Crear cuenta <span>→</span>';
  }
}

function toggleAuthForm(showRegister) {
  document.querySelector('#login-form').classList.toggle('form-hidden', showRegister);
  document.querySelector('#register-form').classList.toggle('form-hidden', !showRegister);
}

let currentDoses = [];

async function loadDashboard() {
  try {
    // Validar sesión contra el servidor (no confía en localStorage)
    const res = await api('/users/me');
    const user = res.data;
    renderUser(user);
    if (user.role === 'admin') {
      loadAdminSummary();
    }
  } catch (err) {
    location.href = '/';
    return;
  }

  const date = new Date();
  document.querySelector('#today-date').textContent = date.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' });
  document.querySelector('#day-name').textContent = date.toLocaleDateString('es-CO', { weekday: 'long' }).toUpperCase();
  await Promise.all([loadDoses(), loadMedications(), loadTreatments()]);
}

function renderUser(user) {
  const fullName = unescapeHtml(user.full_name) || 'Usuario';
  document.querySelector('#user-name').textContent = fullName;
  document.querySelector('#user-role').textContent = user.role === 'admin' ? 'Administrador' : 'Usuario estándar';
  document.querySelector('#welcome-name').textContent = (fullName || 'amigo').split(' ')[0];
  document.querySelector('#user-avatar').textContent = (fullName || 'M').charAt(0).toUpperCase();
}

async function submitProfile(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const body = await api('/users/me', {
      method: 'PUT',
      body: JSON.stringify({ full_name: form.full_name.value })
    });
    renderUser(body.data);
    form.closest('.modal').classList.remove('open');
    showMessage('Nombre actualizado correctamente');
  } catch (err) {
    showMessage(err.message, true);
  }
}

async function loadDoses() {
  try {
    const res = await api('/doses/today');
    currentDoses = res.data || [];
    renderDoses();
  } catch (err) {
    showMessage(err.message, true);
  }
}

function renderDoses() {
  const labels = { pending: 'Pendiente', taken: 'Tomada', snoozed: 'Pospuesta', missed: 'Omitida' };
  const list = document.querySelector('#dose-list');

  list.innerHTML = currentDoses.length
    ? currentDoses.map(dose => {
        const timeStr = formatTime(dose.scheduled_at);
        const canTake = dose.status === 'pending' || dose.status === 'snoozed';
        const actionBtn = canTake
          ? `<button class="button-take-inline" type="button" data-take-dose="${dose.id}" title="Marcar esta dosis como tomada">✓ Tomar</button>`
          : '';
        return `
          <div class="dose-item is-${dose.status}">
            <span class="dose-dot"></span>
            <span class="dose-time">${timeStr}</span>
            <div class="dose-info">
              <strong>${escapeHtml(dose.medication_name)}</strong>
              <span>${escapeHtml(dose.dosage)}</span>
            </div>
            <span class="dose-status ${dose.status}">${labels[dose.status] || dose.status}</span>
            ${actionBtn}
          </div>
        `;
      }).join('')
    : '<div class="empty-state">No hay dosis para hoy. Tu agenda está despejada.</div>';

  const counts = currentDoses.reduce((acc, dose) => {
    acc[dose.status] = (acc[dose.status] || 0) + 1;
    return acc;
  }, {});
  document.querySelector('#taken-count').textContent = counts.taken || 0;
  document.querySelector('#pending-count').textContent = (counts.pending || 0) + (counts.snoozed || 0);
  document.querySelector('#missed-count').textContent = counts.missed || 0;

  const next = currentDoses.find(dose => dose.status === 'pending' || dose.status === 'snoozed');
  const card = document.querySelector('#next-dose-card');
  if (next) {
    const nextMedName = unescapeHtml(next.medication_name);
    const nextDosage = unescapeHtml(next.dosage);
    document.querySelector('#next-dose-title').textContent = nextMedName;
    const nextTimeStr = formatTime(next.scheduled_at);
    if (next.is_due) {
      document.querySelector('#next-dose-detail').textContent = `${nextDosage} · ¡Es hora de tomarla!`;
    } else if (next.status === 'snoozed') {
      document.querySelector('#next-dose-detail').textContent = `${nextDosage} · pospuesta hasta las ${nextTimeStr}`;
    } else {
      document.querySelector('#next-dose-detail').textContent = `${nextDosage} · programada para hoy`;
    }
    document.querySelector('#next-dose-time').textContent = nextTimeStr;
  } else {
    document.querySelector('#next-dose-title').textContent = 'Todo al día por ahora';
    document.querySelector('#next-dose-detail').textContent = 'Tus próximas tomas aparecerán aquí.';
    document.querySelector('#next-dose-time').textContent = '✓';
  }

  const alertDose = currentDoses.find(dose => dose.is_due);
  const alert = document.querySelector('#dose-alert');
  if (alertDose) {
    document.querySelector('#alert-title').textContent = `${unescapeHtml(alertDose.medication_name)} · ${unescapeHtml(alertDose.dosage)}`;
    const mins = alertDose.minutes_left ?? 0;
    document.querySelector('#alert-detail').textContent = `Tómala antes de ${mins} ${mins === 1 ? 'minuto' : 'minutos'} o se marcará como omitida.`;
    alert.dataset.doseId = alertDose.id;
    alert.classList.add('visible');
  } else {
    alert.classList.remove('visible');
  }
}

async function loadMedications() {
  const items = (await api('/medications')).data || [];
  document.querySelector('#medication-list').innerHTML = items.length
    ? items.map(item => `
        <div class="medication-item">
          <div>
            <strong>${escapeHtml(item.name)}</strong>
            <span>${escapeHtml(item.presentation)}</span>
          </div>
          <span class="stock">${item.stock} disp.</span>
          <button class="delete-button" type="button" data-delete-medication="${item.id}" title="Eliminar medicamento" aria-label="Eliminar ${escapeHtml(item.name)}">Eliminar</button>
        </div>
      `).join('')
    : '<div class="empty-state">Añade tu primer medicamento.</div>';

  document.querySelector('#medication-select').innerHTML = items.map(item => `
    <option value="${item.id}">${escapeHtml(item.name)}</option>
  `).join('');
}

async function loadTreatments() {
  const items = (await api('/treatments?active=true')).data || [];
  document.querySelector('#treatment-list').innerHTML = items.length
    ? items.map(item => `
        <div class="treatment-item">
          <div>
            <strong>${escapeHtml(item.medication_name)}</strong>
            <span>${escapeHtml(item.dosage)} · ${(item.schedule_times || []).map(t => escapeHtml(t)).join(', ')}</span>
          </div>
          <span class="stock">${item.duration_days} días</span>
          <button class="delete-button" type="button" data-delete-treatment="${item.id}" title="Eliminar tratamiento" aria-label="Eliminar tratamiento de ${escapeHtml(item.medication_name)}">Eliminar</button>
        </div>
      `).join('')
    : '<div class="empty-state">Crea una pauta para verla aquí.</div>';
}

async function deleteMedication(button) {
  if (!confirm('¿Eliminar este medicamento? También se eliminarán sus tratamientos relacionados.')) return;
  try {
    await api(`/medications/${button.dataset.deleteMedication}`, { method: 'DELETE' });
    await Promise.all([loadMedications(), loadTreatments(), loadDoses()]);
    showMessage('Medicamento eliminado');
  } catch (err) {
    showMessage(err.message, true);
  }
}

async function deleteTreatment(button) {
  if (!confirm('¿Eliminar este tratamiento?')) return;
  try {
    await api(`/treatments/${button.dataset.deleteTreatment}`, { method: 'DELETE' });
    await Promise.all([loadTreatments(), loadDoses()]);
    showMessage('Tratamiento eliminado');
  } catch (err) {
    showMessage(err.message, true);
  }
}

async function loadAdminSummary() {
  try {
    const summary = (await api('/admin/summary')).data;
    document.querySelector('#admin-users').textContent = summary.users;
    document.querySelector('#admin-medications').textContent = summary.medications;
    document.querySelector('#admin-treatments').textContent = summary.treatments;
    document.querySelector('#admin-panel').classList.add('visible');
  } catch (err) {
    showMessage(err.message, true);
  }
}

async function submitMedication(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    await api('/medications', {
      method: 'POST',
      body: JSON.stringify({
        name: form.name.value,
        presentation: form.presentation.value,
        stock: Number(form.stock.value),
        notes: form.notes.value || null
      })
    });
    form.closest('.modal').classList.remove('open');
    form.reset();
    await loadMedications();
    showMessage('Medicamento registrado');
  } catch (err) {
    showMessage(err.message, true);
  }
}

async function submitTreatment(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    const times = form.schedule_times.value.split(',').map(v => v.trim()).filter(Boolean);
    await api('/treatments', {
      method: 'POST',
      body: JSON.stringify({
        medication_id: Number(form.medication_id.value),
        dosage: form.dosage.value,
        schedule_times: times,
        start_date: form.start_date.value,
        duration_days: Number(form.duration_days.value),
        instructions: form.instructions.value || null
      })
    });
    form.closest('.modal').classList.remove('open');
    form.reset();
    await Promise.all([loadTreatments(), loadDoses()]);
    showMessage('Tratamiento creado');
  } catch (err) {
    showMessage(err.message, true);
  }
}

async function decideDose(button) {
  const alert = document.querySelector('#dose-alert');
  const doseId = alert.dataset.doseId;
  if (!doseId) return;
  try {
    const res = await api(`/doses/${doseId}/decision?decision=${button.dataset.decision}`, { method: 'POST' });
    alert.classList.remove('visible');
    await Promise.all([loadDoses(), loadMedications()]);
    showMessage(res.message || (button.dataset.decision === 'taken' ? 'Dosis registrada como tomada' : 'Dosis pospuesta 10 minutos'));
  } catch (err) {
    showMessage(err.message, true);
  }
}

async function takeDoseInline(doseId) {
  try {
    const res = await api(`/doses/${doseId}/decision?decision=taken`, { method: 'POST' });
    await Promise.all([loadDoses(), loadMedications()]);
    showMessage(res.message || 'Dosis registrada como tomada');
  } catch (err) {
    showMessage(err.message, true);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const login = document.querySelector('#login-form');
  const register = document.querySelector('#register-form');
  if (login) {
    login.addEventListener('submit', handleLogin);
    register.addEventListener('submit', handleRegister);
    document.querySelector('#show-register').addEventListener('click', () => toggleAuthForm(true));
    document.querySelector('#show-login').addEventListener('click', () => toggleAuthForm(false));
  }

  if (document.body.classList.contains('app-page')) {
    loadDashboard();

    document.querySelector('#refresh-button').addEventListener('click', async () => {
      await Promise.all([loadDoses(), loadMedications()]);
      showMessage('Agenda actualizada');
    });

    document.querySelector('#logout-button').addEventListener('click', async () => {
      try {
        await api('/sessions/logout', { method: 'POST' });
      } catch (err) {
        // En caso de falla de red, redirigir igualmente
      }
      location.href = '/';
    });

    document.querySelector('#profile-button').addEventListener('click', () => {
      document.querySelector('#profile-name').value = document.querySelector('#user-name').textContent;
      document.querySelector('#profile-modal').classList.add('open');
    });

    document.querySelector('#profile-form').addEventListener('submit', submitProfile);
    document.querySelector('#medication-form').addEventListener('submit', submitMedication);
    document.querySelector('#treatment-form').addEventListener('submit', submitTreatment);

    document.querySelectorAll('[data-modal]').forEach(btn => {
      btn.addEventListener('click', () => document.querySelector(`#${btn.dataset.modal}`).classList.add('open'));
    });

    document.querySelectorAll('[data-close]').forEach(btn => {
      btn.addEventListener('click', () => btn.closest('.modal').classList.remove('open'));
    });

    document.querySelectorAll('[data-decision]').forEach(btn => {
      btn.addEventListener('click', () => decideDose(btn));
    });

    document.addEventListener('click', event => {
      const takeInlineBtn = event.target.closest('[data-take-dose]');
      if (takeInlineBtn) {
        takeDoseInline(takeInlineBtn.dataset.takeDose);
        return;
      }
      const medicationButton = event.target.closest('[data-delete-medication]');
      const treatmentButton = event.target.closest('[data-delete-treatment]');
      if (medicationButton) deleteMedication(medicationButton);
      if (treatmentButton) deleteTreatment(treatmentButton);
    });

    setInterval(loadDoses, 15000);
  }
});
