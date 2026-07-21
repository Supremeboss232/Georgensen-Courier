// Customer section JS files
// shipments.js
document.addEventListener('DOMContentLoaded', async function() {
    if (!requireCustomer()) return;
    
    loadAddresses();
});

async function loadAddresses() {
    try {
        const data = await getWithAuth('/api/v1/customers/addresses');
        const select = document.getElementById('pickupAddress');
        if (select) {
            select.innerHTML = '<option value="">-- Select Address --</option>';
            data.addresses.forEach(addr => {
                select.innerHTML += `<option value="${addr.id}">${addr.label} - ${addr.street}</option>`;
            });
        }
    } catch (error) {
        console.error('Failed to load addresses:', error);
    }
}

async function createShipment() {
    const form = document.getElementById('createShipmentForm');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            pickup_address_id: document.getElementById('pickupAddress').value,
            recipient_name: document.getElementById('recipientName').value,
            recipient_email: document.getElementById('recipientEmail').value,
            recipient_phone: document.getElementById('recipientPhone').value,
            delivery_address: document.getElementById('deliveryAddress').value,
            weight: parseFloat(document.getElementById('weight').value),
            dimensions: document.getElementById('dimensions').value,
            description: document.getElementById('description').value,
            service_type: document.getElementById('serviceType').value
        };

        try {
            await postWithAuth('/api/v1/customers/shipments', data);
            alert('Shipment created successfully');
            window.location.href = '/customer/active-shipments';
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });
}

document.addEventListener('DOMContentLoaded', createShipment);
