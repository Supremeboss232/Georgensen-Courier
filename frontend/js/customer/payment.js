/**
 * Payment Form Handler
 * Manages Stripe payment processing for customer invoices
 */

let stripe = null;
let elements = null;
let cardElement = null;
let selectedInvoiceId = null;

document.addEventListener('DOMContentLoaded', async () => {
    await initializeStripe();
    await loadInvoices();
    await loadPaymentHistory();
    setupEventListeners();
});

/**
 * Initialize Stripe Elements
 */
async function initializeStripe() {
    try {
        // Get publishable key from backend
        const response = await fetch('/api/v1/payments/intents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({ invoice_id: 0 }) // Dummy request to get publishable key
        }).catch(() => null);

        if (response && response.ok) {
            const data = await response.json();
            if (data.publishable_key) {
                stripe = Stripe(data.publishable_key);
                elements = stripe.elements();
                cardElement = elements.create('card');
                cardElement.mount('#card-element');
                
                // Handle real-time validation errors from Stripe
                cardElement.addEventListener('change', (event) => {
                    handleCardError(event.error);
                });
            }
        } else {
            // Try alternative way to get publishable key
            initializeStripeWithTestKey();
        }
    } catch (error) {
        console.error('Error initializing Stripe:', error);
        initializeStripeWithTestKey();
    }
}

/**
 * Fallback: Initialize with test key (for development)
 * In production, always fetch from backend
 */
function initializeStripeWithTestKey() {
    const testKey = 'pk_test_51234567890abcdefghijklmnop'; // This should be fetched dynamically
    try {
        stripe = Stripe(testKey);
        elements = stripe.elements();
        cardElement = elements.create('card');
        cardElement.mount('#card-element');
        
        cardElement.addEventListener('change', (event) => {
            handleCardError(event.error);
        });
    } catch (error) {
        console.error('Stripe initialization failed:', error);
        showStatus('error', 'Payment system unavailable. Please try again later.');
    }
}

/**
 * Load customer invoices
 */
