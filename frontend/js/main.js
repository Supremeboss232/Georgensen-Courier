// MAIN.JS - Global initialization and utilities

// Local storage keys
const STORAGE_KEYS = {
  ACCESS_TOKEN: 'authToken',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
  PREFERENCES: 'preferences'
};

// Initialize app on page load
document.addEventListener('DOMContentLoaded', function() {
  console.log('🚀 Georgensen App Initialized');
  updateNavbar();
  initializePreferences();
});

/**
 * Update navbar based on authentication state
 */
function updateNavbar() {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  const user = JSON.parse(localStorage.getItem(STORAGE_KEYS.USER) || '{}');
  
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

/**
 * Logout user
 */
function logout() {
  localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.USER);
  alert('Logged out successfully');
  location.href = 'index.html';
}

/**
 * Get current user
 */
function getCurrentUser() {
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.USER) || '{}');
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
  return !!localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
}

/**
 * Get auth header for API calls
 */
function getAuthHeader() {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  if (token) {
    return {
      'Authorization': `Bearer ${token}`
    };
  }
  return {};
}

/**
 * Get authentication header for API calls
 * (API call function is defined in /js/core/api.js)
 */
function getAuthHeader() {
  const token = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  if (token) {
    return {
      'Authorization': `Bearer ${token}`
    };
  }
  return {};
}

/**
 * Initialize user preferences
 */
function initializePreferences() {
  const prefs = JSON.parse(localStorage.getItem(STORAGE_KEYS.PREFERENCES) || '{}');
  
  // Apply dark mode preference
  if (prefs.darkMode) {
    document.body.classList.add('dark-mode');
  }
}

/**
 * Toggle dark mode
 */
function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
  const prefs = JSON.parse(localStorage.getItem(STORAGE_KEYS.PREFERENCES) || '{}');
  prefs.darkMode = document.body.classList.contains('dark-mode');
  localStorage.setItem(STORAGE_KEYS.PREFERENCES, JSON.stringify(prefs));
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info', duration = 3000) {
  const toast = document.createElement('div');
  toast.className = `alert alert-${type}`;
  toast.style.position = 'fixed';
  toast.style.bottom = '20px';
  toast.style.right = '20px';
  toast.style.zIndex = '9999';
  toast.style.maxWidth = '400px';
  toast.textContent = message;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/**
 * Format currency
 */
function formatCurrency(amount) {
  return new Intl.NumberFormat('en-NG', {
    style: 'currency',
    currency: 'NGN',
    minimumFractionDigits: 0
  }).format(amount);
}

/**
 * Format date
 */
function formatDate(date) {
  return new Intl.DateTimeFormat('en-NG', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(date));
}

/**
 * Validate email
 */
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

/**
 * Validate phone
 */
function isValidPhone(phone) {
  return /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/im.test(phone);
}

/**
 * Scroll smooth helper
 */
function smoothScroll(elementId) {
  const element = document.getElementById(elementId);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' });
  }
}

/**
 * Loading spinner
 */
function showLoadingSpinner(element) {
  element.innerHTML = '<span class="spinner"></span>';
  element.disabled = true;
}

function hideLoadingSpinner(element, text) {
  element.textContent = text;
  element.disabled = false;
}

/**
 * Handle common errors
 */
function handleError(error) {
  console.error('Error:', error);
  
  if (error.message === 'Session expired. Please login again.') {
    logout();
  } else if (error.message.includes('Network')) {
    showNotification('Network error. Please check your connection.', 'error');
  } else {
    showNotification(error.message || 'An error occurred', 'error');
  }
}

// Export for use in other modules
window.apiCall = apiCall;
window.showNotification = showNotification;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.isAuthenticated = isAuthenticated;
window.getCurrentUser = getCurrentUser;
window.handleError = handleError;
