// Customer section JS files
// billing.js
document.addEventListener('DOMContentLoaded', async function() {
    if (!requireCustomer()) return;
    
    try {
        const data = await getWithAuth('/api/v1/customers/billing');
        document.getElementById('balance').textContent = `$${data.balance.toFixed(2)}`;
        
        loadInvoices(data.invoices);
        loadPayments(data.payments);
    } catch (error) {
        console.error('Failed to load billing:', error);
    }
});

function loadInvoices(invoices) {
    const tbody = document.getElementById('invoicesTableBody');
    if (tbody) {
        tbody.innerHTML = '';
        invoices.forEach(inv => {
            const row = `
                <tr>
                    <td>${inv.invoice_number}</td>
                    <td>${inv.date}</td>
                    <td>$${inv.amount.toFixed(2)}</td>
                    <td><span class="badge bg-${inv.status === 'paid' ? 'success' : 'warning'}">${inv.status}</span></td>
                    <td><a href="/invoice/${inv.id}" class="btn btn-sm btn-primary">View</a></td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    }
}

function loadPayments(payments) {
    const tbody = document.getElementById('paymentsTableBody');
    if (tbody) {
        tbody.innerHTML = '';
        payments.forEach(pay => {
            const row = `
                <tr>
                    <td>${pay.date}</td>
                    <td>${pay.type}</td>
                    <td>$${pay.amount.toFixed(2)}</td>
                    <td><span class="badge bg-success">${pay.status}</span></td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    }
}

async function processPayment() {
    const amount = document.getElementById('amount').value;
    const paymentMethod = document.getElementById('paymentMethod').value;

    try {
        await postWithAuth('/api/v1/customers/payments', {
            amount: parseFloat(amount),
            payment_method: paymentMethod
        });
        alert('Payment processed successfully');
        location.reload();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}
