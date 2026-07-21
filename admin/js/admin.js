// Main Admin Dashboard
const AdminDashboard = {
    async loadDashboardData() {
        try {
            const response = await fetch('/api/admin/dashboard');
            const data = await response.json();
            this.renderDashboard(data);
        } catch (error) {
            console.error('Error loading dashboard:', error);
        }
    },

    renderDashboard(data) {
        // Update metrics
        document.getElementById('totalOrders').textContent = data.total_orders || 0;
        document.getElementById('totalRevenue').textContent = formatCurrency(data.total_revenue || 0);
        document.getElementById('activePartners').textContent = data.active_partners || 0;
        document.getElementById('averageRating').textContent = (data.average_rating || 0).toFixed(1);

        // Update charts
        this.renderRecentOrders(data.recent_orders || []);
        this.renderRevenueChart(data.revenue_data || []);
        this.renderOrdersChart(data.orders_data || []);
    },

    renderRecentOrders(orders) {
        const tbody = document.getElementById('recentOrdersTable');
        if (!tbody) return;

        tbody.innerHTML = orders.slice(0, 5).map(order => `
            <tr>
                <td>${order.id}</td>
                <td>${order.customer}</td>
                <td>${order.service_type}</td>
                <td><span class="badge bg-info">${order.status}</span></td>
                <td>${formatCurrency(order.amount)}</td>
                <td>${formatDate(order.date)}</td>
            </tr>
        `).join('');
    },

    renderRevenueChart(data) {
        const canvas = document.getElementById('revenueChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: 'Daily Revenue',
                    data: data.map(d => d.amount),
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: true } }
            }
        });
    },

    renderOrdersChart(data) {
        const canvas = document.getElementById('ordersChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Local', 'Interstate', 'International', 'Express'],
                datasets: [{
                    label: 'Orders by Type',
                    data: data.map(d => d.count),
                    backgroundColor: ['#0d6efd', '#6c757d', '#198754', '#ffc107']
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } }
            }
        });
    }
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    AdminDashboard.loadDashboardData();
    // Refresh every 5 minutes
    setInterval(() => AdminDashboard.loadDashboardData(), 300000);
});

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-AU', {
        style: 'currency',
        currency: 'AUD'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-AU');
}
