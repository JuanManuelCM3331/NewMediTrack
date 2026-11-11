// Devuelve el elemento o un nodo suelto, para que las vistas parciales no fallen si falta un elemento
const q = sel => document.querySelector(sel) || document.createElement('div');
const PAGE = () => document.body.dataset.page || '';

const ICON_PATHS = {
  plus: 'M12 4.5v15m7.5-7.5h-15',
  check: 'M4.5 12.75l6 6 9-13.5',
  clock: 'M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z',
  alert: 'M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z',
  logout: 'M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75',
  refresh: 'M16.023 9.348h4.992V4.356M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182',
  sparkles: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z',
  beaker: 'M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5m4.75-11.396c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5',
  note: 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z',
  trash: 'M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0',
  arrow: 'M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3',
  x: 'M6 18L18 6M6 6l12 12',
  pencil: 'M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z',
  calendar: 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5',
  clipboard: 'M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184',
  shield: 'M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z',
  info: 'M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z',
  home: 'M2.25 12l8.954-8.955a1.126 1.126 0 011.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25',
  bell: 'M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0',
  user: 'M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z'
};
const ico = (name, cls = 'h-5 w-5') =>
  `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" aria-hidden="true" class="shrink-0 ${cls}"><path stroke-linecap="round" stroke-linejoin="round" d="${ICON_PATHS[name] || ''}"/></svg>`;
function hydrateIcons(root = document) {
  root.querySelectorAll('i[data-icon]').forEach(el => {
    const tpl = document.createElement('template');
    tpl.innerHTML = ico(el.dataset.icon, el.className);
    el.replaceWith(tpl.content.firstChild);
  });
}

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

function formatScheduleDateTime(isoString) {
  if (!isoString) return '--:--';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return '--:--';
  const timeStr = date.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
  const today = new Date();
  const todayDateOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const targetDateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const diffDays = Math.round((targetDateOnly - todayDateOnly) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return timeStr;
  if (diffDays === 1) return `Mañana · ${timeStr}`;
  if (diffDays > 1 && diffDays < 7) {
    const weekday = date.toLocaleDateString('es-CO', { weekday: 'short' });
    const capitalized = weekday.charAt(0).toUpperCase() + weekday.slice(1).replace('.', '');
    return `${capitalized} · ${timeStr}`;
  }
  const dayMonth = date.toLocaleDateString('es-CO', { day: 'numeric', month: 'short' }).replace('.', '');
  return `${dayMonth} · ${timeStr}`;
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
    if (!['/', '/login'].includes(location.pathname)) {
      location.href = '/login';
    }
  }
  if (!response.ok) {
    throw new Error(body.message || body.detail || 'No se pudo completar la operación');
  }
  return body;
};

const openModal = (modal) => { modal.classList.remove('hidden'); modal.classList.add('flex'); };
const closeModal = (modal) => { modal.classList.add('hidden'); modal.classList.remove('flex'); };

const showMessage = (message, error = false) => {
  const node = q('#app-message');
  if (!node) return;
  node.textContent = message;
  node.classList.remove('opacity-0', 'translate-y-3');
  node.classList.add('opacity-100', 'translate-y-0');
  node.classList.toggle('bg-brand-dark', !error);
  node.classList.toggle('bg-coral-dark', error);
  setTimeout(() => {
    node.classList.add('opacity-0', 'translate-y-3');
    node.classList.remove('opacity-100', 'translate-y-0');
  }, 3600);
};

const DOSE_STYLES = {
  pending: { name: 'clock', box: 'bg-[#fff8e6]', icon: 'bg-[#fbe7b0] text-[#8a6416]', badge: 'bg-[#fbe7b0] text-[#7a5c10]' },
  taken: { name: 'check', box: 'bg-[#eef8f2]', icon: 'bg-brand-mint text-brand', badge: 'bg-brand-mint text-brand-dark' },
  missed: { name: 'alert', box: 'bg-[#fff1ed]', icon: 'bg-[#ffd9d0] text-coral-dark', badge: 'bg-[#ffd9d0] text-coral-dark' },
  snoozed: { name: 'clock', box: 'bg-[#eef5f9]', icon: 'bg-[#cfe3ee] text-[#2f5d75]', badge: 'bg-[#cfe3ee] text-[#2f5d75]' }
};
const EMPTY_CLASS = 'col-span-full px-2 py-8 text-center text-base text-muted';
const EDIT_BTN = 'grid h-11 w-11 shrink-0 place-items-center rounded-full bg-white/80 text-brand-dark transition hover:bg-brand-mint focus:outline-none focus:ring-4 focus:ring-brand/30';
const DELETE_BTN = 'grid h-11 w-11 shrink-0 place-items-center rounded-full bg-white/80 text-coral-dark transition hover:bg-[#ffd9d0] focus:outline-none focus:ring-4 focus:ring-coral/30';

