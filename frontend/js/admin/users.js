// Georgensen Admin - User Management
let allUsers = [];
let filteredUsers = [];
let selectedUsers = new Set();
let currentUser = null;

const roleMap = {
    'customer': { label: 'Customer (Sender)', color: 'customer' },
    'partner': { label: 'Partner (Driver)', color: 'partner' },
    'regional_mgr': { label: 'Regional Manager', color: 'regional-mgr' },
    'admin': { label: 'Global Admin', color: 'admin' }
};

const complianceStatusMap = {
    'verified': { label: '✓ KYC Verified', color: 'verified', icon: 'check-circle' },
    'pending': { label: '⧗ Pending', color: 'pending', icon: 'hourglass' },
    'expired': { label: '⚠ Expired', color: 'expired', icon: 'exclamation-triangle' },
    'inactive': { label: 'Inactive', color: 'inactive', icon: 'times-circle' }
};

const regions = {
    'north_america': '🇺🇸 North America',
    'europe': '🇪🇺 Europe',
    'asia_pacific': '🌏 Asia Pacific',
    'middle_east': '🇦🇪 Middle East',
    'latin_america': '🇧🇷 Latin America'
};

document.addEventListener('DOMContentLoaded', async function() {
    if (!requireAdmin()) return;
    
    // Load users
    await loadUsers();
    
    // Setup search
    document.getElementById('globalUserSearch').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performUserSearch();
    });
});

async function loadUsers() {
    try {
        const response = await getWithAuth('/admin/users');
        allUsers = response || [];
        filteredUsers = [...allUsers];
        renderUsers();
    } catch (error) {
        console.error('Failed to load users:', error);
        showErrorState('Failed to load users');
    }
}

function renderUsers() {
    const tbody = document.getElementById('usersTableBody');
    
    if (!filteredUsers || filteredUsers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No users found</td></tr>';
        return;
    }
    
    tbody.innerHTML = filteredUsers.map((user, idx) => `
        <tr onclick="selectUserRow(${idx}, event)">
            <td>
                <div class="form-check">
                    <input class="form-check-input user-checkbox" type="checkbox" 
                           data-user-id="${user.id}" 
                           onchange="handleCheckboxChange(${user.id}, this)" />
                </div>
            </td>
            <td><strong>${user.id || 'N/A'}</strong></td>
            <td>
                <a href="#" onclick="viewUserDetails(${user.id}); return false;">
                    ${user.full_name || 'N/A'}
                </a>
            </td>
            <td>
                <div>${user.email || 'N/A'}</div>
                <small class="text-muted">${user.phone || 'No phone'}</small>
            </td>
            <td>
                <span class="role-badge role-${roleMap[user.role]?.color || 'customer'}">
                    ${roleMap[user.role]?.label || user.role}
                </span>
            </td>
            <td>
                <span class="region-chip">${regions[user.primary_region] || user.primary_region || '---'}</span>
            </td>
            <td>
                <span class="status-badge status-${user.compliance_status || 'pending'}">
                    <i class="fas fa-${complianceStatusMap[user.compliance_status]?.icon || 'question'}"></i>
                    ${complianceStatusMap[user.compliance_status]?.label || 'Unknown'}
                </span>
            </td>
            <td>
                ${formatJoinedDate(user.created_at)}
                <div class="timezone-info">UTC ${user.timezone || 'UTC'}</div>
            </td>
            <td>
                <button class="btn btn-sm btn-info" onclick="viewUserDetails(${user.id}); event.stopPropagation();">
                    <i class="fas fa-eye"></i> View
                </button>
            </td>
        </tr>
    `).join('');
    
    // Reset select all checkbox
    document.getElementById('selectAllCheckbox').checked = false;
}

function filterUsers() {
    const regionFilter = document.getElementById('regionFilter').value;
    const roleFilter = document.getElementById('roleFilter').value;
    const complianceFilter = document.getElementById('complianceFilter').value;
    
    filteredUsers = allUsers.filter(user => {
        const regionMatch = !regionFilter || user.primary_region === regionFilter;
        const roleMatch = !roleFilter || user.role === roleFilter;
        const complianceMatch = !complianceFilter || user.compliance_status === complianceFilter;
        
        return regionMatch && roleMatch && complianceMatch;
    });
    
    renderUsers();
}

function performUserSearch() {
    const searchTerm = document.getElementById('globalUserSearch').value.toLowerCase().trim();
    
    if (!searchTerm) {
        filteredUsers = [...allUsers];
        renderUsers();
        return;
    }
    
    filteredUsers = allUsers.filter(user => {
        const id = (user.id || '').toString().toLowerCase();
        const email = (user.email || '').toLowerCase();
        const phone = (user.phone || '').toLowerCase();
        const name = (user.full_name || '').toLowerCase();
        
        return id.includes(searchTerm) || 
               email.includes(searchTerm) || 
               phone.includes(searchTerm) ||
               name.includes(searchTerm);
    });
    
    renderUsers();
}

function handleCheckboxChange(userId, checkbox) {
    if (checkbox.checked) {
        selectedUsers.add(userId);
    } else {
        selectedUsers.delete(userId);
    }
    
    updateBulkActionsBar();
}

function selectUserRow(idx, event) {
    const checkbox = event.currentTarget.querySelector('.form-check-input');
    if (event.target !== checkbox && !event.target.closest('.form-check')) {
        checkbox.checked = !checkbox.checked;
        handleCheckboxChange(filteredUsers[idx].id, checkbox);
    }
}

