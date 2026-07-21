// Regional definitions with colors and emojis
const REGIONS = {
    north_america: { name: '🇺🇸 North America', color: '#3498db', emoji: '🇺🇸' },
    europe: { name: '🇪🇺 Europe', color: '#9b59b6', emoji: '🇪🇺' },
    asia_pacific: { name: '🌏 Asia Pacific', color: '#e74c3c', emoji: '🌏' },
    middle_east: { name: '🇦🇪 Middle East', color: '#f39c12', emoji: '🇦🇪' },
    africa: { name: '🇿🇦 Africa', color: '#16a085', emoji: '🇿🇦' },
    latin_america: { name: '🇧🇷 Latin America', color: '#c0392b', emoji: '🇧🇷' }
};

// Tier definitions
const TIERS = {
    elite: { name: 'Elite', badge: '🏆', minShipments: 500, minRating: 4.8 },
    gold: { name: 'Gold', badge: '⭐', minShipments: 100, minRating: 4.5 },
    standard: { name: 'Standard', badge: '📦', minShipments: 0, minRating: 4.0 }
};

// Compliance status colors
const COMPLIANCE_COLORS = {
    verified: { color: '#28a745', label: '✓ Verified', bg: '#d4edda' },
    warning: { color: '#ffc107', label: '⚠ Warning', bg: '#fff3cd' },
    expired: { color: '#dc3545', label: '✕ Expired', bg: '#f8d7da' },
    pending: { color: '#17a2b8', label: '⏳ Pending', bg: '#d1ecf1' }
};

// Global state
let allPartners = [];
let filteredPartners = [];
let selectedPartners = new Set();
let currentPartner = null;

/**
 * Initialize partners page on load
 */
document.addEventListener('DOMContentLoaded', () => {
    loadPartners();
});

/**
 * Load partners from API and populate table
 */
async function loadPartners() {
    try {
        const response = await apiCall('/admin/partners', 'GET', null, { skipErrorNotification: true });
        
        if (response && response.partners) {
            allPartners = response.partners.map(partner => ({
                ...partner,
                tier: calculateTier(partner.completed_shipments || 0, partner.rating || 4.0),
                compliance_status: determineComplianceStatus(partner),
                service_zones: partner.service_zones || ['Local'],
                primary_region: partner.primary_region || 'north_america'
            }));
            
            filteredPartners = [...allPartners];
            renderPartnerTable();
            updatePartnerCount();
        }
    } catch (error) {
        console.error('Error loading partners:', error);
        // Show placeholder data for demo
        createMockPartners();
    }
}

/**
 * Create mock partners for demonstration
 */
function createMockPartners() {
    const mockData = [
        { id: 'P001', name: 'FastRoute Logistics', primary_region: 'north_america', completed_shipments: 850, rating: 4.9, documents_status: 'verified', kyc_status: 'verified', regional_tax_id: 'US-TX-12345', email: 'admin@fastroute.com', phone: '+1-555-0101' },
        { id: 'P002', name: 'Euro Express', primary_region: 'europe', completed_shipments: 650, rating: 4.7, documents_status: 'verified', kyc_status: 'verified', regional_tax_id: 'DE-12345X', email: 'info@euroexpress.eu', phone: '+49-30-123456' },
        { id: 'P003', name: 'Asian Couriers', primary_region: 'asia_pacific', completed_shipments: 1200, rating: 4.8, documents_status: 'verified', kyc_status: 'verified', regional_tax_id: 'SG-12345678', email: 'ops@asiancouriers.sg', phone: '+65-6123-4567' },
        { id: 'P004', name: 'Emirates Delivery', primary_region: 'middle_east', completed_shipments: 300, rating: 4.5, documents_status: 'warning', kyc_status: 'pending', regional_tax_id: 'AE-12345', email: 'contact@emiratesdelivery.ae', phone: '+971-4-123-4567' },
        { id: 'P005', name: 'AfriCargo Solutions', primary_region: 'africa', completed_shipments: 450, rating: 4.6, documents_status: 'verified', kyc_status: 'verified', regional_tax_id: 'ZA-1234567890', email: 'support@africargo.co.za', phone: '+27-11-123-4567' },
        { id: 'P006', name: 'LatinAmerica Express', primary_region: 'latin_america', completed_shipments: 120, rating: 4.4, documents_status: 'expired', kyc_status: 'expired', regional_tax_id: 'MX-12345678901', email: 'info@laexpress.mx', phone: '+52-55-1234-5678' },
    ];

    allPartners = mockData.map(partner => ({
        ...partner,
        tier: calculateTier(partner.completed_shipments, partner.rating),
        compliance_status: determineComplianceStatus(partner),
        service_zones: ['Local', 'Cross-border'],
        vehicle_type: 'Van',
        license_plate: 'XYZ-' + partner.id.substring(2),
        insurance_status: 'Active',
        capacity: 500,
        total_earnings: (Math.random() * 50000 + 10000).toFixed(2),
        pending_payouts: (Math.random() * 5000).toFixed(2),
        last_payout: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
        avg_order_value: (Math.random() * 500 + 50).toFixed(2),
        background_check: 'Passed',
        last_compliance_review: new Date(Date.now() - Math.random() * 90 * 24 * 60 * 60 * 1000)
    }));

    filteredPartners = [...allPartners];
    renderPartnerTable();
    updatePartnerCount();
}

