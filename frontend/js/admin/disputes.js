// Regional definitions with dispute specifications
const REGIONS = {
    north_america: { 
        name: '🇺🇸 North America', 
        color: '#3498db', 
        emoji: '🇺🇸',
        sla_days: 30,
        timezone: 'EST',
        primary_language: 'English',
        legal_framework: 'UCC (Uniform Commercial Code)',
        required_documents: ['Commercial Invoice', 'Shipping Receipt', 'POD', 'Tracking History']
    },
    europe: { 
        name: '🇪🇺 Europe', 
        color: '#9b59b6', 
        emoji: '🇪🇺',
        sla_days: 45,
        timezone: 'CET',
        primary_language: 'English/French',
        legal_framework: 'EU Consumer Protection Directive',
        required_documents: ['Commercial Invoice', 'VAT Documentation', 'POD', 'Proof of Delivery']
    },
    asia_pacific: { 
        name: '🌏 Asia Pacific', 
        color: '#e74c3c', 
        emoji: '🌏',
        sla_days: 23,
        timezone: 'SGT',
        primary_language: 'English/Mandarin',
        legal_framework: 'UNCITRAL Model Law',
        required_documents: ['Commercial Invoice', 'Customs Declaration', 'POD', 'Insurance Certificate']
    },
    middle_east: { 
        name: '🇦🇪 Middle East', 
        color: '#f39c12', 
        emoji: '🇦🇪',
        sla_days: 20,
        timezone: 'GST',
        primary_language: 'English/Arabic',
        legal_framework: 'Islamic/Civil Law',
        required_documents: ['Commercial Invoice', 'Certificate of Origin', 'POD', 'Halal Certificate (if applicable)']
    },
    africa: { 
        name: '🇿🇦 Africa', 
        color: '#16a085', 
        emoji: '🇿🇦',
        sla_days: 40,
        timezone: 'SAST',
        primary_language: 'English',
        legal_framework: 'CISG (UN Convention)',
        required_documents: ['Commercial Invoice', 'Bill of Lading', 'POD', 'Customs Clearance']
    },
    latin_america: { 
        name: '🇧🇷 Latin America', 
        color: '#c0392b', 
        emoji: '🇧🇷',
        sla_days: 35,
        timezone: 'BRT',
        primary_language: 'Spanish/Portuguese',
        legal_framework: 'Civil Code / UNCITRAL',
        required_documents: ['Factura Comercial', 'Certificado de Origen', 'POD', 'NF-e (Brazil)']
    }
};

// Dispute categories with multi-language support
const DISPUTE_CATEGORIES = {
    en: {
        delivery_failure: { label: 'Delivery Failure', icon: '📦' },
        damaged_goods: { label: 'Damaged Goods', icon: '💔' },
        missing_items: { label: 'Missing Items', icon: '❌' },
        wrong_item: { label: 'Wrong Item Delivered', icon: '🔄' },
        delayed_delivery: { label: 'Delayed Delivery', icon: '⏰' },
        customs_hold: { label: 'Customs Hold / Loss', icon: '🔒' },
        quality_issue: { label: 'Quality Issues', icon: '⚠️' },
        payment_dispute: { label: 'Payment Dispute', icon: '💰' }
    },
    es: {
        delivery_failure: { label: 'Fallo de Entrega', icon: '📦' },
        damaged_goods: { label: 'Mercancía Dañada', icon: '💔' },
        missing_items: { label: 'Artículos Faltantes', icon: '❌' },
        wrong_item: { label: 'Artículo Incorrecto', icon: '🔄' },
        delayed_delivery: { label: 'Entrega Retrasada', icon: '⏰' },
        customs_hold: { label: 'Retención Aduanal', icon: '🔒' },
        quality_issue: { label: 'Problemas de Calidad', icon: '⚠️' },
        payment_dispute: { label: 'Disputa de Pago', icon: '💰' }
    },
    fr: {
        delivery_failure: { label: 'Échec de Livraison', icon: '📦' },
        damaged_goods: { label: 'Marchandises Endommagées', icon: '💔' },
        missing_items: { label: 'Articles Manquants', icon: '❌' },
        wrong_item: { label: 'Mauvais Article', icon: '🔄' },
        delayed_delivery: { label: 'Livraison Retardée', icon: '⏰' },
        customs_hold: { label: 'Mainlevée Douanière', icon: '🔒' },
        quality_issue: { label: 'Problèmes de Qualité', icon: '⚠️' },
        payment_dispute: { label: 'Litige de Paiement', icon: '💰' }
    }
};

