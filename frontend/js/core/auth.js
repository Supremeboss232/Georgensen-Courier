// Authentication utilities
function getAuthToken() {
    return localStorage.getItem('authToken');
}

function setAuthToken(token) {
    localStorage.setItem('authToken', token);
}

function removeAuthToken() {
    localStorage.removeItem('authToken');
}

function isAuthenticated() {
    return !!getAuthToken();
}

function getUserRole() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return user.role || null;
}

function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

function getUser() {
    return JSON.parse(localStorage.getItem('user') || '{}');
}

function logout() {
    removeAuthToken();
    localStorage.removeItem('user');
    window.location.href = '/auth/login';
}

// Check if user has permission
function hasRole(requiredRole) {
    const userRole = getUserRole();
    return userRole === requiredRole;
}

// Check if user is admin
function isAdmin() {
    return hasRole('admin');
}

// Check if user is customer
function isCustomer() {
    return hasRole('customer');
}

// Check if user is partner
function isPartner() {
    return hasRole('partner');
}