const VIEW_MODE_KEY = 'meditrack_view_mode';

function clearSavedViewMode() {
  sessionStorage.removeItem(VIEW_MODE_KEY);
  localStorage.removeItem(VIEW_MODE_KEY);
}

function getPostAuthRoute(authResponse) {
  return authResponse?.data?.user?.role === 'admin' ? '/app' : '/app/selector';
}

async function handleLogin(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = q('#login-button');
  const error = q('#login-error');
  error.textContent = '';
  if (!form.reportValidity()) return;
  button.disabled = true;
  button.textContent = 'Ingresando...';
  try {
    const res = await api('/sessions', {
      method: 'POST',
      body: JSON.stringify({ email: form.email.value, password: form.password.value })
    });
    // Reiniciar modo guardado para que usuarios no admin elijan siempre al iniciar sesión
    clearSavedViewMode();
    // El token de autenticación se gestiona en Cookie HttpOnly (inmune a XSS)
    location.href = getPostAuthRoute(res);
  } catch (err) {
    error.textContent = err.message;
    button.disabled = false;
    button.innerHTML = `Entrar a MediTrack ${ico('arrow')}`;
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = q('#register-button');
  const error = q('#register-error');
  error.textContent = '';
  if (!form.reportValidity()) return;
  button.disabled = true;
  button.textContent = 'Creando cuenta...';
  try {
    const res = await api('/users', {
      method: 'POST',
      body: JSON.stringify({ full_name: form.full_name.value, email: form.email.value, password: form.password.value })
    });
    clearSavedViewMode();
    location.href = getPostAuthRoute(res);
  } catch (err) {
    error.textContent = err.message;
    button.disabled = false;
    button.innerHTML = `Crear cuenta ${ico('arrow')}`;
  }
}

function toggleAuthForm(showRegister) {
  q('#login-form').classList.toggle('hidden', showRegister);
  q('#register-form').classList.toggle('hidden', !showRegister);
}

let currentDoses = [];
let currentUpcomingDoses = [];
let currentMedications = [];

async function loadDashboard() {
  let user;
  try {
    // Validar sesión contra el servidor (no confía en localStorage)
    user = (await api('/users/me')).data;
    renderUser(user);
  } catch (err) {
    location.href = '/login';
    return;
  }

  const page = PAGE();

  // Control según rol
  if (user.role === 'admin') {
    // Admin skipea el selector y no muestra botón de cambiar modo
    if (page === 'selector') {
      location.href = '/app';
      return;
    }
    const switchBtn = document.querySelector('#switch-mode-btn');
    if (switchBtn) switchBtn.classList.add('hidden');
  } else {
    // Usuario estándar: panel de resumen inaccesible
    if (page === 'resumen') {
      location.href = '/app';
      return;
    }

    localStorage.removeItem(VIEW_MODE_KEY);
    const savedMode = sessionStorage.getItem(VIEW_MODE_KEY);

    // Si ingresa al panel principal sin haber elegido modo previamente, dirigir al selector
    if (page === 'panel' && !savedMode) {
      location.href = '/app/selector';
      return;
    }

    // Si guardó preferencia asistida y navega a /app, llevar a asistido
    if (page === 'panel' && savedMode === 'asistido') {
      location.href = '/app/asistido';
      return;
    }
  }

  if (page === 'selector') {
    return; // No requiere cargar dosis ni agenda
  }

  const date = new Date();
  q('#today-date').textContent = date.toLocaleDateString('es-CO', { day: '2-digit', month: 'short' });
  q('#day-name').textContent = date.toLocaleDateString('es-CO', { weekday: 'long' }).toUpperCase();
  const jobs = [loadDoses(), loadMedications(), loadTreatments()];
  if (page === 'resumen') jobs.push(loadAdminSummary());
  await Promise.all(jobs);
}

function renderUser(user) {
  const fullName = unescapeHtml(user.full_name) || 'Usuario';
  q('#user-name').textContent = fullName;
  q('#user-role').textContent = user.role === 'admin' ? 'Administrador' : 'Usuario estándar';
  q('#welcome-name').textContent = (fullName || 'amigo').split(' ')[0];
  q('#user-avatar').textContent = (fullName || 'M').charAt(0).toUpperCase();
  if (user.role === 'admin') {
    document.querySelectorAll('[data-admin-only]').forEach(el => el.classList.remove('hidden'));
  }
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
    closeModal(form.closest('.modal'));
    showMessage('Nombre actualizado correctamente');
  } catch (err) {
    showMessage(err.message, true);
  }
}

