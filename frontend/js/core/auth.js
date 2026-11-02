// Authentication utilities
function getAuthToken() {
    return localStorage.getItem('authToken') || localStorage.getItem('access_token');
}

function setAuthToken(token) {
    localStorage.setItem('authToken', token);
    localStorage.setItem('access_token', token);
}

function removeAuthToken() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
}

function isAuthenticated() {
    return !!getAuthToken();
}

function getUser() {
    try {
        return JSON.parse(localStorage.getItem('user') || '{}');
    } catch {
        return {};
    }
}

function getCurrentUser() {
    const user = getUser();
    return (user && (user.id || user.email)) ? user : null;
}

function getUserRole() {
    const user = getUser();
    return user.role || null;
}

function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

function logout() {
    removeAuthToken();
    localStorage.removeItem('user');
    window.location.href = '/auth/login';
}

// Check if user has permission
function hasRole(requiredRole) {
    const userRole = getUserRole();
    if (!userRole) return false;
    if (requiredRole === 'admin') {
        return userRole === 'admin' || userRole === 'system_admin';
    }
    if (requiredRole === 'partner') {
        return userRole === 'partner' || userRole === 'driver' || userRole === 'admin' || userRole === 'system_admin';
    }
    if (requiredRole === 'customer') {
        return userRole === 'customer' || userRole === 'admin' || userRole === 'system_admin';
    }
    return userRole === requiredRole;
}

function isAdmin() {
    return hasRole('admin');
}

function isCustomer() {
    return hasRole('customer');
}

function isPartner() {
    return hasRole('partner');
}

// Global toast notification fallback if main.js is not loaded
if (typeof window.showNotification !== 'function') {
    window.showNotification = function showNotification(message, type = 'info', duration = 3500) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type}`;
        toast.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;max-width:400px;padding:12px 18px;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.15);background:#1e293b;color:#fff;';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    };
}

window.getAuthToken = getAuthToken;
window.setAuthToken = setAuthToken;
window.removeAuthToken = removeAuthToken;
window.isAuthenticated = isAuthenticated;
window.getUser = getUser;
window.getCurrentUser = getCurrentUser;
window.getUserRole = getUserRole;
window.setUser = setUser;
window.logout = logout;
window.hasRole = hasRole;
window.isAdmin = isAdmin;
window.isCustomer = isCustomer;
window.isPartner = isPartner;