function toggleSelectAll(checkbox) {
    const userCheckboxes = document.querySelectorAll('.user-checkbox');
    
    if (checkbox.checked) {
        userCheckboxes.forEach(cb => {
            cb.checked = true;
            handleCheckboxChange(cb.dataset.userId, cb);
        });
    } else {
        selectedUsers.clear();
        userCheckboxes.forEach(cb => cb.checked = false);
        updateBulkActionsBar();
    }
}

function updateBulkActionsBar() {
    const bar = document.getElementById('bulkActionsBar');
    const count = selectedUsers.size;
    
    if (count > 0) {
        bar.classList.add('active');
        document.getElementById('selectedCount').textContent = 
            `${count} user${count !== 1 ? 's' : ''} selected`;
    } else {
        bar.classList.remove('active');
    }
}

function resetBulkSelection() {
    selectedUsers.clear();
    document.querySelectorAll('.user-checkbox').forEach(cb => cb.checked = false);
    document.getElementById('selectAllCheckbox').checked = false;
    updateBulkActionsBar();
}

async function viewUserDetails(userId) {
    try {
        const user = allUsers.find(u => u.id == userId);
        if (!user) return;
        
        currentUser = user;
        
        // Populate modal
        document.getElementById('modalUserName').textContent = user.full_name || 'User Details';
        document.getElementById('modalAccountId').textContent = user.id || '---';
        document.getElementById('modalEmail').textContent = user.email || '---';
        document.getElementById('modalPhone').textContent = user.phone || '---';
        document.getElementById('modalRole').textContent = roleMap[user.role]?.label || user.role;
        document.getElementById('modalRegion').textContent = regions[user.primary_region] || user.primary_region || '---';
        
        // Compliance information
        document.getElementById('modalKycStatus').innerHTML = 
            `<span class="status-badge status-${user.kyc_status || 'pending'}">
                <i class="fas fa-${complianceStatusMap[user.kyc_status]?.icon || 'question'}"></i>
                ${complianceStatusMap[user.kyc_status]?.label || 'Pending'}
            </span>`;
        
        document.getElementById('modalBackgroundCheck').textContent = 
            user.background_check_status || 'Not checked';
        
        document.getElementById('modalDocExpiry').textContent = 
            user.document_expiry ? formatDate(user.document_expiry) : 'N/A';
        
        document.getElementById('modalLastVerified').textContent = 
            user.last_verified ? formatDate(user.last_verified) : 'Never';
        
        // Load logistics history
        loadUserLogisticsHistory(userId);
        
        // Show modal
        document.getElementById('userDetailModal').classList.add('show');
        
    } catch (error) {
        console.error('Failed to load user details:', error);
        alert('Failed to load user details');
    }
}

async function loadUserLogisticsHistory(userId) {
    try {
        const history = await getWithAuth(`/admin/users/${userId}/logistics-history`);
        const historyContainer = document.getElementById('modalLogisticsHistory');
        
        if (!history || history.length === 0) {
            historyContainer.innerHTML = '<p class="text-muted">No logistics history found</p>';
            return;
        }
        
        historyContainer.innerHTML = history.map(record => `
            <div class="compliance-row">
                <strong>${record.shipment_count || 0} shipments</strong> in ${regions[record.region] || record.region}
                <br/><small class="text-muted">Rating: ${record.rating || 'N/A'} | Last active: ${formatDate(record.last_active)}</small>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Failed to load logistics history:', error);
        document.getElementById('modalLogisticsHistory').innerHTML = 
            '<p class="text-danger">Failed to load history</p>';
    }
}

function closeUserModal() {
    document.getElementById('userDetailModal').classList.remove('show');
    currentUser = null;
}

function openUserModal() {
    // For adding new user - would open a form modal
    alert('New user creation form would open here');
}

function editUser() {
    if (!currentUser) return;
    alert(`Edit user form for ${currentUser.full_name} would open here`);
}

function deactivateUser() {
    if (!currentUser) return;
    
    if (confirm(`Deactivate account for ${currentUser.full_name}? This action cannot be undone immediately.`)) {
        // API call to deactivate
        console.log('Deactivating user:', currentUser.id);
        closeUserModal();
        loadUsers();
    }
}

async function sendRegionalUpdate() {
    if (selectedUsers.size === 0) {
        alert('Please select users first');
        return;
    }
    
    const region = prompt('Enter region or message for regional update:');
    if (!region) return;
    
    try {
        const result = await post('/admin/users/bulk-action', {
            user_ids: Array.from(selectedUsers),
            action: 'send_regional_update',
            message: region
        });
        
        alert(`Regional update sent to ${selectedUsers.size} users`);
        resetBulkSelection();
        loadUsers();
    } catch (error) {
        console.error('Failed to send update:', error);
        alert('Failed to send regional update');
    }
}

async function suspendRegionalAccess() {
    if (selectedUsers.size === 0) {
        alert('Please select users first');
        return;
    }
    
    if (!confirm(`Suspend regional access for ${selectedUsers.size} users?`)) return;
    
    try {
        const result = await post('/admin/users/bulk-action', {
            user_ids: Array.from(selectedUsers),
            action: 'suspend_regional_access'
        });
        
        alert(`Access suspended for ${selectedUsers.size} users`);
        resetBulkSelection();
        loadUsers();
    } catch (error) {
        console.error('Failed to suspend access:', error);
        alert('Failed to suspend access');
    }
}

function formatJoinedDate(dateStr) {
    if (!dateStr) return '---';
    
    try {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
        if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
        
        return `${Math.floor(diffDays / 365)} years ago`;
    } catch (e) {
        return '---';
    }
}

function formatDate(dateStr) {
    if (!dateStr) return '---';
    try {
        return new Date(dateStr).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        return '---';
    }
}

function showErrorState(message) {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = `<tr><td colspan="9" class="text-center text-danger">${message}</td></tr>`;
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