async function loadDoses() {
  try {
    const page = PAGE();
    const needsUpcoming = page === 'panel' || page === 'asistido';
    const calls = [api('/doses/today')];
    if (needsUpcoming) {
      calls.push(api('/doses/upcoming?limit=10'));
    }
    const [todayRes, upcomingRes] = await Promise.all(calls);
    currentDoses = todayRes.data || [];
    if (upcomingRes) {
      currentUpcomingDoses = upcomingRes.data || [];
    } else {
      currentUpcomingDoses = currentDoses.filter(d => d.status === 'pending' || d.status === 'snoozed');
    }
    renderDoses();
  } catch (err) {
    showMessage(err.message, true);
  }
}

function renderDoses() {
  const labels = { pending: 'Pendiente', taken: 'Tomada', snoozed: 'Pospuesta', missed: 'Omitida' };
  const list = q('#dose-list');

  list.innerHTML = currentDoses.length
    ? currentDoses.map(dose => {
        const timeStr = formatTime(dose.scheduled_at);
        const isPendingOrSnoozed = dose.status === 'pending' || dose.status === 'snoozed';
        const canTake = isPendingOrSnoozed && (dose.can_take !== undefined ? dose.can_take : true);
        const actionBtn = canTake
          ? `<button class="inline-flex min-h-[48px] shrink-0 items-center justify-center gap-2 rounded-full bg-brand px-6 text-base font-bold text-white shadow transition hover:bg-brand-dark focus:outline-none focus:ring-4 focus:ring-brand/30 max-sm:w-full" type="button" data-take-dose="${dose.id}" title="Marcar esta dosis como tomada">${ico('check')}Tomar</button>`
          : '';
        const st = DOSE_STYLES[dose.status] || DOSE_STYLES.pending;
        return `
          <article class="flex flex-wrap items-center gap-4 rounded-3xl p-4 transition hover:shadow-soft sm:p-5 ${st.box}">
            <span class="grid h-14 w-14 shrink-0 place-items-center rounded-full ${st.icon}">${ico(st.name, 'h-7 w-7')}</span>
            <div class="min-w-0 flex-1 basis-44">
              <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
                <span class="font-serif text-2xl font-semibold leading-none">${timeStr}</span>
                <span class="rounded-full px-3 py-0.5 text-sm font-bold ${st.badge}">${labels[dose.status] || dose.status}</span>
              </div>
              <strong class="mt-1 block text-lg [overflow-wrap:anywhere] font-bold leading-snug">${escapeHtml(dose.medication_name)}</strong>
              <span class="block text-base text-muted [overflow-wrap:anywhere]">${escapeHtml(dose.dosage)}</span>
            </div>
            <div class="flex w-full flex-wrap gap-2 sm:w-auto sm:flex-col sm:items-stretch">
              ${actionBtn}
              <button class="inline-flex min-h-[48px] shrink-0 items-center justify-center gap-2 rounded-full bg-white/90 px-5 text-base font-bold text-brand-dark transition hover:bg-brand-mint focus:outline-none focus:ring-4 focus:ring-brand/30 max-sm:flex-1" type="button" data-dose-details="${dose.id}">${ico('info')}Ver detalles</button>
            </div>
          </article>
        `;
      }).join('')
    : `<div class="${EMPTY_CLASS}">No hay dosis para hoy. Tu agenda está despejada.</div>`;

  const counts = currentDoses.reduce((acc, dose) => {
    acc[dose.status] = (acc[dose.status] || 0) + 1;
    return acc;
  }, {});
  q('#taken-count').textContent = counts.taken || 0;
  q('#pending-count').textContent = (counts.pending || 0) + (counts.snoozed || 0);
  q('#missed-count').textContent = counts.missed || 0;

  // Próxima dosis en general (mostrada en el banner superior)
  const next = currentUpcomingDoses[0];
  const card = q('#next-dose-card');
  if (next) {
    const nextMedName = unescapeHtml(next.medication_name);
    const nextDosage = unescapeHtml(next.dosage);
    q('#next-dose-title').textContent = nextMedName;
    const formattedSchedule = formatScheduleDateTime(next.scheduled_at);

    const schedDate = new Date(next.scheduled_at);
    const today = new Date();
    const todayDateOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    const targetDateOnly = new Date(schedDate.getFullYear(), schedDate.getMonth(), schedDate.getDate());
    const diffDays = Math.round((targetDateOnly - todayDateOnly) / (1000 * 60 * 60 * 24));

    if (next.is_due) {
      q('#next-dose-detail').textContent = `${nextDosage} · ¡Es hora de tomarla!`;
    } else if (next.status === 'snoozed') {
      q('#next-dose-detail').textContent = `${nextDosage} · pospuesta hasta las ${formatTime(next.scheduled_at)}`;
    } else if (diffDays === 0) {
      q('#next-dose-detail').textContent = `${nextDosage} · programada para hoy`;
    } else if (diffDays === 1) {
      q('#next-dose-detail').textContent = `${nextDosage} · programada para mañana`;
    } else {
      q('#next-dose-detail').textContent = `${nextDosage} · programada para el ${formattedSchedule}`;
    }
    q('#next-dose-time').textContent = formattedSchedule;
  } else {
    q('#next-dose-title').textContent = 'Todo al día por ahora';
    q('#next-dose-detail').textContent = 'Tus próximas tomas aparecerán aquí.';
    q('#next-dose-time').innerHTML = ico('check', 'h-8 w-8');
  }

  // Siguientes dosis a consumir en general (las 3 más próximas sin contar la del banner)
  const followingContainer = document.querySelector('#following-doses-list');
  if (followingContainer) {
    const followingDoses = currentUpcomingDoses.slice(1, 4);
    followingContainer.innerHTML = followingDoses.length
      ? followingDoses.map(dose => {
          const timeStr = formatScheduleDateTime(dose.scheduled_at);
          const isPendingOrSnoozed = dose.status === 'pending' || dose.status === 'snoozed';
          const canTake = isPendingOrSnoozed && (dose.can_take !== undefined ? dose.can_take : false);
          const actionBtn = canTake
            ? `<button class="inline-flex min-h-[44px] flex-1 items-center justify-center gap-1.5 rounded-full bg-brand px-4 text-sm font-bold text-white shadow transition hover:bg-brand-dark focus:outline-none focus:ring-4 focus:ring-brand/30" type="button" data-take-dose="${dose.id}" title="Marcar esta dosis como tomada">${ico('check', 'h-4 w-4')}Tomar</button>`
            : '';
          const st = DOSE_STYLES[dose.status] || DOSE_STYLES.pending;
          return `
            <article class="flex flex-col justify-between rounded-3xl p-5 shadow-soft transition hover:-translate-y-0.5 hover:shadow-lift ${st.box}">
              <div>
                <div class="flex items-center justify-between gap-2">
                  <span class="inline-flex items-center gap-2 font-serif text-lg font-semibold leading-none">
                    <span class="grid h-8 w-8 place-items-center rounded-full ${st.icon}">${ico(st.name, 'h-4 w-4')}</span>
                    ${timeStr}
                  </span>
                  <span class="rounded-full px-3 py-0.5 text-xs font-bold ${st.badge}">${labels[dose.status] || dose.status}</span>
                </div>
                <div class="my-4 min-w-0">
                  <strong class="block text-lg font-bold leading-snug [overflow-wrap:anywhere]">${escapeHtml(dose.medication_name)}</strong>
                  <span class="block text-sm text-muted [overflow-wrap:anywhere]">${escapeHtml(dose.dosage)}</span>
                </div>
              </div>
              <div class="mt-2 flex flex-wrap items-center gap-2 border-t border-line/60 pt-3">
                ${actionBtn}
                <button class="inline-flex min-h-[44px] flex-1 items-center justify-center gap-1.5 rounded-full bg-white/90 px-4 text-sm font-bold text-brand-dark shadow-sm transition hover:bg-brand-mint focus:outline-none focus:ring-4 focus:ring-brand/30" type="button" data-dose-details="${dose.id}">
                  ${ico('info', 'h-4 w-4')}Detalles
                </button>
              </div>
            </article>
          `;
        }).join('')
      : `
        <div class="col-span-full rounded-3xl bg-white p-7 text-center shadow-soft">
          <span class="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-[#f1f5f1] text-brand-dark">${ico('check', 'h-6 w-6')}</span>
          <p class="font-serif text-lg font-semibold text-ink">Sin más tomas pendientes</p>
          <p class="mt-1 text-sm text-muted">No hay más medicamentos programados a continuación.</p>
        </div>
      `;
  }

  if (PAGE() === 'asistido') {
    renderAsistidoView();
  }

  const alertDose = currentDoses.find(dose => dose.is_due);
  const alert = q('#dose-alert');
  if (alertDose) {
    q('#alert-title').textContent = `${unescapeHtml(alertDose.medication_name)} · ${unescapeHtml(alertDose.dosage)}`;
    const mins = alertDose.minutes_left ?? 0;
    q('#alert-detail').textContent = `Tómala antes de ${mins} ${mins === 1 ? 'minuto' : 'minutos'} o se marcará como omitida.`;
    alert.dataset.doseId = alertDose.id;
    alert.classList.remove('hidden');
    alert.classList.add('flex');
  } else {
    alert.classList.add('hidden');
    alert.classList.remove('flex');
  }
}

