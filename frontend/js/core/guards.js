// Route protection guards
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/auth/login';
        return false;
    }
    return true;
}

function requireRole(role) {
    if (!isAuthenticated()) {
        window.location.href = '/auth/login';
        return false;
    }
    
    if (!hasRole(role)) {
        window.location.href = '/';
        return false;
    }
    return true;
}

function requireCustomer() {
    return requireRole('customer');
}

function requirePartner() {
    return requireRole('partner');
}

function requireAdmin() {
    return requireRole('admin');
}

// Redirect if already authenticated
function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        const role = getUserRole();
        switch(role) {
            case 'customer':
                window.location.href = '/customer/dashboard';
                break;
            case 'partner':
                window.location.href = '/partner/dashboard';
                break;
            case 'admin':
                window.location.href = '/admin/dashboard';
                break;
            default:
                window.location.href = '/';
        }
        return false;
    }
    return true;
}
