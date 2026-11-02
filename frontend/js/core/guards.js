// Route protection guards and dynamic portal layout helpers
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

function guardCustomerPortal() {
    return requireCustomer();
}

function guardPartnerPortal() {
    return requirePartner();
}

function guardAdminPortal() {
    return requireAdmin();
}

function loadNavbar() {
    const navContainer = document.getElementById('navbar-container');
    if (navContainer && !navContainer.innerHTML.trim()) {
        const user = (typeof getUser === 'function' ? getUser() : {}) || {};
        navContainer.innerHTML = `
            <div class="navbar navbar-expand-lg navbar-dark bg-dark px-4 py-2">
                <a class="navbar-brand fw-bold text-white text-decoration-none" href="/customer/dashboard.html">
                    Georgensen Courier — Customer Portal
                </a>
                <div class="ms-auto d-flex align-items-center gap-3 flex-wrap">
                    <a class="text-light text-decoration-none" href="/customer/dashboard.html">Dashboard</a>
                    <a class="text-light text-decoration-none" href="/customer/new-order.html">New Shipment</a>
                    <a class="text-light text-decoration-none" href="/customer/orders.html">My Orders</a>
                    <a class="text-light text-decoration-none" href="/customer/tracking.html">Track</a>
                    <a class="text-light text-decoration-none" href="/customer/invoices.html">Invoices</a>
                    <a class="text-light text-decoration-none" href="/customer/support.html">Support</a>
                    <a class="text-light text-decoration-none" href="/customer/profile.html">Profile</a>
                    <span class="badge bg-secondary">${user.email || 'Customer'}</span>
                    <button class="btn btn-sm btn-outline-light" onclick="logout()">Logout</button>
                </div>
            </div>
        `;
    }
    if (typeof updateNavbar === 'function') {
        updateNavbar();
    }
}

function loadFooter() {
    const footerContainer = document.getElementById('footer-container');
    if (footerContainer && !footerContainer.innerHTML.trim()) {
        footerContainer.innerHTML = `
            <div class="text-center text-muted py-4 mt-5 border-top">
                <small>&copy; 2026 Georgensen Courier Inc. All rights reserved. | <a href="/privacy.html">Privacy</a> | <a href="/terms.html">Terms</a> | <a href="/contact.html">Support</a></small>
            </div>
        `;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('navbar-container')) {
        loadNavbar();
    }
    if (document.getElementById('footer-container')) {
        loadFooter();
    }
});

function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        const role = getUserRole();
        switch (role) {
            case 'customer':
                window.location.href = '/customer/dashboard';
                break;
            case 'partner':
            case 'driver':
                window.location.href = '/partner/partner-dashboard.html';
                break;
            case 'admin':
            case 'system_admin':
                window.location.href = '/admin/dashboard';
                break;
            default:
                window.location.href = '/';
        }
        return false;
    }
    return true;
}

window.requireAuth = requireAuth;
window.requireRole = requireRole;
window.requireCustomer = requireCustomer;
window.requirePartner = requirePartner;
window.requireAdmin = requireAdmin;
window.guardCustomerPortal = guardCustomerPortal;
window.guardPartnerPortal = guardPartnerPortal;
window.guardAdminPortal = guardAdminPortal;
window.loadNavbar = loadNavbar;
window.loadFooter = loadFooter;
window.redirectIfAuthenticated = redirectIfAuthenticated;