async function loadMedications() {
  if (!['medicamentos', 'tratamientos'].includes(PAGE())) return;
  const items = (await api('/medications')).data || [];
  currentMedications = items;
  q('#medication-list').innerHTML = items.length
    ? items.map(item => {
        const low = item.stock <= 5;
        return `
        <article class="flex items-start gap-4 rounded-3xl bg-[#fff8e8] p-4 transition hover:shadow-soft sm:p-5">
          <span class="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-[#fbe7b0] text-[#8a6416]">${ico('beaker', 'h-6 w-6')}</span>
          <div class="min-w-0 flex-1">
            <strong class="block text-lg [overflow-wrap:anywhere] font-bold leading-snug">${escapeHtml(item.name)}</strong>
            <p class="text-base text-muted [overflow-wrap:anywhere]">${escapeHtml(item.presentation)} · <span class="font-bold ${low ? 'text-coral-dark' : 'text-brand-dark'}">${item.stock} disp.${low ? ' (poco stock)' : ''}</span></p>
          </div>
          <div class="flex shrink-0 gap-1.5">
            <button class="${EDIT_BTN}" type="button" data-edit-medication="${item.id}" title="Editar existencias y nota" aria-label="Editar ${escapeHtml(item.name)}">${ico('pencil', 'h-5 w-5')}</button>
            <button class="${DELETE_BTN}" type="button" data-delete-medication="${item.id}" title="Eliminar medicamento" aria-label="Eliminar ${escapeHtml(item.name)}">${ico('trash', 'h-5 w-5')}</button>
          </div>
        </article>`;
      }).join('')
    : `<div class="${EMPTY_CLASS}">Añade tu primer medicamento.</div>`;

  q('#medication-select').innerHTML = items.map(item => `
    <option value="${item.id}">${escapeHtml(item.name)}</option>
  `).join('');
}

