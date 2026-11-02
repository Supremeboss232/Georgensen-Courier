// MAIN.JS - Global initialization and utilities

const STORAGE_KEYS = {
  ACCESS_TOKEN: 'authToken',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
  PREFERENCES: 'preferences'
};

document.addEventListener('DOMContentLoaded', function() {
  updateNavbar();
  initializePreferences();
});

function updateNavbar() {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) || localStorage.getItem('access_token');
  let user = {};
  try {
    user = JSON.parse(localStorage.getItem(STORAGE_KEYS.USER) || '{}');
  } catch {
    user = {};
  }

  if (token && user.email) {
    const loginBtn = document.getElementById('loginBtn');
    const registerBtn = document.getElementById('registerBtn');
    const authButtons = document.querySelector('.auth-buttons');

    if (loginBtn) loginBtn.style.display = 'none';
    if (registerBtn) registerBtn.style.display = 'none';

    if (authButtons) {
      authButtons.innerHTML = `
        <li class="flex items-center gap-md" style="display: flex; gap: var(--spacing-md); align-items: center; white-space: nowrap;">
          <span>${user.email}</span>
          <button class="btn btn-sm btn-ghost" onclick="logout()" style="margin: 0;">Logout</button>
        </li>
      `;
    }
  }
}

function logout() {
  localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
  localStorage.removeItem('access_token');
  localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.USER);
  window.location.href = '/auth/login';
}

function getCurrentUser() {
  try {
    const u = JSON.parse(localStorage.getItem(STORAGE_KEYS.USER) || '{}');
    return (u && (u.id || u.email)) ? u : null;
  } catch {
    return null;
  }
}

function isAuthenticated() {
  return !!(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) || localStorage.getItem('access_token'));
}

function getAuthHeader() {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) || localStorage.getItem('access_token');
  if (token) {
    return {
      'Authorization': `Bearer ${token}`
    };
  }
  return {};
}

function initializePreferences() {
  try {
    const prefs = JSON.parse(localStorage.getItem(STORAGE_KEYS.PREFERENCES) || '{}');
    if (prefs.darkMode) {
      document.body.classList.add('dark-mode');
    }
  } catch {}
}

function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
  const prefs = JSON.parse(localStorage.getItem(STORAGE_KEYS.PREFERENCES) || '{}');
  prefs.darkMode = document.body.classList.contains('dark-mode');
  localStorage.setItem(STORAGE_KEYS.PREFERENCES, JSON.stringify(prefs));
}

function showNotification(message, type = 'info', duration = 3500) {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.style.position = 'fixed';
  toast.style.bottom = '20px';
  toast.style.right = '20px';
  toast.style.zIndex = '9999';
  toast.style.maxWidth = '400px';
  toast.style.padding = '12px 18px';
  toast.style.borderRadius = '8px';
  toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
  toast.textContent = message;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function formatCurrency(amount, currency = 'CAD') {
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2
  }).format(Number(amount || 0));
}

function formatDate(date) {
  if (!date) return 'N/A';
  return new Intl.DateTimeFormat('en-CA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(date));
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidPhone(phone) {
  return /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/im.test(phone);
}

function smoothScroll(elementId) {
  const element = document.getElementById(elementId);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' });
  }
}

function showLoadingSpinner(element) {
  if (!element) return;
  element.innerHTML = '<span class="spinner"></span>';
  element.disabled = true;
}

function hideLoadingSpinner(element, text) {
  if (!element) return;
  element.textContent = text;
  element.disabled = false;
}

function handleError(error) {
  console.error('Error:', error);
  const msg = (error && error.message) ? error.message : 'An error occurred';
  if (msg === 'Session expired. Please login again.') {
    logout();
  } else if (msg.includes('Network')) {
    showNotification('Network error. Please check your connection.', 'error');
  } else {
    showNotification(msg, 'error');
  }
}

if (typeof apiCall !== 'undefined') {
  window.apiCall = apiCall;
}
window.showNotification = showNotification;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.isAuthenticated = isAuthenticated;
window.getCurrentUser = getCurrentUser;
window.handleError = handleError;
window.logout = logout;
