// Admin Orders Management
const OrdersAdmin = {
    async loadOrders(filters = {}) {
        try {
            const queryString = new URLSearchParams(filters).toString();
            const response = await fetch(`/api/admin/orders?${queryString}`);
            const data = await response.json();
            this.renderOrdersTable(data);
        } catch (error) {
            console.error('Error loading orders:', error);
        }
    },

    renderOrdersTable(orders) {
        const tbody = document.getElementById('ordersTable');
        if (!tbody) return;

        tbody.innerHTML = orders.map(order => `
            <tr>
                <td>${order.id}</td>
                <td>${order.customer_email}</td>
                <td>${order.service_type}</td>
                <td><span class="badge bg-${this.getStatusColor(order.status)}">${order.status}</span></td>
                <td>${formatCurrency(order.total_amount)}</td>
                <td>${formatDate(order.created_at)}</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="OrdersAdmin.viewOrder(${order.id})">View</button>
                    <button class="btn btn-sm btn-warning" onclick="OrdersAdmin.editOrder(${order.id})">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="OrdersAdmin.deleteOrder(${order.id})">Delete</button>
                </td>
            </tr>
        `).join('');
    },

    getStatusColor(status) {
        const colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'in_transit': 'primary',
            'delivered': 'success',
            'cancelled': 'danger'
        };
        return colors[status] || 'secondary';
    },

    async viewOrder(orderId) {
        try {
            const response = await fetch(`/api/orders/${orderId}`);
            const order = await response.json();
            // Display order details modal
            console.log('Order details:', order);
        } catch (error) {
            console.error('Error viewing order:', error);
        }
    },

    async editOrder(orderId) {
        // Open edit modal
        alert('Edit order ' + orderId);
    },

    async deleteOrder(orderId) {
        if (confirm('Are you sure you want to delete this order?')) {
            try {
                await fetch(`/api/admin/orders/${orderId}`, { method: 'DELETE' });
                this.loadOrders();
            } catch (error) {
                console.error('Error deleting order:', error);
            }
        }
    },

    setupEventListeners() {
        document.getElementById('filterStatus')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('filterService')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('searchInput')?.addEventListener('input', () => this.applyFilters());
    },

    applyFilters() {
        const filters = {
            status: document.getElementById('filterStatus')?.value,
            service_type: document.getElementById('filterService')?.value,
            search: document.getElementById('searchInput')?.value
        };
        this.loadOrders(filters);
    }
};

// Document ready
document.addEventListener('DOMContentLoaded', () => {
    OrdersAdmin.loadOrders();
    OrdersAdmin.setupEventListeners();
});