async function loadTreatments() {
  if (PAGE() !== 'tratamientos') return;
  const items = (await api('/treatments?active=true')).data || [];
  q('#treatment-list').innerHTML = items.length
    ? items.map(item => `
        <article class="flex items-start gap-4 rounded-3xl bg-[#eef5f9] p-4 transition hover:shadow-soft sm:p-5">
          <span class="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-[#cfe3ee] text-[#2f5d75]">${ico('clipboard', 'h-6 w-6')}</span>
          <div class="min-w-0 flex-1">
            <strong class="block text-lg [overflow-wrap:anywhere] font-bold leading-snug">${escapeHtml(item.medication_name)}</strong>
            <p class="text-base text-muted [overflow-wrap:anywhere]">${escapeHtml(item.dosage)} · <span class="font-bold text-[#2f5d75]">${item.duration_days} días</span></p>
            <p class="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-sm font-semibold text-ink">${ico('clock', 'h-4 w-4 text-[#2f5d75]')}${(item.schedule_times || []).map(t => escapeHtml(t)).join(' · ')}</p>
          </div>
          <button class="${DELETE_BTN}" type="button" data-delete-treatment="${item.id}" title="Eliminar tratamiento" aria-label="Eliminar tratamiento de ${escapeHtml(item.medication_name)}">${ico('trash', 'h-5 w-5')}</button>
        </article>
      `).join('')
    : `<div class="${EMPTY_CLASS}">Crea una pauta para verla aquí.</div>`;
}

function openDoseDetails(doseId) {
  const dose = currentDoses.find(d => String(d.id) === String(doseId))
            || currentUpcomingDoses.find(d => String(d.id) === String(doseId));
  if (!dose) return;
  q('#details-title').textContent = unescapeHtml(dose.medication_name);
  q('#details-sub').textContent = `${unescapeHtml(dose.dosage)} · ${formatScheduleDateTime(dose.scheduled_at)}`;
  [['#details-notes', dose.notes, 'Sin nota registrada.'], ['#details-instructions', dose.instructions, 'Sin indicaciones registradas.']].forEach(([sel, value, empty]) => {
    const node = q(sel);
    const text = unescapeHtml(value).trim();
    node.textContent = text || empty;
    node.classList.toggle('italic', !text);
    node.classList.toggle('text-muted', !text);
  });
  openModal(q('#details-modal'));
}

function openMedicationEdit(medicationId) {
  const med = currentMedications.find(m => String(m.id) === String(medicationId));
  if (!med) return;
  q('#edit-med-id').value = med.id;
  q('#edit-med-name').textContent = unescapeHtml(med.name);
  q('#edit-med-stock').value = med.stock;
  q('#edit-med-notes').value = unescapeHtml(med.notes);
  openModal(q('#medication-edit-modal'));
}

async function submitMedicationEdit(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const id = q('#edit-med-id').value;
  try {
    await api(`/medications/${id}`, {
      method: 'PUT',
      body: JSON.stringify({
        stock: Number(q('#edit-med-stock').value),
        notes: q('#edit-med-notes').value.trim() || null
      })
    });
    closeModal(form.closest('.modal'));
    await loadMedications();
    showMessage('Medicamento actualizado');
  } catch (err) {
    showMessage(err.message, true);
  }
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
    q('#admin-users').textContent = summary.users;
    q('#admin-medications').textContent = summary.medications;
    q('#admin-treatments').textContent = summary.treatments;
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
    closeModal(form.closest('.modal'));
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
    closeModal(form.closest('.modal'));
    form.reset();
    await Promise.all([loadTreatments(), loadDoses()]);
    showMessage('Tratamiento creado');
  } catch (err) {
    showMessage(err.message, true);
  }
}

