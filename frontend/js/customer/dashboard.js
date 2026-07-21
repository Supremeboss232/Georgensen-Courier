// Customer section JS files
// dashboard.js
document.addEventListener('DOMContentLoaded', async function() {
    if (!requireCustomer()) return;
    
    try {
        const data = await getWithAuth('/api/v1/customers/dashboard');
        document.getElementById('activeCount').textContent = data.active_shipments;
        document.getElementById('deliveredCount').textContent = data.delivered_count;
        document.getElementById('totalSpent').textContent = `$${data.total_spent.toFixed(2)}`;
        document.getElementById('balance').textContent = `$${data.account_balance.toFixed(2)}`;
        
        loadRecentShipments(data.recent_shipments);
    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
});

function loadRecentShipments(shipments) {
    const tbody = document.getElementById('shipmentsTableBody');
    tbody.innerHTML = '';
    
    shipments.forEach(shipment => {
        const row = `
            <tr>
                <td>${shipment.tracking_number}</td>
                <td>${shipment.destination}</td>
                <td><span class="badge bg-info">${shipment.status}</span></td>
                <td>${shipment.date}</td>
                <td><a href="/customer/tracking?id=${shipment.id}" class="btn btn-sm btn-primary">Track</a></td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}