/**
 * Calculate partner tier based on metrics
 */
function calculateTier(shipments, rating) {
    if (shipments >= TIERS.elite.minShipments && rating >= TIERS.elite.minRating) {
        return 'elite';
    } else if (shipments >= TIERS.gold.minShipments && rating >= TIERS.gold.minRating) {
        return 'gold';
    }
    return 'standard';
}

/**
 * Determine compliance status based on documents and KYC
 */
function determineComplianceStatus(partner) {
    if (partner.documents_status === 'expired' || partner.kyc_status === 'expired') {
        return 'expired';
    } else if (partner.documents_status === 'warning' || partner.kyc_status === 'pending') {
        return 'warning';
    } else if (partner.documents_status === 'verified' && partner.kyc_status === 'verified') {
        return 'verified';
    }
    return 'pending';
}

/**
 * Render partner table with current filtered data
 */
function renderPartnerTable() {
    const tbody = document.getElementById('partnersTableBody');
    tbody.innerHTML = '';

    if (filteredPartners.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted py-4">No partners found</td></tr>';
        return;
    }

    filteredPartners.forEach(partner => {
        const tierConfig = TIERS[partner.tier];
        const regionConfig = REGIONS[partner.primary_region];
        const complianceConfig = COMPLIANCE_COLORS[partner.compliance_status];

        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="width: 40px;">
                <input type="checkbox" class="partner-checkbox" value="${partner.id}" onchange="updateBulkActions()" />
            </td>
            <td><strong>${partner.id}</strong></td>
            <td>
                <div>${partner.name}</div>
                <small class="region-chip" style="background: ${regionConfig.color}20; color: ${regionConfig.color};">
                    ${regionConfig.emoji} ${regionConfig.name}
                </small>
            </td>
            <td>
                <span class="tier-badge tier-${partner.tier}">
                    ${tierConfig.badge} ${tierConfig.name}
                </span>
            </td>
            <td><strong>${partner.completed_shipments || 0}</strong></td>
            <td>
                <span class="rating-stars">
                    ${'★'.repeat(Math.floor(partner.rating || 4))}${'☆'.repeat(5 - Math.floor(partner.rating || 4))}
                </span>
                <br><small>${(partner.rating || 4.0).toFixed(1)} / 5.0</small>
            </td>
            <td>
                <span class="compliance-badge" style="background: ${complianceConfig.bg}; color: ${complianceConfig.color};">
                    ${complianceConfig.label}
                </span>
            </td>
            <td>
                <div class="service-zone">
                    ${(partner.service_zones || ['Local']).map(z => `<span class="badge bg-info">${z}</span>`).join(' ')}
                </div>
            </td>
            <td><small class="text-muted">${partner.regional_tax_id || 'N/A'}</small></td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="openPartnerProfile('${partner.id}')">
                    <i class="fas fa-arrow-right"></i> View
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

    updatePartnerCount();
}

/**
 * Update partner count display
 */
function updatePartnerCount() {
    const count = filteredPartners.length;
    document.getElementById('partnerCount').textContent = `(${count})`;
}

/**
 * Filter partners based on selected criteria
 */
function filterPartners() {
    const region = document.getElementById('regionFilter').value;
    const tier = document.getElementById('tierFilter').value;
    const compliance = document.getElementById('complianceFilter').value;

    filteredPartners = allPartners.filter(partner => {
        let match = true;
        if (region && partner.primary_region !== region) match = false;
        if (tier && partner.tier !== tier) match = false;
        if (compliance && partner.compliance_status !== compliance) match = false;
        return match;
    });

    renderPartnerTable();
}

/**
 * Search partners by ID or name
 */
function searchPartners() {
    const query = document.getElementById('partnerSearch').value.toLowerCase();
    
    filteredPartners = allPartners.filter(partner => {
        return partner.id.toLowerCase().includes(query) || 
               partner.name.toLowerCase().includes(query);
    });

    renderPartnerTable();
}

/**
 * Open partner profile modal
 */
function openPartnerProfile(partnerId) {
    currentPartner = allPartners.find(p => p.id === partnerId);
    
    if (!currentPartner) return;

    // Populate overview tab
    document.getElementById('modalPartnerName').textContent = currentPartner.name;
    document.getElementById('modalPartnerId').textContent = currentPartner.id;
    document.getElementById('modalEmail').textContent = currentPartner.email || '---';
    document.getElementById('modalPhone').textContent = currentPartner.phone || '---';
    document.getElementById('modalRegion').textContent = REGIONS[currentPartner.primary_region].name;
    document.getElementById('modalTier').textContent = `${TIERS[currentPartner.tier].badge} ${TIERS[currentPartner.tier].name}`;
    document.getElementById('modalServiceZone').textContent = (currentPartner.service_zones || ['Local']).join(', ');
    document.getElementById('modalJoinedDate').textContent = new Date(currentPartner.created_at || Date.now()).toLocaleDateString();

    // Populate documents tab
    populateDocumentsTab();

    // Populate vehicle tab
    document.getElementById('modalVehicleType').textContent = currentPartner.vehicle_type || 'Van';
    document.getElementById('modalLicensePlate').textContent = currentPartner.license_plate || '---';
    document.getElementById('modalInsuranceStatus').textContent = currentPartner.insurance_status || 'Active';
    document.getElementById('modalCapacity').textContent = currentPartner.capacity || 500;

    // Populate earnings tab
    document.getElementById('modalTotalEarnings').textContent = `$${parseFloat(currentPartner.total_earnings || 0).toFixed(2)}`;
    document.getElementById('modalPendingPayouts').textContent = `$${parseFloat(currentPartner.pending_payouts || 0).toFixed(2)}`;
    document.getElementById('modalLastPayout').textContent = currentPartner.last_payout ? new Date(currentPartner.last_payout).toLocaleDateString() : '---';
    document.getElementById('modalAvgOrderValue').textContent = `$${parseFloat(currentPartner.avg_order_value || 0).toFixed(2)}`;

    // Populate compliance tab
    document.getElementById('modalTaxId').textContent = currentPartner.regional_tax_id || '---';
    document.getElementById('modalKycStatus').textContent = (currentPartner.kyc_status || 'pending').toUpperCase();
    document.getElementById('modalBackgroundCheck').textContent = currentPartner.background_check || 'Pending';
    document.getElementById('modalLastReview').textContent = currentPartner.last_compliance_review ? new Date(currentPartner.last_compliance_review).toLocaleDateString() : '---';

    // Show modal
    document.getElementById('partnerModal').classList.add('show');
    document.querySelector('.modal-tab.active').click();
}

/**
 * Populate documents tab with partner documents
 */
function populateDocumentsTab() {
    const docsList = document.getElementById('documentsList');
    
    const documents = [
        { name: 'Insurance Certificate', status: currentPartner.documents_status || 'verified', expiry: '2026-12-31' },
        { name: 'Tax Registration', status: currentPartner.kyc_status || 'verified', expiry: '2027-06-30' },
        { name: 'Business License', status: 'verified', expiry: '2025-12-31' },
        { name: 'Driver License (Primary)', status: 'verified', expiry: '2028-03-15' },
        { name: 'Vehicle Registration', status: 'verified', expiry: '2026-09-30' }
    ];

    docsList.innerHTML = documents.map(doc => {
        const statusClass = `doc-status-${doc.status}`;
        const statusIcon = doc.status === 'verified' ? '✓' : doc.status === 'pending' ? '⏳' : '✕';
        return `
            <li class="document-item">
                <span>${doc.name}</span>
                <span class="${statusClass}">
                    ${statusIcon} ${doc.status.toUpperCase()} 
                    <small>(Expires: ${doc.expiry})</small>
                </span>
            </li>
        `;
    }).join('');
}

/**
 * Switch between modal tabs
 */
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.modal-tab').forEach(tab => tab.classList.remove('active'));

    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    event.target.closest('.modal-tab').classList.add('active');
}

/**
 * Close partner profile modal
 */
function closePartnerModal() {
    document.getElementById('partnerModal').classList.remove('show');
    currentPartner = null;
}

/**
 * Update bulk actions bar visibility and count
 */
function updateBulkActions() {
    selectedPartners.clear();
    document.querySelectorAll('.partner-checkbox:checked').forEach(cb => {
        selectedPartners.add(cb.value);
    });

    const bar = document.getElementById('bulkActionsBar');
    const count = selectedPartners.size;

    if (count > 0) {
        bar.classList.add('active');
        document.getElementById('selectedCount').textContent = `${count} partner${count !== 1 ? 's' : ''} selected`;
    } else {
        bar.classList.remove('active');
    }
}

/**
 * Toggle select all checkbox
 */
function toggleSelectAll(checkbox) {
    document.querySelectorAll('.partner-checkbox').forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateBulkActions();
}

/**
 * Send message to selected partners
 */
function sendBulkMessage() {
    if (selectedPartners.size === 0) {
        alert('Please select at least one partner');
        return;
    }
    alert(`Message will be sent to ${selectedPartners.size} partner(s):\n${Array.from(selectedPartners).join(', ')}`);
}

/**
 * Verify documents for selected partners
 */
function verifyBulkDocuments() {
    if (selectedPartners.size === 0) {
        alert('Please select at least one partner');
        return;
    }
    alert(`Document verification requests sent to ${selectedPartners.size} partner(s)`);
}

/**
 * Reset bulk selection
 */
function resetBulkSelection() {
    document.querySelectorAll('.partner-checkbox').forEach(cb => cb.checked = false);
    document.getElementById('selectAllCheckbox').checked = false;
    updateBulkActions();
}

/**
 * Toggle activity heatmap section
 */
function toggleActivityMap() {
    const mapSection = document.getElementById('mapSection');
    mapSection.style.display = mapSection.style.display === 'none' ? 'block' : 'none';
}

/**
 * Open bulk communication modal
 */
function openBulkCommunication() {
    document.getElementById('communicationModal').classList.add('show');
}

/**
 * Close bulk communication modal
 */
function closeCommunicationModal() {
    document.getElementById('communicationModal').classList.remove('show');
}

/**
 * Send regional communication
 */
function sendCommunication() {
    const region = document.getElementById('commRegion').value;
    const subject = document.getElementById('commSubject').value;
    const message = document.getElementById('commMessage').value;

    if (!region || !subject || !message) {
        alert('Please fill in all fields');
        return;
    }

    alert(`Communication sent to ${REGIONS[region].name} partners:\n\nSubject: ${subject}\n\nMessage: ${message}`);
    closeCommunicationModal();
    
    // Clear form
    document.getElementById('commRegion').value = '';
    document.getElementById('commSubject').value = '';
    document.getElementById('commMessage').value = '';
}

/**
 * Edit partner profile
 */
function editPartner() {
    alert(`Edit partner: ${currentPartner.name} (${currentPartner.id})`);
}

/**
 * Request document verification for partner
 */
function requestDocumentVerification() {
    alert(`Document verification requested for ${currentPartner.name}`);
}

/**
 * Suspend partner account
 */
function suspendPartner() {
    if (confirm(`Are you sure you want to suspend ${currentPartner.name}?`)) {
        alert(`Partner ${currentPartner.name} has been suspended`);
        closePartnerModal();
    }
}

/**
 * Add new partner
 */
function addNewPartner() {
    alert('Opening new partner registration form...');
}

/**
 * Action Button Handlers
 */

/**
 * Create a new partner
 */
function createNewPartner() {
    window.location.href = '/admin/partners/onboard';
}

/**
 * View partner analytics
 */
function viewPartnerAnalytics() {
    window.location.href = '/admin/reports?type=partners&view=analytics';
}

/**
 * Download all partner data
 */
function downloadPartnerData() {
    const data = filteredPartners.map(partner => ({
        'Partner Name': partner.name,
        'Partner ID': partner.id,
        'Region': REGIONS[partner.region]?.name || partner.region,
        'Tier': partner.tier,
        'Rating': partner.rating,
        'Compliance': partner.kyc_status,
        'Active Status': partner.is_active ? 'Active' : 'Inactive',
        'Joined': new Date(partner.created_date).toLocaleDateString()
    }));

    downloadCSV(data, 'partners.csv');
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
 * View all orders from current partner
 */
function viewPartnerOrders() {
    if (!currentPartner) return;
    closePartnerModal();
    window.location.href = `/admin/orders?partner=${currentPartner.id}`;
}

/**
 * View all disputes involving current partner
 */
function viewPartnerDisputes() {
    if (!currentPartner) return;
    closePartnerModal();
    window.location.href = `/admin/disputes?partner=${currentPartner.id}`;
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
