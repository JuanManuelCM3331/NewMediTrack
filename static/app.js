const tokenKey = 'meditrack_token';
const userKey = 'meditrack_user';
const api = async (path, options = {}) => {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const token = localStorage.getItem(tokenKey);
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`/api${path}`, { ...options, headers });
  const body = await response.json().catch(() => ({ message: 'Respuesta inválida del servidor' }));
  if (response.status === 401) { localStorage.removeItem(tokenKey); localStorage.removeItem(userKey); if (!location.pathname.endsWith('/')) location.href = '/'; }
  if (!response.ok) throw new Error(body.message || body.detail || 'No se pudo completar la operación');
  return body;
};
const showMessage = (message, error = false) => { const node = document.querySelector('#app-message'); if (!node) return; node.textContent = message; node.classList.toggle('visible', true); node.style.background = error ? '#a54b40' : ''; setTimeout(() => node.classList.remove('visible'), 3200); };

async function handleLogin(event) {
  event.preventDefault();
  const form = event.currentTarget; const button = document.querySelector('#login-button'); const error = document.querySelector('#login-error');
  error.textContent = '';
  if (!form.reportValidity()) return;
  button.disabled = true; button.innerHTML = 'Ingresando... <span>•</span>';
  try { const body = await api('/sessions', { method: 'POST', body: JSON.stringify({ email: form.email.value, password: form.password.value }) }); localStorage.setItem(tokenKey, body.data.access_token); localStorage.setItem(userKey, JSON.stringify(body.data.user)); location.href = '/app'; }
  catch (err) { error.textContent = err.message; button.disabled = false; button.innerHTML = 'Entrar a MediTrack <span>→</span>'; }
}

async function handleRegister(event) {
  event.preventDefault();
  const form = event.currentTarget; const button = document.querySelector('#register-button'); const error = document.querySelector('#register-error');
  error.textContent = '';
  if (!form.reportValidity()) return;
  button.disabled = true; button.innerHTML = 'Creando cuenta... <span>•</span>';
  try { const body = await api('/users', { method: 'POST', body: JSON.stringify({ full_name: form.full_name.value, email: form.email.value, password: form.password.value }) }); localStorage.setItem(tokenKey, body.data.access_token); localStorage.setItem(userKey, JSON.stringify(body.data.user)); location.href = '/app'; }
  catch (err) { error.textContent = err.message; button.disabled = false; button.innerHTML = 'Crear cuenta <span>→</span>'; }
}

function toggleAuthForm(showRegister) {
  document.querySelector('#login-form').classList.toggle('form-hidden', showRegister);
  document.querySelector('#register-form').classList.toggle('form-hidden', !showRegister);
}