// Currency exchange rates (to USD base)
const EXCHANGE_RATES = {
    USD: 1.0,
    EUR: 0.92,
    CAD: 1.36,
    AED: 3.67
};

// Severity styles
const SEVERITY_STYLES = {
    low: { bg: 'severity-low', label: '🟢 Low' },
    medium: { bg: 'severity-medium', label: '🟡 Medium' },
    high: { bg: 'severity-high', label: '🔴 High' }
};

// Status styles
const STATUS_STYLES = {
    open: { bg: 'status-open', label: '🔴 Open' },
    in_review: { bg: 'status-in-review', label: '⏳ In Review' },
    escalated: { bg: 'status-escalated', label: '⚡ Escalated' },
    resolved: { bg: 'status-resolved', label: '✓ Resolved' }
};

// Global state
let allDisputes = [];
let filteredDisputes = [];
let selectedDisputes = new Set();
let currentDispute = null;

/**
 * Initialize disputes page on load
 */
document.addEventListener('DOMContentLoaded', () => {
    loadDisputes();
});

/**
 * Load disputes from API
 */
async function loadDisputes() {
    try {
        const response = await apiCall('/admin/disputes', 'GET', null, { skipErrorNotification: true });
        
        if (response && Array.isArray(response)) {
            allDisputes = response.map(dispute => ({
                ...dispute,
                region: dispute.region || 'north_america',
                sla_status: calculateSlaStatus(dispute)
            }));
            
            filteredDisputes = [...allDisputes];
            renderDisputeTable();
            updateDisputeStats();
        }
    } catch (error) {
        console.error('Error loading disputes:', error);
        createMockDisputes();
    }
}

/**
 * Create mock disputes for demonstration
 */
function createMockDisputes() {
    const mockData = [
        {
            id: 'DSP-2026-001',
            order_id: 'ORD-2026-001',
            region: 'north_america',
            category: 'damaged_goods',
            plaintiff: 'Acme Corp',
            defendant: 'FastRoute Logistics',
            description: 'Package arrived with damaged electronic components',
            status: 'in_review',
            severity: 'high',
            claim_currency: 'USD',
            claim_amount: 1200,
            refund_processed: false,
            filed_date: new Date(Date.now() - 5*24*60*60*1000),
            messages: [
                { sender: 'Acme Corp', text: 'Package arrived damaged, unable to use contents', timestamp: new Date(Date.now() - 5*24*60*60*1000) },
                { sender: 'FastRoute Support', text: 'We apologize. Please provide photos and filing documentation.', timestamp: new Date(Date.now() - 4*24*60*60*1000) }
            ]
        },
        {
            id: 'DSP-2026-002',
            order_id: 'ORD-2026-002',
            region: 'europe',
            category: 'delayed_delivery',
            plaintiff: 'Global Tech',
            defendant: 'Euro Express',
            description: 'Shipment delayed by 15 days past agreed deadline',
            status: 'open',
            severity: 'medium',
            claim_currency: 'EUR',
            claim_amount: 450,
            refund_processed: false,
            filed_date: new Date(Date.now() - 2*24*60*60*1000),
            messages: []
        },
        {
            id: 'DSP-2026-003',
            order_id: 'ORD-2026-003',
            region: 'asia_pacific',
            category: 'customs_hold',
            plaintiff: 'Asian Couriers',
            defendant: 'Customs Authority',
            description: 'Shipment held in customs for 20 days, documentation in question',
            status: 'escalated',
            severity: 'high',
            claim_currency: 'SGD',
            claim_amount: 2500,
            refund_processed: false,
            filed_date: new Date(Date.now() - 20*24*60*60*1000),
            messages: [
                { sender: 'Asian Couriers', text: 'Commercial invoice discrepancy reported by customs', timestamp: new Date(Date.now() - 20*24*60*60*1000) },
                { sender: 'Admin - Singapore Hub', text: 'Escalated to regional legal team. Requesting amended documentation.', timestamp: new Date(Date.now() - 18*24*60*60*1000) }
            ]
        },
        {
            id: 'DSP-2026-004',
            order_id: 'ORD-2026-004',
            region: 'middle_east',
            category: 'missing_items',
            plaintiff: 'Emirates Supply',
            defendant: 'Georgensen Courier',
            description: '2 of 5 cases missing from shipment',
            status: 'resolved',
            severity: 'medium',
            claim_currency: 'AED',
            claim_amount: 1875,
            refund_processed: true,
            filed_date: new Date(Date.now() - 35*24*60*60*1000),
            messages: []
        },
        {
            id: 'DSP-2026-005',
            order_id: 'ORD-2026-005',
            region: 'latin_america',
            category: 'wrong_item',
            plaintiff: 'Brazilian Foods',
            defendant: 'Georgensen Courier',
            description: 'Incorrect SKU delivered - wrong product type',
            status: 'in_review',
            severity: 'low',
            claim_currency: 'BRL',
            claim_amount: 650,
            refund_processed: false,
            filed_date: new Date(Date.now() - 8*24*60*60*1000),
            messages: []
        }
    ];

    allDisputes = mockData.map(dispute => ({
        ...dispute,
        sla_status: calculateSlaStatus(dispute),
        exchange_rate: EXCHANGE_RATES[dispute.claim_currency] || 1.0
    }));

    filteredDisputes = [...allDisputes];
    renderDisputeTable();
    updateDisputeStats();
}

