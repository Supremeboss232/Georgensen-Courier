/**
 * Admin Common Utilities
 * Shared functionality for all admin pages
 */

/**
 * Load admin navbar component
 */
async function loadAdminNavbar() {
    try {
        const response = await fetch('../../components/admin-navbar.html');
        const html = await response.text();
        const container = document.getElementById('navbar-container');
        if (container) {
            container.innerHTML = html;
            initializeAdminNavbar();
        }
    } catch (error) {
        console.error('Error loading admin navbar:', error);
    }
}

/**
 * Initialize admin navbar functionality
 */
function initializeAdminNavbar() {
    // Get user info from localStorage
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    // Set user name and role
    document.getElementById('adminName').textContent = user.name || user.email || 'Admin User';
    document.getElementById('userInitial').textContent = (user.name || user.email || 'A')[0].toUpperCase();
    document.getElementById('adminRole').textContent = `${user.role || 'User'}`;
    
    // Set active nav link based on current page
    const currentPage = getCurrentPageName();
    document.querySelectorAll('.nav-link').forEach(link => {
        const page = link.getAttribute('data-page');
        if (page === currentPage) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Add event listeners to close dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        const userMenu = document.getElementById('userMenu');
        const userAvatar = document.querySelector('.user-avatar');
        
        if (!event.target.closest('.user-info-section')) {
            userMenu.classList.remove('show');
        }
    });
}

/**
 * Get current page name from URL or filename
 */
function getCurrentPageName() {
    const pathname = window.location.pathname;
    
    if (pathname.includes('/orders')) return 'orders';
    if (pathname.includes('/partners')) return 'partners';
    if (pathname.includes('/users')) return 'users';
    if (pathname.includes('/disputes')) return 'disputes';
    if (pathname.includes('/reports')) return 'reports';
    if (pathname.includes('/dashboard') || pathname === '/admin/') return 'dashboard';
    
    return 'dashboard';
}

/**
 * Toggle user menu visibility
 */
function toggleUserMenu() {
    const userMenu = document.getElementById('userMenu');
    userMenu.classList.toggle('show');
}

/**
 * Toggle admin search bar
 */
function toggleSearch() {
    const searchBar = document.getElementById('searchBar');
    searchBar.style.display = searchBar.style.display === 'none' ? 'block' : 'none';
    
    if (searchBar.style.display === 'block') {
        document.getElementById('adminSearch').focus();
    }
}

/**
 * Handle admin search
 */
function handleAdminSearch() {
    const query = document.getElementById('adminSearch').value.toLowerCase();
    const resultsDiv = document.getElementById('searchResults');
    
    if (query.length < 2) {
        resultsDiv.innerHTML = '';
        return;
    }

    // Simulate search results - in production would call API
    const mockResults = [
        { type: 'order', id: 'ORD-2026-001', title: 'Order #ORD-2026-001', meta: 'To: Acme Corp' },
        { type: 'order', id: 'ORD-2026-002', title: 'Order #ORD-2026-002', meta: 'To: Global Tech' },
        { type: 'partner', id: 'PART-001', title: 'FastRoute Logistics', meta: 'North America' },
        { type: 'dispute', id: 'DSP-2026-001', title: 'Dispute #DSP-2026-001', meta: 'High Severity' }
    ];

    const filtered = mockResults.filter(result => 
        result.title.toLowerCase().includes(query) ||
        result.meta.toLowerCase().includes(query)
    );

    if (filtered.length === 0) {
        resultsDiv.innerHTML = '<div style="padding: 1rem; color: #666;">No results found</div>';
        return;
    }

    resultsDiv.innerHTML = filtered.map(result => `
        <div class="search-result-item" onclick="navigateToResult('${result.type}', '${result.id}')">
            <span class="search-result-icon">
                ${result.type === 'order' ? '📦' : result.type === 'partner' ? '🤝' : '⚖️'}
            </span>
            <div class="search-result-content">
                <div class="search-result-title">${result.title}</div>
                <div class="search-result-meta">${result.meta}</div>
            </div>
        </div>
    `).join('');
}

/**
 * Navigate to search result
 */
function navigateToResult(type, id) {
    let url = '/admin/';
    if (type === 'order') {
        url += `orders?open=${id}`;
    } else if (type === 'partner') {
        url += `partners?partner=${id}`;
    } else if (type === 'dispute') {
        url += `disputes?open=${id}`;
    }
    window.location.href = url;
}

/**
 * Toggle notifications
 */
function toggleNotifications() {
    alert('Notifications panel - To be implemented');
}

/**
 * Open admin settings
 */
function openSettings() {
    alert('Settings page - To be implemented');
}

/**
 * Logout admin user
 */
function logoutAdmin() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        window.location.href = '/auth/login';
    }
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
        color: white;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 2000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Format currency
 */
function formatCurrency(amount, currency = 'USD') {
    const formatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    });
    return formatter.format(amount);
}

/**
 * Format date
 */
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Initialize page on DOMContentLoaded
 */
function initializeAdminPage() {
    // Load navbar
    if (document.getElementById('navbar-container')) {
        loadAdminNavbar();
    }

    // Check authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/auth/login';
    }
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAdminPage);
} else {
    initializeAdminPage();
}

/**
 * Initialize admin page on DOMContentLoaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Load navbar if container exists
    if (document.getElementById('navbar-container')) {
        loadAdminNavbar();
    }
});
