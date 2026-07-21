// Georgensen Admin Dashboard - Enhanced Logistics
let currentRegion = 'all';
let currentCurrency = 'USD';
let dashboardData = null;
let exhangeRates = {
    USD: 1.0,
    EUR: 0.92,
    CAD: 1.36,
    AED: 3.67
};

const currencySymbols = {
    USD: '$',
    EUR: '€',
    CAD: 'C$',
    AED: 'د.إ'
};

const regions = [
    { id: 'all', name: '🌍 All Regions', color: '#667eea' },
    { id: 'north_america', name: '🇺🇸 North America', color: '#764ba2' },
    { id: 'europe', name: '🇪🇺 Europe', color: '#f093fb' },
    { id: 'asia_pacific', name: '🌏 Asia Pacific', color: '#4facfe' },
    { id: 'middle_east', name: '🇦🇪 Middle East', color: '#43e97b' },
    { id: 'latin_america', name: '🇧🇷 Latin America', color: '#fa709a' }
];

document.addEventListener('DOMContentLoaded', async function() {
    if (!requireAdmin()) return;
    
    // Initialize region selectors
    initializeRegionSelectors();
    
    // Load system health
    loadSystemHealth();
    
    // Load compliance alerts
    loadComplianceAlerts();
    
    // Load dashboard data
    await loadDashboardData();
    
    // Setup tracking search
    document.getElementById('globalTrackingSearch').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performTrackingSearch();
    });
});

function initializeRegionSelectors() {
    const container = document.getElementById('regionSelectors');
    container.innerHTML = '';
    
    regions.forEach(region => {
        const button = document.createElement('button');
        button.className = `region-badge ${region.id === 'all' ? 'active' : ''}`;
        button.textContent = region.name;
        button.onclick = () => selectRegion(region.id);
        container.appendChild(button);
    });
}

function selectRegion(regionId) {
    currentRegion = regionId;
    
    // Update UI
    document.querySelectorAll('.region-badge').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update selected region name
    const regionLabel = regions.find(r => r.id === regionId)?.name || 'All Regions';
    document.getElementById('selectedRegionName').textContent = regionLabel.replace(/^[🌍🇺🇸🇪🇺🌏🇦🇪🇧🇷]\s+/, '');
    
    // Reload data for selected region
    loadDashboardData();
}

async function loadDashboardData() {
    try {
        const data = await getWithAuth('/admin/dashboard');
        dashboardData = data;
        
        // Filter data if region selected
        let filteredData = currentRegion === 'all' ? data : filterByRegion(data, currentRegion);
        
        // Update standard KPIs
        updateKPIs(filteredData);
        
        // Update logistics-specific KPIs
        updateLogisticsKPIs(filteredData);
        
        // Load and render orders
        loadOrders(filteredData.orders || []);
        
        // Update charts
        updateCharts(filteredData);
        
    } catch (error) {
        console.error('Failed to load admin dashboard:', error);
        showErrorState();
    }
}

function updateKPIs(data) {
    // Total Orders
    const totalOrders = data.orders?.total || 0;
    document.getElementById('totalOrders').textContent = totalOrders.toLocaleString();
    
    // Active Partners
    const activePartners = data.users?.partners || 0;
    document.getElementById('activePartners').textContent = activePartners.toLocaleString();
    
    // Revenue (Today) - with multi-currency
    const revenue = data.revenue?.total || 0;
    const convertedRevenue = revenue * exhangeRates[currentCurrency];
    document.getElementById('todayRevenue').textContent = `${currencySymbols[currentCurrency]}${convertedRevenue.toFixed(2)}`;
    
    // Support Tickets
    const tickets = data.support_tickets || 0;
    document.getElementById('supportTickets').textContent = tickets.toLocaleString();
}

function updateLogisticsKPIs(data) {
    // Shipments in Transit
    const inTransit = data.orders?.in_transit || 0;
    document.getElementById('shipmentsInTransit').textContent = inTransit.toLocaleString();
    
    // Customs Clearance Holds
    const customsHolds = data.orders?.customs_hold || 0;
    document.getElementById('customsHolds').textContent = customsHolds.toLocaleString();
    
    // SLA Breach Risk
    const slaBreach = data.orders?.sla_breach_risk || 0;
    document.getElementById('slaBreachRisk').textContent = slaBreach.toLocaleString();
    
    // On-Time Rate
    const onTimeRate = data.orders?.on_time_rate || 0;
    document.getElementById('onTimeRate').textContent = `${onTimeRate.toFixed(1)}%`;
}