async function loadInvoices() {
    try {
        const token = localStorage.getItem('authToken');
        if (!token) {
            window.location.href = '/auth/login';
            return;
        }

        const response = await fetch('/api/v1/customers/invoices', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const invoices = await response.json();
        displayInvoices(invoices);

    } catch (error) {
        console.error('Error loading invoices:', error);
        document.getElementById('invoiceList').innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> Could not load invoices. Please refresh the page.
            </div>
        `;
    }
}

/**
 * Display invoices in the list
 */
function displayInvoices(invoices) {
    const container = document.getElementById('invoiceList');

    if (!invoices || invoices.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <strong>No pending invoices</strong>
                <p class="mb-0 mt-2">You don't have any unpaid invoices at this time.</p>
            </div>
        `;
        document.getElementById('paymentBtn').disabled = true;
        return;
    }

    // Filter for unpaid invoices
    const unpaidInvoices = invoices.filter(inv => inv.status !== 'paid');

    if (unpaidInvoices.length === 0) {
        container.innerHTML = `
            <div class="alert alert-success">
                <strong>✓ All paid!</strong>
                <p class="mb-0 mt-2">You have no outstanding invoices.</p>
            </div>
        `;
        document.getElementById('paymentBtn').disabled = true;
        return;
    }

    container.innerHTML = unpaidInvoices.map(invoice => `
        <div class="invoice-card p-3 cursor-pointer" data-invoice-id="${invoice.id}">
            <div class="row align-items-center">
                <div class="col-8">
                    <div class="fw-bold">Invoice #${invoice.id}</div>
                    <small class="text-muted">
                        ${new Date(invoice.created_at).toLocaleDateString()} • 
                        ${invoice.description || 'Shipping Invoice'}
                    </small>
                </div>
                <div class="col-4 text-end">
                    <div class="fw-bold text-primary">$${parseFloat(invoice.total_amount).toFixed(2)}</div>
                    <small class="text-muted">${invoice.status}</small>
                </div>
            </div>
        </div>
    `).join('');

    // Add click handlers
    document.querySelectorAll('.invoice-card').forEach(card => {
        card.addEventListener('click', () => selectInvoice(card));
    });
}

/**
 * Select invoice for payment
 */
function selectInvoice(cardElement) {
    // Remove previous selection
    document.querySelectorAll('.invoice-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Select new card
    cardElement.classList.add('selected');
    selectedInvoiceId = parseInt(cardElement.dataset.invoiceId);

    // Update summary
    const text = cardElement.textContent;
    const match = text.match(/Invoice #(\d+).*?\$([\d.]+)/);
    if (match) {
        document.getElementById('invoiceSummary').style.display = 'block';
        document.getElementById('summaryInvoiceNum').textContent = match[1];
        document.getElementById('summaryAmount').textContent = match[2];
    }

    // Enable payment button
    document.getElementById('paymentBtn').disabled = false;

    // Focus to payment form
    document.querySelector('.payment-form-container').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Payment button click
    document.getElementById('paymentBtn').addEventListener('click', handlePayment);

    // Auto-fill email if available
    const userEmail = localStorage.getItem('userEmail');
    if (userEmail) {
        document.getElementById('receiptEmail').value = userEmail;
    }
}

/**
 * Handle payment submission
 */
async function handlePayment(e) {
    e.preventDefault();

    if (!selectedInvoiceId) {
        showStatus('error', 'Please select an invoice');
        return;
    }

    if (!document.getElementById('termsCheck').checked) {
        showStatus('error', 'You must agree to the payment terms');
        return;
    }

    const cardholderName = document.getElementById('cardholderName').value.trim();
    const receiptEmail = document.getElementById('receiptEmail').value.trim();

    if (!cardholderName) {
        showStatus('error', 'Please enter cardholder name');
        return;
    }

    if (!receiptEmail || !isValidEmail(receiptEmail)) {
        showStatus('error', 'Please enter valid email');
        return;
    }

    // Disable button and show loading
    const btn = document.getElementById('paymentBtn');
    const btnText = document.getElementById('btnText');
    const spinner = document.getElementById('btnSpinner');

    btn.disabled = true;
    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';

    try {
        // Step 1: Create payment intent
        showStatus('info', 'Creating payment intent...');
        const intentResponse = await fetch('/api/v1/payments/intents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({ invoice_id: selectedInvoiceId })
        });

        if (!intentResponse.ok) {
            const error = await intentResponse.json();
            throw new Error(error.detail || 'Failed to create payment intent');
        }

        const intentData = await intentResponse.json();
        const clientSecret = intentData.client_secret;

        // Step 2: Confirm payment with Stripe
        showStatus('info', 'Processing payment with Stripe...');
        const confirmResult = await stripe.confirmCardPayment(clientSecret, {
            payment_method: {
                card: cardElement,
                billing_details: { name: cardholderName }
            }
        });

        if (confirmResult.error) {
            throw new Error(confirmResult.error.message);
        }

        // Step 3: Confirm with backend
        showStatus('info', 'Confirming payment...');
        const confirmResponse = await fetch(`/api/v1/payments/intents/${intentData.intent_id}/confirm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            }
        });

        if (!confirmResponse.ok) {
            throw new Error('Payment confirmation failed');
        }

        const confirmData = await confirmResponse.json();

        // Success!
        showStatus('success', `✓ Payment successful! Invoice #${confirmData.invoice_id} has been paid.`);
        
        // Reset form
        document.getElementById('disputeForm')?.reset?.();
        cardElement.clear();
        selectedInvoiceId = null;
        document.getElementById('invoiceSummary').style.display = 'none';

        // Reload data
        setTimeout(() => {
            loadInvoices();
            loadPaymentHistory();
        }, 1500);

    } catch (error) {
        console.error('Payment error:', error);
        showStatus('error', `Payment failed: ${error.message}`);
    } finally {
        // Re-enable button
        btn.disabled = false;
        btnText.style.display = 'inline';
        spinner.style.display = 'none';
    }
}

/**
 * Handle card errors
 */
function handleCardError(error) {
    const errorElement = document.getElementById('card-errors');
    if (error) {
        errorElement.textContent = error.message;
        errorElement.style.display = 'block';
    } else {
        errorElement.textContent = '';
        errorElement.style.display = 'none';
    }
}

/**
 * Load payment history
 */
async function loadPaymentHistory() {
    try {
        const token = localStorage.getItem('authToken');
        const response = await fetch('/api/v1/customers/invoices', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) return;

        const invoices = await response.json();
        const paidInvoices = invoices.filter(inv => inv.status === 'paid').slice(0, 5);

        const tbody = document.getElementById('paymentHistoryBody');
        if (paidInvoices.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted py-3">No payment history</td></tr>`;
            return;
        }

        tbody.innerHTML = paidInvoices.map(inv => `
            <tr>
                <td>#${inv.id}</td>
                <td>$${parseFloat(inv.total_amount).toFixed(2)}</td>
                <td><span class="badge bg-success">Paid</span></td>
                <td>${new Date(inv.created_at).toLocaleDateString()}</td>
            </tr>
        `).join('');

    } catch (error) {
        console.error('Error loading payment history:', error);
    }
}

/**
 * Show status message
 */
function showStatus(type, message) {
    const container = document.getElementById('statusMessage');
    container.innerHTML = `
        <div class="payment-status ${type}" role="alert">
            ${message}
        </div>
    `;
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
