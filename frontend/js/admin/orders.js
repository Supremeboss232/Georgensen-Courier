// Regional definitions with colors and emojis
const REGIONS = {
    north_america: { name: '🇺🇸 North America', color: '#3498db', emoji: '🇺🇸', hub: 'Toronto Hub' },
    europe: { name: '🇪🇺 Europe', color: '#9b59b6', emoji: '🇪🇺', hub: 'Rotterdam Hub' },
    asia_pacific: { name: '🌏 Asia Pacific', color: '#e74c3c', emoji: '🌏', hub: 'Singapore Hub' },
    middle_east: { name: '🇦🇪 Middle East', color: '#f39c12', emoji: '🇦🇪', hub: 'Dubai Logistics City' },
    africa: { name: '🇿🇦 Africa', color: '#16a085', emoji: '🇿🇦', hub: 'Johannesburg Hub' },
    latin_america: { name: '🇧🇷 Latin America', color: '#c0392b', emoji: '🇧🇷', hub: 'São Paulo Hub' }
};

// Currency exchange rates (to USD base)
const EXCHANGE_RATES = {
    USD: 1.0,
    EUR: 0.92,
    CAD: 1.36,
    AED: 3.67
};

// Status badge styles
const STATUS_STYLES = {
    pending: { bg: 'status-pending', label: 'Pending' },
    confirmed: { bg: 'status-confirmed', label: 'Confirmed' },
    in_transit: { bg: 'status-in-transit', label: 'In Transit' },
    delivered: { bg: 'status-delivered', label: 'Delivered' },
    cancelled: { bg: 'status-cancelled', label: 'Cancelled' }
};

// Customs status styles
const CUSTOMS_STYLES = {
    clear: { bg: 'customs-clear', label: '✓ Cleared', icon: '✓' },
    pending: { bg: 'customs-pending', label: '⏳ Pending', icon: '⏳' },
    hold: { bg: 'customs-hold', label: '🔴 Hold', icon: '🔴' },
    cleared: { bg: 'customs-cleared', label: '✓ Cleared', icon: '✓' }
};

// Global state
let allOrders = [];
let filteredOrders = [];
let selectedOrders = new Set();
let currentOrder = null;

/**
 * Initialize orders page on load
 */
document.addEventListener('DOMContentLoaded', () => {
    loadOrders();
});

/**
 * Load orders from API and populate table
 */
async function loadOrders() {
    try {
        const response = await apiCall('/admin/shipments', 'GET', null, { skipErrorNotification: true });
        
        if (response && Array.isArray(response)) {
            allOrders = response.map(order => ({
                ...order,
                region: order.region || 'north_america',
                customs_status: order.customs_status || 'pending',
                hub: REGIONS[order.region || 'north_america'].hub,
                route_type: order.route_type || (order.region !== order.dest_region ? 'International' : 'Domestic')
            }));
            
            filteredOrders = [...allOrders];
            renderOrderTable();
            updateOrderCount();
        }
    } catch (error) {
        console.error('Error loading orders:', error);
        // Show mock data for demo
        createMockOrders();
    }
}

/**
 * Create mock orders for demonstration
 */
function createMockOrders() {
    const mockData = [
        { id: 'ORD-2026-001', tracking_number: 'TRK001', customer: 'Acme Corp', region: 'north_america', dest_region: 'europe', status: 'in_transit', amount_usd: 1250, customs_status: 'cleared', created_at: new Date(Date.now() - 2*24*60*60*1000) },
        { id: 'ORD-2026-002', tracking_number: 'TRK002', customer: 'Global Tech', region: 'europe', dest_region: 'asia_pacific', status: 'confirmed', amount_usd: 890, customs_status: 'pending', created_at: new Date(Date.now() - 1*24*60*60*1000) },
        { id: 'ORD-2026-003', tracking_number: 'TRK003', customer: 'Fast Foods Intl', region: 'asia_pacific', dest_region: 'middle_east', status: 'pending', amount_usd: 2340, customs_status: 'hold', created_at: new Date(Date.now() - 12*60*60*1000) },
        { id: 'ORD-2026-004', tracking_number: 'TRK004', customer: 'Emirates Supply', region: 'middle_east', dest_region: 'africa', status: 'delivered', amount_usd: 650, customs_status: 'cleared', created_at: new Date(Date.now() - 5*24*60*60*1000) },
        { id: 'ORD-2026-005', tracking_number: 'TRK005', customer: 'African Exports', region: 'africa', dest_region: 'north_america', status: 'in_transit', amount_usd: 3100, customs_status: 'pending', created_at: new Date(Date.now() - 3*24*60*60*1000) },
        { id: 'ORD-2026-006', tracking_number: 'TRK006', customer: 'Brazilian Foods', region: 'latin_america', dest_region: 'north_america', status: 'confirmed', amount_usd: 1875, customs_status: 'cleared', created_at: new Date() },
    ];

    allOrders = mockData.map(order => ({
        ...order,
        hub: REGIONS[order.region].hub,
        route_type: order.region !== order.dest_region ? 'International' : 'Domestic',
        hs_code: 'HS621711',
        declared_value: order.amount_usd,
        origin_timezone: 'EST',
        dest_timezone: 'CET'
    }));

    filteredOrders = [...allOrders];
    renderOrderTable();
    updateOrderCount();
}

