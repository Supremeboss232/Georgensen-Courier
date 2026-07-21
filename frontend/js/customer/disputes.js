/**
 * Disputes Form Handler
 * Manages customer dispute filing and dispute viewing
 */

let selectedShipmentId = null;
const disputeTypeNames = {
    delivery_failure: '📦 Delivery Failure',
    quality_issue: '⚠️ Quality Issue',
    missing_items: '📪 Missing Items',
    damage: '🔨 Damage',
    other: '❓ Other'
};

document.addEventListener('DOMContentLoaded', async () => {
    await loadShipments();
    await loadDisputes();
    setupEventListeners();
});

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.form-tabs button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            switchTab(e.target.dataset.tab);
        });
    });

    // Form submission
    document.getElementById('disputeForm').addEventListener('submit', handleDisputeSubmit);
}

/**
 * Switch between tabs
 */
function switchTab(tabName) {
    // Update button active states
    document.querySelectorAll('.form-tabs button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Show/hide tab content
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.style.display = tab.id === tabName ? 'block' : 'none';
    });

    // Reload disputes when switching to that tab
    if (tabName === 'existing-disputes') {
        loadDisputes();
    }
}

/**
 * Load customer shipments
 */
async function loadShipments() {
    try {
        const token = localStorage.getItem('authToken');
        if (!token) {
            window.location.href = '/auth/login';
            return;
        }

        const response = await fetch('/api/v1/customers/shipments', {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const shipments = await response.json();
        displayShipments(shipments);

    } catch (error) {
        console.error('Error loading shipments:', error);
        document.getElementById('shipmentList').innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> Could not load shipments. Please refresh the page.
            </div>
        `;
    }
}

/**
 * Display shipments for selection
 */
function displayShipments(shipments) {
    const container = document.getElementById('shipmentList');

    if (!shipments || shipments.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <strong>No shipments</strong>
                <p class="mb-0 mt-2">You don't have any shipments to dispute.</p>
            </div>
        `;
        return;
    }

    // Filter for delivered/problematic shipments
    const disputeableShipments = shipments.filter(s => 
        ['delivered', 'out_for_delivery', 'in_transit', 'pending'].includes(s.status)
    );

    if (disputeableShipments.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <strong>No available shipments</strong>
                <p class="mb-0 mt-2">Only delivered or in-transit shipments can have disputes filed.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = disputeableShipments.map(shipment => `
        <div class="shipment-select-item" data-shipment-id="${shipment.id}">
            <div class="row align-items-center">
                <div class="col-8">
                    <div class="fw-bold">Shipment #${shipment.tracking_number}</div>
                    <div class="shipment-info">
                        To: ${shipment.recipient_name || 'Unknown'}
                        ${shipment.destination_city ? ` • ${shipment.destination_city}` : ''}
                    </div>
                    <small class="text-muted">
                        Sent: ${new Date(shipment.created_at).toLocaleDateString()}
                    </small>
                </div>
                <div class="col-4 text-end">
                    <span class="badge bg-${getStatusColor(shipment.status)}">${shipment.status}</span>
                </div>
            </div>
        </div>
    `).join('');

    // Add click handlers
    document.querySelectorAll('.shipment-select-item').forEach(item => {
        item.addEventListener('click', () => selectShipment(item));
    });
}

/**
 * Select shipment for dispute
 */
function selectShipment(element) {
    // Remove previous selection
    document.querySelectorAll('.shipment-select-item').forEach(item => {
        item.classList.remove('selected');
    });

    // Select new item
    element.classList.add('selected');
    selectedShipmentId = parseInt(element.dataset.shipmentId);
    document.getElementById('selectedShipmentId').value = selectedShipmentId;
}

/**
 * Load customer disputes
 */
async function loadDisputes() {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/v1/disputes/customer', {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const disputes = await response.json();
        displayDisputes(disputes);

    } catch (error) {
        console.error('Error loading disputes:', error);
        document.getElementById('disputesList').innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> Could not load disputes. Please refresh the page.
            </div>
        `;
    }
}

/**
 * Display disputes
 */
function displayDisputes(disputes) {
    const container = document.getElementById('disputesList');

    if (!disputes || disputes.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <strong>No disputes</strong>
                <p class="mb-0 mt-2">You haven't filed any disputes yet.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = disputes.map(dispute => `
        <div class="dispute-card p-4 mb-3 ${dispute.status}">
            <div class="row align-items-start">
                <div class="col-8">
                    <div class="fw-bold">${dispute.dispute_number}</div>
                    <h6 class="mt-2">${dispute.title}</h6>
                    <div class="mt-2">
                        <span class="dispute-type-badge ${dispute.dispute_type}">
                            ${disputeTypeNames[dispute.dispute_type] || dispute.dispute_type}
                        </span>
                    </div>
                    <p class="text-muted mt-3 mb-0">
                        ${dispute.description}
                    </p>
                </div>
                <div class="col-4 text-end">
                    <div class="mb-2">
                        <span class="status-badge badge bg-${getDisputeStatusColor(dispute.status)}">
                            ${dispute.status.charAt(0).toUpperCase() + dispute.status.slice(1)}
                        </span>
                    </div>
                    <small class="text-muted d-block">
                        Filed: ${new Date(dispute.created_at).toLocaleDateString()}
                    </small>
                    ${dispute.resolved_at ? `
                        <small class="text-muted d-block">
                            Resolved: ${new Date(dispute.resolved_at).toLocaleDateString()}
                        </small>
                    ` : ''}
                    ${dispute.status === 'resolved' && dispute.refund_amount ? `
                        <div class="mt-2 fw-bold text-success">
                            Refund: $${parseFloat(dispute.refund_amount).toFixed(2)}
                        </div>
                    ` : ''}
                </div>
            </div>
            
            ${dispute.resolution ? `
                <div class="mt-3 pt-3 border-top">
                    <strong>Resolution:</strong>
                    <p class="text-muted mb-0">${dispute.resolution}</p>
                </div>
            ` : ''}

            <div class="mt-3">
                <button class="btn btn-sm btn-outline-primary" onclick="viewDisputeDetail(${dispute.id})">
                    View Details
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * Handle dispute form submission
 */
async function handleDisputeSubmit(e) {
    e.preventDefault();

    if (!selectedShipmentId) {
        showDisputeStatus('error', 'Please select a shipment');
        return;
    }

    const disputeType = document.getElementById('disputeType').value;
    const title = document.getElementById('disputeTitle').value.trim();
    const description = document.getElementById('disputeDescription').value.trim();

    if (!disputeType || !title || !description) {
        showDisputeStatus('error', 'Please fill all required fields');
        return;
    }

    const btn = e.target.querySelector('button[type="submit"]');
    const btnText = document.getElementById('submitBtnText');
    const spinner = document.getElementById('submitBtnSpinner');

    btn.disabled = true;
    btnText.textContent = 'Submitting...';
    spinner.style.display = 'inline-block';

    try {
        const response = await fetch('/api/v1/disputes/customer/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({
                shipment_id: selectedShipmentId,
                dispute_type: disputeType,
                title: title,
                description: description
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create dispute');
        }

        const result = await response.json();

        showDisputeStatus('success', 
            `✓ Dispute ${result.dispute_number} has been filed successfully! Our support team will review it shortly.`
        );

        // Reset form
        document.getElementById('disputeForm').reset();
        selectedShipmentId = null;
        document.getElementById('selectedShipmentId').value = '';
        document.querySelectorAll('.shipment-select-item').forEach(item => {
            item.classList.remove('selected');
        });

        // Reload disputes after delay
        setTimeout(() => {
            loadDisputes();
            switchTab('existing-disputes');
        }, 2000);

    } catch (error) {
        console.error('Error creating dispute:', error);
        showDisputeStatus('error', `Failed to create dispute: ${error.message}`);
    } finally {
        btn.disabled = false;
        btnText.textContent = 'Submit Dispute';
        spinner.style.display = 'none';
    }
}

/**
 * View dispute detail (can expand to modal view)
 */
async function viewDisputeDetail(disputeId) {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch(`/api/v1/disputes/customer/${disputeId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            throw new Error('Failed to load dispute details');
        }

        const dispute = await response.json();
        showDisputeDetailModal(dispute);

    } catch (error) {
        console.error('Error loading dispute detail:', error);
        alert('Could not load dispute details');
    }
}

/**
 * Show dispute detail in modal
 */
function showDisputeDetailModal(dispute) {
    const modal = new bootstrap.Modal(document.getElementById('disputeDetailModal'));
    const content = document.getElementById('disputeDetailContent');

    content.innerHTML = `
        <div>
            <div class="row mb-4">
                <div class="col-6">
                    <div class="text-muted small">Dispute Number</div>
                    <div class="fw-bold">${dispute.dispute_number}</div>
                </div>
                <div class="col-6 text-end">
                    <span class="badge bg-${getDisputeStatusColor(dispute.status)}">
                        ${dispute.status.charAt(0).toUpperCase() + dispute.status.slice(1)}
                    </span>
                </div>
            </div>

            <h5 class="mb-3">${dispute.title}</h5>

            <div class="mb-3">
                <span class="dispute-type-badge ${dispute.dispute_type}">
                    ${disputeTypeNames[dispute.dispute_type] || dispute.dispute_type}
                </span>
            </div>

            <div class="mb-4">
                <strong>Description</strong>
                <p class="text-muted">${dispute.description}</p>
            </div>

            <div class="row mb-4">
                <div class="col-6">
                    <div class="text-muted small">Filed</div>
                    <div>${new Date(dispute.created_at).toLocaleDateString()}</div>
                </div>
                ${dispute.resolved_at ? `
                    <div class="col-6">
                        <div class="text-muted small">Resolved</div>
                        <div>${new Date(dispute.resolved_at).toLocaleDateString()}</div>
                    </div>
                ` : ''}
            </div>

            ${dispute.status === 'resolved' ? `
                <div class="alert alert-success">
                    <strong>Resolution</strong>
                    <p class="mb-0 mt-2">${dispute.resolution || 'No resolution details provided.'}</p>
                </div>
                ${dispute.refund_amount ? `
                    <div class="alert alert-info">
                        <strong>Refund Amount:</strong> $${parseFloat(dispute.refund_amount).toFixed(2)}
                    </div>
                ` : ''}
            ` : dispute.status === 'investigating' ? `
                <div class="alert alert-info">
                    <strong>Under Investigation</strong>
                    <p class="mb-0 mt-2">Our support team is actively reviewing your dispute. You'll be notified when there's an update.</p>
                </div>
            ` : `
                <div class="alert alert-warning">
                    <strong>Pending Review</strong>
                    <p class="mb-0 mt-2">Your dispute has been filed and is waiting for initial review from our support team.</p>
                </div>
            `}
        </div>
    `;

    modal.show();
}

/**
 * Show dispute status message
 */
function showDisputeStatus(type, message) {
    const container = document.getElementById('newDisputeStatus');
    container.innerHTML = `
        <div class="status-message ${type}" role="alert">
            ${message}
        </div>
    `;
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Get status color for badge
 */
function getStatusColor(status) {
    const colors = {
        'pending': 'secondary',
        'in_transit': 'primary',
        'out_for_delivery': 'info',
        'delivered': 'success',
        'cancelled': 'danger'
    };
    return colors[status] || 'secondary';
}

/**
 * Get dispute status color for badge
 */
function getDisputeStatusColor(status) {
    const colors = {
        'open': 'warning',
        'investigating': 'info',
        'resolved': 'success'
    };
    return colors[status] || 'secondary';
}
