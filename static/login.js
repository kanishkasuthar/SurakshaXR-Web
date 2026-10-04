/* ========================================================
   Suraksha-XR Admin Portal Login Logic
   ======================================================== */

async function getJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

async function postJSON(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `Authentication failed (HTTP ${res.status})`);
  }
  return data;
}

// 1. Theme Management
function initTheme() {
  const saved = localStorage.getItem('suraksha_web_theme') || 'light';
  applyTheme(saved);

  const btn = document.getElementById('themeToggleBtn');
  if (btn) {
    btn.addEventListener('click', () => {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      applyTheme(isDark ? 'light' : 'dark');
    });
  }
}

function applyTheme(theme) {
  const icon = document.getElementById('themeToggleIcon');
  const text = document.getElementById('themeToggleText');
  if (theme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('suraksha_web_theme', 'dark');
    if (icon) icon.textContent = '☀️';
    if (text) text.textContent = 'Light Theme';
  } else {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('suraksha_web_theme', 'light');
    if (icon) icon.textContent = '🌙';
    if (text) text.textContent = 'Dark Theme';
  }
}

// 2. Check Backend Health
async function checkBackendStatus() {
  const pill = document.getElementById('backendStatusPill');
  const text = document.getElementById('backendStatusText');
  try {
    const status = await getJSON('/api/backend-status');
    if (status.connected) {
      pill.style.display = 'inline-flex';
      text.textContent = 'Live connection';
    } else {
      text.textContent = 'Backend Offline';
      pill.style.borderColor = 'rgba(183, 83, 69, 0.4)';
    }
  } catch (e) {
    text.textContent = 'Backend Offline';
    pill.style.borderColor = 'rgba(183, 83, 69, 0.4)';
  }
}

// 3. Handle Form Submission
const form = document.getElementById('adminLoginForm');
const alertBox = document.getElementById('loginAlert');
const submitBtn = document.getElementById('submitLoginBtn');
const usernameInput = document.getElementById('usernameInput');
const passwordInput = document.getElementById('passwordInput');
const togglePasswordBtn = document.getElementById('togglePasswordBtn');
const quickFillBtn = document.getElementById('quickFillBtn');

// Toggle Password Visibility
if (togglePasswordBtn && passwordInput) {
  togglePasswordBtn.addEventListener('click', () => {
    const isPass = passwordInput.type === 'password';
    passwordInput.type = isPass ? 'text' : 'password';
    togglePasswordBtn.textContent = isPass ? '🙈' : '👁️';
  });
}

// Quick Fill Demo Credentials
if (quickFillBtn) {
  quickFillBtn.addEventListener('click', () => {
    usernameInput.value = 'admin';
    passwordInput.value = 'admin123';
    alertBox.className = 'login-alert-box info';
    alertBox.textContent = 'Demo credentials populated: admin / admin123';
    alertBox.classList.remove('hidden');
    setTimeout(() => alertBox.classList.add('hidden'), 2500);
  });
}

// Login Submit
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    alertBox.classList.add('hidden');
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>VERIFYING SUPERVISOR ACCESS...</span>`;

    try {
      const res = await postJSON('/api/login', { username, password });
      
      // Store token
      sessionStorage.setItem('suraksha_admin_token', res.access_token || res.token || 'admin-token');
      sessionStorage.setItem('suraksha_admin_user', username);
      sessionStorage.setItem('suraksha_admin_role', res.role || 'admin');

      alertBox.className = 'login-alert-box success';
      alertBox.innerHTML = `<strong>✓ Authorization Granted:</strong> Redirecting to Command Center...`;
      alertBox.classList.remove('hidden');

      setTimeout(() => {
        window.location.href = '/';
      }, 700);

    } catch (err) {
      alertBox.className = 'login-alert-box error';
      alertBox.innerHTML = `<strong>❌ Access Denied:</strong> ${err.message || 'Invalid username or password'}`;
      alertBox.classList.remove('hidden');
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>SECURE ADMIN LOGIN</span> <span>➔</span>`;
    }
  });
}

// Check if already authenticated
if (sessionStorage.getItem('suraksha_admin_token')) {
  // Already logged in, provide prompt or auto-redirect
  // window.location.href = '/';
}

initTheme();
checkBackendStatus();
