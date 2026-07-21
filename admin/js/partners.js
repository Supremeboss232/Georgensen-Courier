// Admin Partners Management
const PartnersAdmin = {
    async loadPartners(filters = {}) {
        try {
            const queryString = new URLSearchParams(filters).toString();
            const response = await fetch(`/api/admin/partners?${queryString}`);
            const data = await response.json();
            this.renderPartnersTable(data);
        } catch (error) {
            console.error('Error loading partners:', error);
        }
    },

    renderPartnersTable(partners) {
        const tbody = document.getElementById('partnersTable');
        if (!tbody) return;

        tbody.innerHTML = partners.map(partner => `
            <tr>
                <td>${partner.id}</td>
                <td>${partner.business_name}</td>
                <td>${partner.contact_person}</td>
                <td><span class="badge bg-${this.getStatusColor(partner.status)}">${partner.status}</span></td>
                <td>${partner.completed_orders || 0}</td>
                <td>${(partner.rating || 0).toFixed(1)}/5</td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="PartnersAdmin.viewPartner(${partner.id})">View</button>
                    <button class="btn btn-sm btn-warning" onclick="PartnersAdmin.editPartner(${partner.id})">Edit</button>
                    <button class="btn btn-sm btn-${partner.status === 'active' ? 'danger' : 'success'}" 
                            onclick="PartnersAdmin.toggleStatus(${partner.id})">
                        ${partner.status === 'active' ? 'Suspend' : 'Activate'}
                    </button>
                </td>
            </tr>
        `).join('');
    },

    getStatusColor(status) {
        const colors = {
            'active': 'success',
            'inactive': 'secondary',
            'pending': 'warning',
            'suspended': 'danger'
        };
        return colors[status] || 'secondary';
    },

    async viewPartner(partnerId) {
        try {
            const response = await fetch(`/api/partners/${partnerId}`);
            const partner = await response.json();
            console.log('Partner details:', partner);
        } catch (error) {
            console.error('Error viewing partner:', error);
        }
    },

    async editPartner(partnerId) {
        alert('Edit partner ' + partnerId);
    },

    async toggleStatus(partnerId) {
        try {
            const response = await fetch(`/api/admin/partners/${partnerId}/toggle-status`, {
                method: 'POST'
            });
            if (response.ok) {
                this.loadPartners();
            }
        } catch (error) {
            console.error('Error toggling partner status:', error);
        }
    },

    setupEventListeners() {
        document.getElementById('filterStatus')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('filterRating')?.addEventListener('change', () => this.applyFilters());
        document.getElementById('searchInput')?.addEventListener('input', () => this.applyFilters());
    },

    applyFilters() {
        const filters = {
            status: document.getElementById('filterStatus')?.value,
            rating_min: document.getElementById('filterRating')?.value,
            search: document.getElementById('searchInput')?.value
        };
        this.loadPartners(filters);
    }
};

// Document ready
document.addEventListener('DOMContentLoaded', () => {
    PartnersAdmin.loadPartners();
    PartnersAdmin.setupEventListeners();
});