/**
 * Convert amount based on selected currency
 */
function convertAmount(amountUsd, currency) {
    const rate = EXCHANGE_RATES[currency] || 1.0;
    return (amountUsd * rate).toFixed(2);
}

/**
 * Get currency symbol
 */
function getCurrencySymbol(currency) {
    const symbols = { USD: '$', EUR: '€', CAD: 'C$', AED: 'د.إ' };
    return symbols[currency] || '$';
}

/**
 * Render order table with current filtered data
 */
function renderOrderTable() {
    const tbody = document.getElementById('ordersTableBody');
    const currency = document.getElementById('currencyFilter').value;
    tbody.innerHTML = '';

    if (filteredOrders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="12" class="text-center text-muted py-4">No orders found for this selection</td></tr>';
        return;
    }

    filteredOrders.forEach(order => {
        const regionConfig = REGIONS[order.region];
        const statusConfig = STATUS_STYLES[order.status] || STATUS_STYLES.pending;
        const customsConfig = CUSTOMS_STYLES[order.customs_status] || CUSTOMS_STYLES.pending;
        const convertedAmount = convertAmount(order.amount_usd, currency);
        const currencySymbol = getCurrencySymbol(currency);

        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="width: 40px;">
                <input type="checkbox" class="order-checkbox" value="${order.id}" onchange="updateBulkActions()" />
            </td>
            <td><strong>${order.id}</strong></td>
            <td><code>${order.tracking_number}</code></td>
            <td>${order.customer}</td>
            <td>
                <span class="region-chip" style="background: ${regionConfig.color}20; color: ${regionConfig.color};">
                    ${regionConfig.emoji} ${regionConfig.name}
                </span>
            </td>
            <td><small>${order.hub || 'N/A'}</small></td>
            <td>
                <span class="route-badge">${order.route_type || 'Domestic'}</span>
            </td>
            <td class="currency-display">${currencySymbol}${convertedAmount}</td>
            <td>
                <span class="customs-badge ${customsConfig.bg}">
                    ${customsConfig.label}
                </span>
            </td>
            <td>
                <span class="status-badge ${statusConfig.bg}">
                    ${statusConfig.label}
                </span>
            </td>
            <td><small>${new Date(order.created_at).toLocaleString('en-US', {timeZone: 'UTC'})}</small></td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="openOrderModal('${order.id}')">
                    <i class="fas fa-arrow-right"></i> View
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

    updateOrderCount();
}

/**
 * Update order count display
 */
function updateOrderCount() {
    const count = filteredOrders.length;
    document.getElementById('orderCount').textContent = `(${count})`;
}

/**
 * Filter orders based on selected criteria
 */
function filterOrders() {
    const region = document.getElementById('regionFilter').value;
    const customsStatus = document.getElementById('customsFilter').value;
    const orderStatus = document.getElementById('statusFilter').value;

    filteredOrders = allOrders.filter(order => {
        let match = true;
        if (region && order.region !== region) match = false;
        if (customsStatus && order.customs_status !== customsStatus) match = false;
        if (orderStatus && order.status !== orderStatus) match = false;
        return match;
    });

    renderOrderTable();
}

/**
 * Update order table (for currency changes)
 */
function updateOrderTable() {
    renderOrderTable();
}

/**
 * Search orders by ID, tracking number, or customer
 */
function searchOrders() {
    const query = document.getElementById('orderSearch').value.toLowerCase();
    
    filteredOrders = allOrders.filter(order => {
        return order.id.toLowerCase().includes(query) || 
               order.tracking_number.toLowerCase().includes(query) ||
               order.customer.toLowerCase().includes(query);
    });

    renderOrderTable();
}

/**
 * Open order detail modal
 */
function openOrderModal(orderId) {
    currentOrder = allOrders.find(o => o.id === orderId);
    
    if (!currentOrder) return;

    // Populate overview tab
    document.getElementById('modalOrderId').textContent = `Order ${currentOrder.id}`;
    document.getElementById('modalOrderIdValue').textContent = currentOrder.id;
    document.getElementById('modalTrackingValue').textContent = currentOrder.tracking_number;
    document.getElementById('modalCustomerValue').textContent = currentOrder.customer;
    
    const currency = document.getElementById('currencyFilter').value;
    const converted = convertAmount(currentOrder.amount_usd, currency);
    document.getElementById('modalAmountValue').textContent = `${getCurrencySymbol(currency)}${converted}`;
    
    const statusConfig = STATUS_STYLES[currentOrder.status] || STATUS_STYLES.pending;
    document.getElementById('modalStatusValue').textContent = statusConfig.label;
    document.getElementById('modalCreatedValue').textContent = new Date(currentOrder.created_at).toLocaleString();

    // Populate routing tab
    document.getElementById('modalOriginRegion').textContent = REGIONS[currentOrder.region].name;
    document.getElementById('modalOriginHub').textContent = REGIONS[currentOrder.region].hub;
    document.getElementById('modalDestRegion').textContent = REGIONS[currentOrder.dest_region || 'north_america'].name;
    document.getElementById('modalDestHub').textContent = REGIONS[currentOrder.dest_region || 'north_america'].hub;
    document.getElementById('modalRouteType').textContent = currentOrder.route_type || 'Domestic';
    document.getElementById('modalCurrentHandler').textContent = currentOrder.current_handler || 'Awaiting Assignment';

    // Populate compliance tab
    const customsConfig = CUSTOMS_STYLES[currentOrder.customs_status];
    document.getElementById('modalCustomsStatus').textContent = customsConfig.label;
    document.getElementById('modalHsCode').textContent = currentOrder.hs_code || 'HS621711';
    document.getElementById('modalDeclaredValue').textContent = `${getCurrencySymbol(currency)}${convertAmount(currentOrder.declared_value || currentOrder.amount_usd, currency)}`;
    
    populateComplianceDocuments();

    // Populate timezone tab
    const createdUtc = new Date(currentOrder.created_at).toISOString();
    document.getElementById('tzCreatedUtc').textContent = createdUtc;
    document.getElementById('tzOriginTime').textContent = `${new Date(currentOrder.created_at).toLocaleString('en-US')} (${currentOrder.origin_timezone || 'EST'})`;
    document.getElementById('tzDeliveryUtc').textContent = new Date(Date.now() + 7*24*60*60*1000).toISOString();
    document.getElementById('tzDestTime').textContent = `${new Date(Date.now() + 7*24*60*60*1000).toLocaleString('en-US')} (${currentOrder.dest_timezone || 'CET'})`;

    // Show modal
    document.getElementById('orderModal').classList.add('show');
    document.querySelector('.modal-tab.active').click();
}

/**
 * Populate compliance documents
 */
function populateComplianceDocuments() {
    const docsList = document.getElementById('complianceDocuments');
    
    const documents = [
        { name: 'Commercial Invoice', status: 'verified', date: '2026-04-20' },
        { name: 'Packing List', status: 'verified', date: '2026-04-20' },
        { name: 'Certificate of Origin', status: 'pending', date: '2026-04-20' },
        { name: 'Export License', status: 'verified', date: '2026-04-19' },
        { name: 'Customs Declaration Form', status: 'verified', date: '2026-04-20' }
    ];

    docsList.innerHTML = documents.map(doc => {
        const statusIcon = doc.status === 'verified' ? '✓' : '⏳';
        const statusColor = doc.status === 'verified' ? '#28a745' : '#ffc107';
        return `
            <li class="document-item">
                <span>${doc.name}</span>
                <span style="color: ${statusColor};">${statusIcon} ${doc.status.toUpperCase()} (${doc.date})</span>
            </li>
        `;
    }).join('');
}

/**
 * Switch between modal tabs
 */
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.modal-tab').forEach(tab => tab.classList.remove('active'));
    
    document.getElementById(tabName).classList.add('active');
    event.target.closest('.modal-tab').classList.add('active');
}

/**
 * Close order detail modal
 */
function closeOrderModal() {
    document.getElementById('orderModal').classList.remove('show');
    currentOrder = null;
}

/**
 * Update bulk actions bar
 */
function updateBulkActions() {
    selectedOrders.clear();
    document.querySelectorAll('.order-checkbox:checked').forEach(cb => {
        selectedOrders.add(cb.value);
    });

    const bar = document.getElementById('bulkActionsBar');
    const count = selectedOrders.size;

    if (count > 0) {
        bar.classList.add('active');
        document.getElementById('selectedCount').textContent = `${count} order${count !== 1 ? 's' : ''} selected`;
    } else {
        bar.classList.remove('active');
    }
}

/**
 * Toggle select all checkbox
 */
function toggleSelectAll(checkbox) {
    document.querySelectorAll('.order-checkbox').forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateBulkActions();
}

/**
 * Export selected orders
 */
function exportSelectedOrders() {
    if (selectedOrders.size === 0) {
        alert('Please select at least one order');
        return;
    }
    alert(`Exporting ${selectedOrders.size} order(s) to CSV...`);
}

/**
 * Generate shipping labels
 */
function generateShippingLabels() {
    if (selectedOrders.size === 0) {
        alert('Please select at least one order');
        return;
    }
    alert(`Generating shipping labels for ${selectedOrders.size} order(s)...`);
}

/**
 * Action Button Handlers
 */

/**
 * Create a new order
 */
function createNewOrder() {
    window.location.href = '/admin/orders/create';
}

/**
 * View order analytics
 */
function viewOrderAnalytics() {
    window.location.href = '/admin/reports?type=orders&view=analytics';
}

/**
 * Download all order data
 */
function downloadOrderData() {
    const data = filteredOrders.map(order => ({
        'Order ID': order.id,
        'Tracking': order.tracking_number,
        'Customer': order.customer,
        'Region': REGIONS[order.region]?.name || order.region,
        'Amount': `${order.currency} ${order.amount}`,
        'Status': order.status,
        'Customs': order.customs_status,
        'Date': new Date(order.created_date).toLocaleString()
    }));

    downloadCSV(data, 'orders.csv');
}

/**
 * Download CSV file utility
 */
function downloadCSV(data, filename) {
    if (!data || data.length === 0) return;

    const headers = Object.keys(data[0]);
    let csvContent = headers.join(',') + '\n';
    
    data.forEach(row => {
        csvContent += headers.map(header => {
            let cell = row[header] || '';
            if (typeof cell === 'string' && cell.includes(',')) {
                cell = `"${cell}"`;
            }
            return cell;
        }).join(',') + '\n';
    });

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

/**
 * Modal Navigation Functions
 */

/**
 * View the partner for current order
 */
function viewOrderPartner() {
    if (!currentOrder) return;
    closeOrderModal();
    window.location.href = `/admin/partners?partner=${currentOrder.partner_id}`;
}

/**
 * Create a dispute from current order
 */
function createOrderDispute() {
    if (!currentOrder) return;
    closeOrderModal();
    window.location.href = `/admin/disputes/file?order=${currentOrder.id}`;
}

/**
 * Send bulk update
 */
function sendBulkUpdate() {
    if (selectedOrders.size === 0) {
        alert('Please select at least one order');
        return;
    }
    alert(`Sending update notification to ${selectedOrders.size} customer(s)...`);
}

/**
 * Reset selection
 */
function resetSelection() {
    document.querySelectorAll('.order-checkbox').forEach(cb => cb.checked = false);
    document.getElementById('selectAllCheckbox').checked = false;
    updateBulkActions();
}

/**
 * Print shipping label
 */
function printShippingLabel() {
    if (!currentOrder) return;
    alert(`Printing shipping label for ${currentOrder.id}...`);
}

/**
 * Update customs status
 */
function updateCustomsStatus() {
    if (!currentOrder) return;
    alert(`Update customs status for ${currentOrder.id}...`);
}

/**
 * Download compliance documents
 */
function downloadCompliance() {
    if (!currentOrder) return;
    alert(`Downloading compliance documents for ${currentOrder.id}...`);
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