function renderAsistidoView() {
  const next = currentUpcomingDoses[0];
  const heroContent = q('#asistido-hero-content');
  const heroEmpty = q('#asistido-hero-empty');
  const heroTime = q('#asistido-hero-time');
  const heroTitle = q('#asistido-hero-title');
  const heroDetail = q('#asistido-hero-detail');
  const heroInstr = q('#asistido-hero-instructions');
  const takeBtn = q('#asistido-take-btn');
  const snoozeBtn = q('#asistido-snooze-btn');
  const missBtn = q('#asistido-miss-btn');
  const waitMsg = q('#asistido-hero-wait-msg');

  if (next) {
    heroContent.classList.remove('hidden');
    heroEmpty.classList.add('hidden');
    heroTime.textContent = formatScheduleDateTime(next.scheduled_at);
    heroTitle.textContent = unescapeHtml(next.medication_name);

    const canAct = Boolean(next.can_take);
    let detailText = unescapeHtml(next.dosage);
    if (next.is_due) {
      detailText += ' · ¡Es hora de tu toma!';
    } else if (next.status === 'snoozed') {
      detailText += ' · Pospuesta';
    } else if (canAct) {
      detailText += ' · Dentro del horario de toma';
    } else {
      detailText += ' · Próxima dosis (en espera de horario)';
    }
    heroDetail.textContent = detailText;

    const notesOrInstr = [unescapeHtml(next.instructions), unescapeHtml(next.notes)].filter(Boolean).join(' · ');
    if (notesOrInstr) {
      heroInstr.textContent = `Indicaciones: ${notesOrInstr}`;
      heroInstr.classList.remove('hidden');
    } else {
      heroInstr.classList.add('hidden');
    }

    takeBtn.disabled = !canAct;
    snoozeBtn.disabled = !canAct;
    missBtn.disabled = !canAct;

    takeBtn.dataset.doseId = next.id;
    snoozeBtn.dataset.doseId = next.id;
    missBtn.dataset.doseId = next.id;

    if (waitMsg) {
      if (!canAct) {
        waitMsg.classList.remove('hidden');
        takeBtn.title = 'Disponible 15 minutos antes de la hora';
        snoozeBtn.title = 'Disponible 15 minutos antes de la hora';
        missBtn.title = 'Disponible 15 minutos antes de la hora';
      } else {
        waitMsg.classList.add('hidden');
        takeBtn.title = 'Marcar como tomada';
        snoozeBtn.title = 'Posponer 10 minutos';
        missBtn.title = 'Marcar como no tomada';
      }
    }
  } else {
    heroContent.classList.add('hidden');
    heroEmpty.classList.remove('hidden');
    heroTime.textContent = '✓ Al día';
    if (waitMsg) waitMsg.classList.add('hidden');
  }

  const followingContainer = document.querySelector('#asistido-following-list');
  if (followingContainer) {
    const followingDoses = currentUpcomingDoses.slice(1, 6);
    const labels = { pending: 'Pendiente', taken: 'Tomada', snoozed: 'Pospuesta', missed: 'Omitida' };
    followingContainer.innerHTML = followingDoses.length
      ? followingDoses.map(dose => {
          const timeStr = formatScheduleDateTime(dose.scheduled_at);
          const st = DOSE_STYLES[dose.status] || DOSE_STYLES.pending;
          const notesOrInstr = [unescapeHtml(dose.instructions), unescapeHtml(dose.notes)].filter(Boolean).join(' · ');
          const noteHtml = notesOrInstr
            ? `<p class="mt-2 text-base text-muted [overflow-wrap:anywhere]">${ico('note', 'inline mr-1 h-4 w-4 text-brand')} ${escapeHtml(notesOrInstr)}</p>`
            : '';
          const canAct = Boolean(dose.can_take);
          const actionHtml = canAct
            ? `
              <div class="flex flex-wrap gap-2.5 sm:flex-col">
                <button type="button" data-asistido-action="taken" data-dose-id="${dose.id}" class="inline-flex min-h-[50px] flex-1 items-center justify-center gap-2 rounded-full bg-brand px-5 text-base font-bold text-white shadow transition hover:bg-brand-dark focus:outline-none focus:ring-4 focus:ring-brand/30">
                  ${ico('check', 'h-5 w-5')}Me la tomé
                </button>
                <button type="button" data-asistido-action="snoozed" data-dose-id="${dose.id}" class="inline-flex min-h-[50px] flex-1 items-center justify-center gap-2 rounded-full bg-[#fff2cb] px-5 text-base font-bold text-[#8a6416] transition hover:bg-[#fae4a7] focus:outline-none focus:ring-4 focus:ring-[#8a6416]/30">
                  ${ico('clock', 'h-5 w-5')}Posponer
                </button>
                <button type="button" data-asistido-action="missed" data-dose-id="${dose.id}" class="inline-flex min-h-[50px] flex-1 items-center justify-center gap-2 rounded-full bg-[#fee2e2] px-5 text-base font-bold text-[#991b1b] transition hover:bg-[#fecaca] focus:outline-none focus:ring-4 focus:ring-[#991b1b]/30">
                  ${ico('x', 'h-5 w-5')}No tomada
                </button>
              </div>
            `
            : `
              <div class="flex items-center">
                <span class="inline-flex items-center gap-1.5 rounded-full bg-[#f1f5f1] px-4 py-2.5 text-sm font-semibold text-muted">
                  ${ico('clock', 'h-4 w-4 text-brand')} Esperando horario
                </span>
              </div>
            `;
          return `
            <article class="flex flex-col justify-between gap-4 rounded-[2rem] p-6 shadow-soft transition hover:shadow-lift sm:flex-row sm:items-center ${st.box}">
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-3">
                  <span class="inline-flex items-center gap-2 font-serif text-2xl font-bold leading-none text-ink">
                    <span class="grid h-9 w-9 place-items-center rounded-full ${st.icon}">${ico(st.name, 'h-5 w-5')}</span>
                    ${timeStr}
                  </span>
                  <span class="rounded-full px-3.5 py-1 text-sm font-bold ${st.badge}">${labels[dose.status] || dose.status}</span>
                </div>
                <strong class="mt-3 block text-2xl font-bold leading-snug [overflow-wrap:anywhere] text-ink">${escapeHtml(dose.medication_name)}</strong>
                <p class="mt-0.5 text-lg font-semibold text-brand [overflow-wrap:anywhere]">${escapeHtml(dose.dosage)}</p>
                ${noteHtml}
              </div>
              ${actionHtml}
            </article>
          `;
        }).join('')
      : `
        <div class="rounded-3xl bg-white p-8 text-center shadow-soft">
          <span class="mx-auto mb-3 grid h-14 w-14 place-items-center rounded-full bg-brand-mint text-brand text-2xl">${ico('check', 'h-7 w-7')}</span>
          <p class="font-serif text-2xl font-semibold text-ink">Sin más tomas por hoy</p>
          <p class="mt-1 text-base text-muted">No tienes más dosis pendientes programadas a continuación.</p>
        </div>
      `;
  }
}