let currentDoses = [];
async function loadDashboard() {
  const user = JSON.parse(localStorage.getItem(userKey) || '{}');
  if (!localStorage.getItem(tokenKey)) { location.href = '/'; return; }
  document.querySelector('#user-name').textContent = user.full_name || 'Usuario'; document.querySelector('#user-role').textContent = user.role === 'admin' ? 'Administrador' : 'Usuario estándar'; document.querySelector('#welcome-name').textContent = (user.full_name || 'amigo').split(' ')[0]; document.querySelector('#user-avatar').textContent = (user.full_name || 'M').charAt(0).toUpperCase();
  const date = new Date(); document.querySelector('#today-date').textContent = date.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' }); document.querySelector('#day-name').textContent = date.toLocaleDateString('es-CO', { weekday: 'long' }).toUpperCase();
  await Promise.all([loadDoses(), loadMedications(), loadTreatments()]);
}
function renderUser(user) {
  document.querySelector('#user-name').textContent = user.full_name || 'Usuario'; document.querySelector('#user-role').textContent = user.role === 'admin' ? 'Administrador' : 'Usuario estándar'; document.querySelector('#welcome-name').textContent = (user.full_name || 'amigo').split(' ')[0]; document.querySelector('#user-avatar').textContent = (user.full_name || 'M').charAt(0).toUpperCase();
}
async function submitProfile(event) {
  event.preventDefault(); const form = event.currentTarget;
  try { const body = await api('/users/me', { method: 'PUT', body: JSON.stringify({ full_name: form.full_name.value }) }); localStorage.setItem(userKey, JSON.stringify(body.data)); renderUser(body.data); form.closest('.modal').classList.remove('open'); showMessage('Nombre actualizado correctamente'); }
  catch (err) { showMessage(err.message, true); }
}
async function loadDoses() {
  try { currentDoses = (await api('/treatments/schedule/today')).data; renderDoses(); } catch (err) { showMessage(err.message, true); }
}
function renderDoses() {
  const labels = { pending: 'Pendiente', taken: 'Tomada', snoozed: 'Pospuesta', missed: 'Omitida' }; const list = document.querySelector('#dose-list');
  list.innerHTML = currentDoses.length ? currentDoses.map(dose => `<div class="dose-item is-${dose.status}"><span class="dose-dot"></span><span class="dose-time">${new Date(dose.scheduled_at).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}</span><div class="dose-info"><strong>${dose.medication_name}</strong><span>${dose.dosage}</span></div><span class="dose-status ${dose.status}">${labels[dose.status]}</span></div>`).join('') : '<div class="empty-state">No hay dosis para hoy. Tu agenda está despejada.</div>';
  const counts = currentDoses.reduce((acc, dose) => { acc[dose.status] = (acc[dose.status] || 0) + 1; return acc; }, {}); document.querySelector('#taken-count').textContent = counts.taken || 0; document.querySelector('#pending-count').textContent = counts.pending || 0; document.querySelector('#missed-count').textContent = counts.missed || 0;
  const next = currentDoses.find(dose => dose.status === 'pending'); const card = document.querySelector('#next-dose-card'); if (next) { document.querySelector('#next-dose-title').textContent = next.medication_name; document.querySelector('#next-dose-detail').textContent = `${next.dosage} · pendiente de confirmar`; document.querySelector('#next-dose-time').textContent = new Date(next.scheduled_at).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }); } else { document.querySelector('#next-dose-title').textContent = 'Todo al día por ahora'; document.querySelector('#next-dose-detail').textContent = 'Tus próximas tomas aparecerán aquí.'; document.querySelector('#next-dose-time').textContent = '✓'; }
  const alertDose = currentDoses.find(dose => dose.status === 'pending'); const alert = document.querySelector('#dose-alert'); if (alertDose) { document.querySelector('#alert-title').textContent = `${alertDose.medication_name} · ${alertDose.dosage}`; document.querySelector('#alert-detail').textContent = `Tómala antes de ${alertDose.minutes_left ?? 0} minutos o se marcará como omitida.`; alert.dataset.doseId = alertDose.id; alert.classList.add('visible'); } else alert.classList.remove('visible');
}
async function loadMedications() { const items = (await api('/medications')).data; document.querySelector('#medication-list').innerHTML = items.length ? items.map(item => `<div class="medication-item"><div><strong>${item.name}</strong><span>${item.presentation}</span></div><span class="stock">${item.stock} disp.</span></div>`).join('') : '<div class="empty-state">Añade tu primer medicamento.</div>'; document.querySelector('#medication-select').innerHTML = items.map(item => `<option value="${item.id}">${item.name}</option>`).join(''); }
async function loadTreatments() { const items = (await api('/treatments?active=true')).data; document.querySelector('#treatment-list').innerHTML = items.length ? items.map(item => `<div class="treatment-item"><div><strong>${item.medication_name}</strong><span>${item.dosage} · ${item.schedule_times.join(', ')}</span></div><span class="stock">${item.duration_days} días</span></div>`).join('') : '<div class="empty-state">Crea una pauta para verla aquí.</div>'; }
async function loadAdminSummary() { try { const summary = (await api('/admin/summary')).data; document.querySelector('#admin-users').textContent = summary.users; document.querySelector('#admin-medications').textContent = summary.medications; document.querySelector('#admin-treatments').textContent = summary.treatments; document.querySelector('#admin-panel').classList.add('visible'); } catch (err) { showMessage(err.message, true); } }
async function submitMedication(event) { event.preventDefault(); const form = event.currentTarget; try { await api('/medications', { method: 'POST', body: JSON.stringify({ name: form.name.value, presentation: form.presentation.value, stock: Number(form.stock.value), notes: form.notes.value || null }) }); form.closest('.modal').classList.remove('open'); form.reset(); await loadMedications(); showMessage('Medicamento registrado'); } catch (err) { showMessage(err.message, true); } }
async function submitTreatment(event) { event.preventDefault(); const form = event.currentTarget; try { const times = form.schedule_times.value.split(',').map(value => value.trim()).filter(Boolean); await api('/treatments', { method: 'POST', body: JSON.stringify({ medication_id: Number(form.medication_id.value), dosage: form.dosage.value, schedule_times: times, start_date: form.start_date.value, duration_days: Number(form.duration_days.value), instructions: form.instructions.value || null }) }); form.closest('.modal').classList.remove('open'); form.reset(); await Promise.all([loadTreatments(), loadDoses()]); showMessage('Tratamiento creado'); } catch (err) { showMessage(err.message, true); } }
async function decideDose(button) { const alert = document.querySelector('#dose-alert'); try { await api(`/treatments/doses/${alert.dataset.doseId}/decision?decision=${button.dataset.decision}`, { method: 'POST' }); alert.classList.remove('visible'); await loadDoses(); showMessage(button.dataset.decision === 'taken' ? 'Dosis registrada como tomada' : 'Dosis pospuesta'); } catch (err) { showMessage(err.message, true); } }

document.addEventListener('DOMContentLoaded', () => { const login = document.querySelector('#login-form'); const register = document.querySelector('#register-form'); if (login) { login.addEventListener('submit', handleLogin); register.addEventListener('submit', handleRegister); document.querySelector('#show-register').addEventListener('click', () => toggleAuthForm(true)); document.querySelector('#show-login').addEventListener('click', () => toggleAuthForm(false)); } if (document.body.classList.contains('app-page')) { const user = JSON.parse(localStorage.getItem(userKey) || '{}'); renderUser(user); loadDashboard(); if (user.role === 'admin') loadAdminSummary(); document.querySelector('#refresh-button').addEventListener('click', loadDoses); document.querySelector('#logout-button').addEventListener('click', () => { localStorage.clear(); location.href = '/'; }); document.querySelector('#profile-button').addEventListener('click', () => { document.querySelector('#profile-name').value = user.full_name || ''; document.querySelector('#profile-modal').classList.add('open'); }); document.querySelector('#profile-form').addEventListener('submit', submitProfile); document.querySelector('#medication-form').addEventListener('submit', submitMedication); document.querySelector('#treatment-form').addEventListener('submit', submitTreatment); document.querySelectorAll('[data-modal]').forEach(button => button.addEventListener('click', () => document.querySelector(`#${button.dataset.modal}`).classList.add('open'))); document.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => button.closest('.modal').classList.remove('open'))); document.querySelectorAll('[data-decision]').forEach(button => button.addEventListener('click', () => decideDose(button))); setInterval(loadDoses, 30000); } });