function loadOrders(orders) {
    const tbody = document.getElementById('ordersTableBody');
    if (!tbody || !orders || orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No active orders</td></tr>';
        return;
    }
    
    tbody.innerHTML = '';
    orders.forEach(order => {
        const convertedRevenue = (order.revenue || 0) * exhangeRates[currentCurrency];
        const slaClass = order.sla_risk ? (order.sla_risk === 'critical' ? 'danger' : 'warning') : 'success';
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${order.tracking_id || 'N/A'}</strong></td>
            <td>${order.region || 'N/A'}</td>
            <td>${order.customer || 'N/A'}</td>
            <td><span class="badge bg-info">${order.status || 'Unknown'}</span></td>
            <td>${order.eta || '---'}</td>
            <td>${currencySymbols[currentCurrency]}${convertedRevenue.toFixed(2)}</td>
            <td><span class="badge bg-${slaClass}">${order.sla_risk || 'On Track'}</span></td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="viewOrder('${order.tracking_id}')">
                    <i class="fas fa-eye"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function updateCharts(data) {
    // Orders by Region Chart
    const ordersCtx = document.getElementById('ordersChart');
    if (ordersCtx && window.Chart) {
        new Chart(ordersCtx, {
            type: 'doughnut',
            data: {
                labels: regions.slice(1).map(r => r.name.split(' ')[1]),
                datasets: [{
                    data: [
                        data.orders?.delivery?.north_america || 0,
                        data.orders?.delivery?.europe || 0,
                        data.orders?.delivery?.asia || 0,
                        data.orders?.delivery?.middle_east || 0,
                        data.orders?.delivery?.latin_america || 0
                    ],
                    backgroundColor: regions.slice(1).map(r => r.color)
                }]
            },
            options: { responsive: true, maintainAspectRatio: true }
        });
    }
    
    // Revenue Trend Chart
    const revenueCtx = document.getElementById('revenueChart');
    if (revenueCtx && window.Chart) {
        const revenueData = data.revenue_trend || [0, 0, 0, 0, 0, 0, 0];
        const convertedRevenueData = revenueData.map(r => (r || 0) * exhangeRates[currentCurrency]);
        
        new Chart(revenueCtx, {
            type: 'line',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: `Revenue (${currentCurrency})`,
                    data: convertedRevenueData,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: { responsive: true, maintainAspectRatio: true }
        });
    }
}

function loadSystemHealth() {
    // Simulated system health check
    const healthChecks = {
        'trackerHealth': { status: 'healthy', text: 'Healthy' },
        'webhookHealth': { status: 'healthy', text: 'Healthy' },
        'dbHealth': { status: 'healthy', text: 'Healthy' },
        'lastSync': { status: 'info', text: 'Just now' }
    };
    
    Object.entries(healthChecks).forEach(([id, info]) => {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = info.text;
            el.parentElement.querySelector('.health-status').className = 
                `health-status status-${info.status === 'info' ? 'healthy' : info.status}`;
        }
    });
}

function loadComplianceAlerts() {
    // Load compliance alerts from backend or local state
    const alerts = [
        {
            type: 'warning',
            icon: 'exclamation-circle',
            title: 'Partner Insurance Expiring',
            description: 'Driver ID-3452 (Europe region) has insurance expiring in 5 days'
        },
        {
            type: 'warning',
            icon: 'file-alt',
            title: 'Missing VAT Documentation',
            description: '2 partners in Middle East are missing required VAT certificates'
        }
    ];
    
    const container = document.getElementById('complianceAlertsContainer');
    if (alerts.length === 0) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = alerts.map(alert => `
        <div class="compliance-alert">
            <i class="fas fa-${alert.icon}"></i>
            <strong>${alert.title}</strong><br/>
            <small>${alert.description}</small>
        </div>
    `).join('');
}

function performTrackingSearch() {
    const trackingNumber = document.getElementById('globalTrackingSearch').value.trim();
    if (!trackingNumber) {
        alert('Please enter a tracking number');
        return;
    }
    
    // Navigate to order details
    window.location.href = `/admin/orders?tracking=${trackingNumber}`;
}

function changeCurrency(currency) {
    currentCurrency = currency;
    loadDashboardData(); // Refresh with new currency
}

function filterByRegion(data, region) {
    // Filter data by selected region
    if (region === 'all') return data;
    
    // Would filter orders and related data by region
    return data;
}

function viewOrder(trackingId) {
    window.location.href = `/admin/orders/${trackingId}`;
}

function showErrorState() {
    document.getElementById('totalOrders').textContent = '---';
    document.getElementById('activePartners').textContent = '---';
    document.getElementById('todayRevenue').textContent = '---';
    document.getElementById('supportTickets').textContent = '---';
    document.getElementById('shipmentsInTransit').textContent = '---';
    document.getElementById('customsHolds').textContent = '---';
    document.getElementById('slaBreachRisk').textContent = '---';
    document.getElementById('onTimeRate').textContent = '---';
}

// Helper function to format numbers
function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

// ================== ADMIN COMMON FUNCTIONS ==================

/**
 * Get current page name from URL
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
    const mockResults = [
        { type: 'order', id: 'ORD-2026-001', title: 'Order #ORD-2026-001', meta: 'To: Acme Corp' },
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
    if (type === 'order') url += `orders?open=${id}`;
    else if (type === 'partner') url += `partners?partner=${id}`;
    else if (type === 'dispute') url += `disputes?open=${id}`;
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
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), duration);
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
 * Initialize navbar on page load
 */
(function() {
    function initNavbar() {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        if (document.getElementById('adminName')) {
            document.getElementById('adminName').textContent = user.name || user.email || 'Admin User';
            document.getElementById('userInitial').textContent = (user.name || user.email || 'A')[0].toUpperCase();
            document.getElementById('adminRole').textContent = `${user.role || 'User'}`;
        }
        
        const currentPage = getCurrentPageName();
        document.querySelectorAll('.nav-link').forEach(link => {
            const page = link.getAttribute('data-page');
            if (page === currentPage) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
        
        document.addEventListener('click', function(event) {
            const userMenu = document.getElementById('userMenu');
            if (!event.target.closest('.user-info-section')) {
                userMenu.classList.remove('show');
            }
        });
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNavbar);
    } else {
        initNavbar();
    }
})();