async function decideDoseById(doseId, decision) {
  if (!doseId) return;
  try {
    const res = await api(`/doses/${doseId}/decision?decision=${decision}`, { method: 'POST' });
    const alert = q('#dose-alert');
    if (alert) {
      alert.classList.add('hidden');
      alert.classList.remove('flex');
    }
    await Promise.all([loadDoses(), loadMedications()]);
    let defaultMsg = 'Dosis registrada';
    if (decision === 'taken') defaultMsg = 'Dosis registrada como tomada';
    else if (decision === 'snoozed') defaultMsg = 'Dosis pospuesta 10 minutos';
    else if (decision === 'missed') defaultMsg = 'Dosis registrada como no tomada';
    showMessage(res.message || defaultMsg);
  } catch (err) {
    showMessage(err.message, true);
  }
}

async function decideDose(button) {
  const alert = q('#dose-alert');
  const doseId = alert.dataset.doseId;
  if (!doseId) return;
  await decideDoseById(doseId, button.dataset.decision);
}

async function takeDoseInline(doseId) {
  await decideDoseById(doseId, 'taken');
}

document.addEventListener('DOMContentLoaded', () => {
  hydrateIcons();
  const login = document.querySelector('#login-form');
  const register = document.querySelector('#register-form');
  if (login) {
    login.addEventListener('submit', handleLogin);
    register.addEventListener('submit', handleRegister);
    q('#show-register').addEventListener('click', () => toggleAuthForm(true));
    q('#show-login').addEventListener('click', () => toggleAuthForm(false));
    if (location.hash === '#registro') toggleAuthForm(true);

    // Botones para autorrellenar credenciales de prueba (admin y usuario)
    document.querySelectorAll('[data-demo-email]').forEach(btn => {
      btn.addEventListener('click', () => {
        const emailInput = document.querySelector('#email');
        const passInput = document.querySelector('#password');
        const err = document.querySelector('#login-error');
        const notice = document.querySelector('#demo-fill-notice');
        if (emailInput && passInput) {
          emailInput.value = btn.dataset.demoEmail || '';
          passInput.value = btn.dataset.demoPassword || '';
          if (err) err.textContent = '';
          emailInput.dispatchEvent(new Event('input', { bubbles: true }));
          passInput.dispatchEvent(new Event('input', { bubbles: true }));

          if (notice) {
            notice.textContent = `Credenciales de ${btn.dataset.demoRole || 'prueba'} completadas`;
            notice.className = 'mt-2.5 text-center text-xs font-semibold text-brand';
          }

          emailInput.classList.add('ring-2', 'ring-brand');
          setTimeout(() => emailInput.classList.remove('ring-2', 'ring-brand'), 600);

          const submitBtn = document.querySelector('#login-button');
          if (submitBtn) submitBtn.focus();
        }
      });
    });
  }

  // Botones de selección de modo (Adulto Mayor vs Cuidador)
  document.querySelectorAll('[data-select-mode]').forEach(btn => {
    btn.addEventListener('click', () => {
      const mode = btn.dataset.selectMode;
      localStorage.removeItem(VIEW_MODE_KEY);
      sessionStorage.setItem(VIEW_MODE_KEY, mode);
      location.href = mode === 'asistido' ? '/app/asistido' : '/app';
    });
  });

  // Botones de acción directa en modo asistido
  const asistidoTake = document.querySelector('#asistido-take-btn');
  const asistidoSnooze = document.querySelector('#asistido-snooze-btn');
  const asistidoMiss = document.querySelector('#asistido-miss-btn');
  if (asistidoTake) {
    asistidoTake.addEventListener('click', (e) => {
      if (asistidoTake.disabled) {
        showMessage('Aún no estás en el rango de tiempo para tomar este medicamento', true);
        return;
      }
      const id = e.currentTarget.dataset.doseId;
      if (id) decideDoseById(id, 'taken');
    });
  }
  if (asistidoSnooze) {
    asistidoSnooze.addEventListener('click', (e) => {
      if (asistidoSnooze.disabled) {
        showMessage('Aún no estás en el rango de tiempo para posponer este medicamento', true);
        return;
      }
      const id = e.currentTarget.dataset.doseId;
      if (id) decideDoseById(id, 'snoozed');
    });
  }
  if (asistidoMiss) {
    asistidoMiss.addEventListener('click', (e) => {
      if (asistidoMiss.disabled) {
        showMessage('Aún no estás en el rango de tiempo para este medicamento', true);
        return;
      }
      const id = e.currentTarget.dataset.doseId;
      if (id) decideDoseById(id, 'missed');
    });
  }

  if (document.body.classList.contains('app-page')) {
    loadDashboard();

    q('#refresh-button').addEventListener('click', async () => {
      await Promise.all([loadDoses(), loadMedications()]);
      showMessage('Agenda actualizada');
    });

    q('#logout-button').addEventListener('click', async () => {
      clearSavedViewMode();
      try {
        await api('/sessions/logout', { method: 'POST' });
      } catch (err) {
        // En caso de falla de red, redirigir igualmente
      }
      location.href = '/login';
    });

    q('#profile-button').addEventListener('click', () => {
      q('#profile-name').value = q('#user-name').textContent;
      openModal(q('#profile-modal'));
    });

    q('#profile-form').addEventListener('submit', submitProfile);
    q('#medication-form').addEventListener('submit', submitMedication);
    q('#treatment-form').addEventListener('submit', submitTreatment);
    q('#medication-edit-form').addEventListener('submit', submitMedicationEdit);

    document.querySelectorAll('[data-modal]').forEach(btn => {
      btn.addEventListener('click', () => openModal(q(`#${btn.dataset.modal}`)));
    });

    document.querySelectorAll('[data-close]').forEach(btn => {
      btn.addEventListener('click', () => closeModal(btn.closest('.modal')));
    });

    document.querySelectorAll('[data-decision]').forEach(btn => {
      btn.addEventListener('click', () => decideDose(btn));
    });

    document.addEventListener('click', event => {
      const asistidoActionBtn = event.target.closest('[data-asistido-action]');
      if (asistidoActionBtn) {
        decideDoseById(asistidoActionBtn.dataset.doseId, asistidoActionBtn.dataset.asistidoAction);
        return;
      }

      const takeInlineBtn = event.target.closest('[data-take-dose]');
      if (takeInlineBtn) {
        takeDoseInline(takeInlineBtn.dataset.takeDose);
        return;
      }
      const detailsBtn = event.target.closest('[data-dose-details]');
      if (detailsBtn) {
        openDoseDetails(detailsBtn.dataset.doseDetails);
        return;
      }
      const editBtn = event.target.closest('[data-edit-medication]');
      if (editBtn) {
        openMedicationEdit(editBtn.dataset.editMedication);
        return;
      }
      const medicationButton = event.target.closest('[data-delete-medication]');
      const treatmentButton = event.target.closest('[data-delete-treatment]');
      if (medicationButton) deleteMedication(medicationButton);
      if (treatmentButton) deleteTreatment(treatmentButton);
    });

    if (PAGE() !== 'selector') {
      setInterval(loadDoses, 15000);
    }
  }
});