/**
 * Calculate SLA status
 */
function calculateSlaStatus(dispute) {
    const regionConfig = REGIONS[dispute.region];
    const sla_days = regionConfig.sla_days;
    const days_elapsed = Math.floor((Date.now() - new Date(dispute.filed_date).getTime()) / (1000 * 60 * 60 * 24));
    const days_remaining = sla_days - days_elapsed;
    
    if (days_remaining < 0) {
        return { status: 'breached', days_remaining: 0, label: '✕ Breached' };
    } else if (days_remaining <= Math.ceil(sla_days * 0.25)) {
        return { status: 'warning', days_remaining, label: '⚠ Warning' };
    }
    return { status: 'on_track', days_remaining, label: '✓ On Track' };
}

/**
 * Render dispute table
 */
function renderDisputeTable() {
    const tbody = document.getElementById('disputesTableBody');
    tbody.innerHTML = '';

    if (filteredDisputes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted py-4">No disputes found for this selection</td></tr>';
        return;
    }

    filteredDisputes.forEach(dispute => {
        const regionConfig = REGIONS[dispute.region];
        const statusConfig = STATUS_STYLES[dispute.status] || STATUS_STYLES.open;
        const severityConfig = SEVERITY_STYLES[dispute.severity] || SEVERITY_STYLES.low;
        const slaStatus = dispute.sla_status;
        const claimUsd = (dispute.claim_amount * (dispute.exchange_rate || 1.0)).toFixed(2);

        let slaDisplay = '';
        if (slaStatus.status === 'breached') {
            slaDisplay = '<span class="sla-breach">✕ Breached</span>';
        } else if (slaStatus.status === 'warning') {
            slaDisplay = `<span class="sla-warning">⚠ ${slaStatus.days_remaining} days left</span>`;
        } else {
            slaDisplay = `<span class="sla-warning">✓ ${slaStatus.days_remaining} days left</span>`;
        }

        const row = document.createElement('tr');
        row.innerHTML = `
            <td style="width: 40px;">
                <input type="checkbox" class="dispute-checkbox" value="${dispute.id}" onchange="updateBulkActions()" />
            </td>
            <td><strong>${dispute.id}</strong></td>
            <td><small>${dispute.order_id}</small></td>
            <td>
                <span class="region-chip" style="background: ${regionConfig.color}20; color: ${regionConfig.color};">
                    ${regionConfig.emoji} ${regionConfig.name}
                </span>
            </td>
            <td><small>${DISPUTE_CATEGORIES.en[dispute.category]?.label || dispute.category}</small></td>
            <td><strong>$${claimUsd}</strong></td>
            <td>
                <span class="status-badge ${statusConfig.bg}">
                    ${statusConfig.label}
                </span>
            </td>
            <td>
                <span class="severity-badge ${severityConfig.bg}">
                    ${severityConfig.label}
                </span>
            </td>
            <td>${slaDisplay}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="openDisputeModal('${dispute.id}')">
                    <i class="fas fa-arrow-right"></i> View
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

    updateDisputeCount();
}

/**
 * Update dispute count
 */
function updateDisputeCount() {
    document.getElementById('disputeCount').textContent = `(${filteredDisputes.length})`;
}

/**
 * Update dispute statistics
 */
function updateDisputeStats() {
    const total = filteredDisputes.length;
    const onTrack = filteredDisputes.filter(d => d.sla_status?.status === 'on_track').length;
    const warning = filteredDisputes.filter(d => d.sla_status?.status === 'warning').length;
    const breached = filteredDisputes.filter(d => d.sla_status?.status === 'breached').length;

    document.getElementById('totalCount').textContent = allDisputes.length;
    document.getElementById('onTrackCount').textContent = onTrack;
    document.getElementById('warningCount').textContent = warning;
    document.getElementById('breachedCount').textContent = breached;
}

/**
 * Filter disputes
 */
function filterDisputes() {
    const region = document.getElementById('regionFilter').value;
    const status = document.getElementById('statusFilter').value;
    const severity = document.getElementById('severityFilter').value;
    const slaStatus = document.getElementById('slaFilter').value;

    filteredDisputes = allDisputes.filter(dispute => {
        let match = true;
        if (region && dispute.region !== region) match = false;
        if (status && dispute.status !== status) match = false;
        if (severity && dispute.severity !== severity) match = false;
        if (slaStatus && dispute.sla_status?.status !== slaStatus) match = false;
        return match;
    });

    renderDisputeTable();
    updateDisputeStats();
}

/**
 * Search disputes
 */
function searchDisputes() {
    const query = document.getElementById('disputeSearch').value.toLowerCase();
    
    filteredDisputes = allDisputes.filter(dispute => {
        return dispute.id.toLowerCase().includes(query) ||
               dispute.order_id.toLowerCase().includes(query) ||
               dispute.plaintiff.toLowerCase().includes(query);
    });

    renderDisputeTable();
}

/**
 * Open dispute modal
 */
function openDisputeModal(disputeId) {
    currentDispute = allDisputes.find(d => d.id === disputeId);
    
    if (!currentDispute) return;

    const regionConfig = REGIONS[currentDispute.region];

    // Overview tab
    document.getElementById('modalDisputeId').textContent = `Dispute ${currentDispute.id}`;
    document.getElementById('modalDisputeIdValue').textContent = currentDispute.id;
    document.getElementById('modalOrderIdValue').textContent = currentDispute.order_id;
    document.getElementById('modalRegionValue').textContent = regionConfig.name;
    document.getElementById('modalCategoryValue').textContent = DISPUTE_CATEGORIES.en[currentDispute.category]?.label || currentDispute.category;
    document.getElementById('modalPlaintiffValue').textContent = currentDispute.plaintiff;
    document.getElementById('modalDefendantValue').textContent = currentDispute.defendant;
    document.getElementById('modalDescriptionValue').textContent = currentDispute.description;
    
    const statusConfig = STATUS_STYLES[currentDispute.status];
    document.getElementById('modalStatusValue').innerHTML = `<span class="status-badge ${statusConfig.bg}">${statusConfig.label}</span>`;
    
    const severityConfig = SEVERITY_STYLES[currentDispute.severity];
    document.getElementById('modalSeverityValue').innerHTML = `<span class="severity-badge ${severityConfig.bg}">${severityConfig.label}</span>`;

    // Financial tab
    document.getElementById('modalOriginalCurrency').textContent = currentDispute.claim_currency;
    document.getElementById('modalClaimAmountOriginal').textContent = `${currentDispute.claim_currency} ${currentDispute.claim_amount.toFixed(2)}`;
    document.getElementById('modalExchangeRate').textContent = `1 ${currentDispute.claim_currency} = ${currentDispute.exchange_rate.toFixed(4)} USD`;
    const claimUsd = (currentDispute.claim_amount * currentDispute.exchange_rate).toFixed(2);
    document.getElementById('modalClaimAmountUsd').textContent = `$${claimUsd}`;
    document.getElementById('modalRefundStatus').textContent = currentDispute.refund_processed ? '✓ Processed' : 'Pending';

    // Evidence Vault tab
    populateEvidenceVault(regionConfig);

    // Communication Log tab
    populateCommunicationLog();

    // SLA & Timezone tab
    const slaStatus = currentDispute.sla_status;
    const regionSLADays = regionConfig.sla_days;
    document.getElementById('modalSlaRange').textContent = `${regionSLADays} business days (${regionConfig.legal_framework})`;
    document.getElementById('modalFiledDate').textContent = new Date(currentDispute.filed_date).toLocaleString();
    
    const dueDate = new Date(currentDispute.filed_date);
    dueDate.setDate(dueDate.getDate() + regionSLADays);
    document.getElementById('modalDueDate').textContent = dueDate.toLocaleString();
    document.getElementById('modalDaysRemaining').textContent = slaStatus.days_remaining;

    // SLA Alert
    const slaAlertDiv = document.getElementById('slaAlert');
    if (slaStatus.status === 'breached') {
        slaAlertDiv.innerHTML = `<div class="alert alert-danger"><strong>⚠ SLA BREACHED!</strong> This dispute has exceeded the regional SLA limit.</div>`;
    } else if (slaStatus.status === 'warning') {
        slaAlertDiv.innerHTML = `<div class="alert alert-warning"><strong>⚠ SLA WARNING:</strong> Only ${slaStatus.days_remaining} days remaining to resolve.</div>`;
    } else {
        slaAlertDiv.innerHTML = `<div class="alert alert-info"><strong>✓ On Track:</strong> ${slaStatus.days_remaining} days remaining.</div>`;
    }

    // Timezone info
    const filedUtc = new Date(currentDispute.filed_date).toISOString();
    document.getElementById('tzFiledUtc').textContent = filedUtc;
    document.getElementById('tzRegionTime').textContent = `${new Date(currentDispute.filed_date).toLocaleString('en-US')} (${regionConfig.timezone})`;
    document.getElementById('tzAdminTime').textContent = `${new Date(currentDispute.filed_date).toLocaleString('en-US')} (Local)`;

    document.getElementById('disputeModal').classList.add('show');
    document.querySelector('.modal-tab.active').click();
}

/**
 * Populate evidence vault with regional requirements
 */
function populateEvidenceVault(regionConfig) {
    const docsList = document.getElementById('evidenceVault');
    docsList.innerHTML = regionConfig.required_documents.map(doc => {
        return `
            <li class="document-item">
                <span>
                    <i class="fas fa-file"></i> ${doc}
                </span>
                <span>
                    <button class="btn btn-sm btn-link" onclick="downloadDocument('${doc}')">
                        <i class="fas fa-download"></i>
                    </button>
                </span>
            </li>
        `;
    }).join('');
}

/**
 * Populate communication log
 */
function populateCommunicationLog() {
    const logDiv = document.getElementById('communicationLog');
    
    if (!currentDispute.messages || currentDispute.messages.length === 0) {
        logDiv.innerHTML = '<div class="message-item text-center text-muted py-3"><small>No messages yet</small></div>';
        return;
    }

    logDiv.innerHTML = currentDispute.messages.map(msg => {
        return `
            <div class="message-item">
                <div class="message-sender">${msg.sender}</div>
                <div class="message-timestamp">${new Date(msg.timestamp).toLocaleString()}</div>
                <div class="message-content">${msg.text}</div>
            </div>
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
 * Close dispute modal
 */
function closeDisputeModal() {
    document.getElementById('disputeModal').classList.remove('show');
    currentDispute = null;
}

/**
 * Update bulk actions
 */
function updateBulkActions() {
    selectedDisputes.clear();
    document.querySelectorAll('.dispute-checkbox:checked').forEach(cb => {
        selectedDisputes.add(cb.value);
    });

    const bar = document.getElementById('bulkActionsBar');
    const count = selectedDisputes.size;

    if (count > 0) {
        bar.classList.add('active');
        document.getElementById('selectedCount').textContent = `${count} dispute${count !== 1 ? 's' : ''} selected`;
    } else {
        bar.classList.remove('active');
    }
}

/**
 * Toggle select all
 */
function toggleSelectAll(checkbox) {
    document.querySelectorAll('.dispute-checkbox').forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateBulkActions();
}

/**
 * Bulk regional escalate
 */
function bulkRegionalEscalate() {
    if (selectedDisputes.size === 0) {
        alert('Please select at least one dispute');
        return;
    }
    alert(`Escalating ${selectedDisputes.size} dispute(s) to regional legal teams...`);
}

/**
 * Bulk regional resolve
 */
function bulkRegionalResolve() {
    if (selectedDisputes.size === 0) {
        alert('Please select at least one dispute');
        return;
    }
    alert(`Processing batch resolution for ${selectedDisputes.size} dispute(s)...`);
}

/**
 * Send regional notification
 */
function sendRegionalNotification() {
    if (selectedDisputes.size === 0) {
        alert('Please select at least one dispute');
        return;
    }
    alert(`Sending notifications to regional teams for ${selectedDisputes.size} dispute(s)...`);
}

/**
 * Reset selection
 */
function resetSelection() {
    document.querySelectorAll('.dispute-checkbox').forEach(cb => cb.checked = false);
    document.getElementById('selectAllCheckbox').checked = false;
    updateBulkActions();
}

/**
 * View evidence vault
 */
function viewEvidenceVault() {
    alert('Opening full evidence vault...');
}

/**
 * Request more documents
 */
function requestMoreDocuments() {
    alert('Sending document request to plaintiff...');
}

/**
 * Add communication note
 */
function addCommunicationNote() {
    const note = document.getElementById('resolutionNote').value;
    if (!note.trim()) {
        alert('Please enter a note');
        return;
    }
    alert(`Note added to dispute ${currentDispute.id}`);
    document.getElementById('resolutionNote').value = '';
}

/**
 * Escalate dispute
 */
function escalateDispute() {
    if (!currentDispute) return;
    alert(`Escalating ${currentDispute.id} to regional team...`);
}

/**
 * Resolve dispute
 */
function resolveDispute() {
    if (!currentDispute) return;
    alert(`Resolving ${currentDispute.id}...`);
}

/**
 * Adjust refund
 */
function adjustRefund() {
    if (!currentDispute) return;
    alert(`Adjusting refund for ${currentDispute.id}...`);
}

/**
 * Download document
 */
function downloadDocument(docName) {
    alert(`Downloading ${docName}...`);
}

/**
 * Action Button Handlers
 */

/**
 * Create a new dispute
 */
function createNewDispute() {
    window.location.href = '/admin/disputes/file';
}

/**
 * View dispute analytics
 */
function viewDisputeAnalytics() {
    window.location.href = '/admin/reports?type=disputes&view=analytics';
}

/**
 * Download all dispute data
 */
function downloadDisputeData() {
    const data = filteredDisputes.map(dispute => ({
        'Dispute ID': dispute.id,
        'Order ID': dispute.order_id,
        'Region': REGIONS[dispute.region]?.name || dispute.region,
        'Category': DISPUTE_CATEGORIES.en[dispute.category]?.label || dispute.category,
        'Claim Amount': `${dispute.claim_currency} ${dispute.claim_amount}`,
        'Status': dispute.status,
        'Severity': dispute.severity,
        'SLA Days Left': dispute.sla_status?.days_remaining || 0,
        'Filed Date': new Date(dispute.filed_date).toLocaleDateString()
    }));

    downloadCSV(data, 'disputes.csv');
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
 * View the order related to this dispute
 */
function viewDisputeOrder() {
    if (!currentDispute) return;
    closeDisputeModal();
    window.location.href = `/admin/orders?open=${currentDispute.order_id}`;
}

/**
 * View the partner involved in this dispute
 */
function viewDisputePartner() {
    if (!currentDispute) return;
    closeDisputeModal();
    window.location.href = `/admin/partners?partner=${currentDispute.defendant_id || ''}`;
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
