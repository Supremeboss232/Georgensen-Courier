// Customer Profile & Security Handler
document.addEventListener('DOMContentLoaded', async () => {
    if (typeof requireCustomer === 'function' && !requireCustomer()) {
        return;
    }

    await loadCustomerProfile();

    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }
});

async function loadCustomerProfile() {
    try {
        const user = await getWithAuth('/auth/me');
        const profile = await getWithAuth('/customers/profile').catch(() => ({}));

        const fullName = (user && user.full_name) || '';
        const parts = fullName.trim().split(/\s+/);
        const firstName = parts[0] || '';
        const lastName = parts.slice(1).join(' ') || '';

        const firstEl = document.getElementById('firstName');
        const lastEl = document.getElementById('lastName');
        const emailEl = document.getElementById('email');
        const phoneEl = document.getElementById('phone');
        const companyEl = document.getElementById('company');

        if (firstEl) firstEl.value = firstName;
        if (lastEl) lastEl.value = lastName;
        if (emailEl) emailEl.value = (user && user.email) || '';
        if (phoneEl) phoneEl.value = (profile && profile.phone) || (user && user.phone) || '';
        if (companyEl) companyEl.value = (profile && profile.company_name) || '';
    } catch (err) {
        console.error('Failed to load profile:', err);
    }
}

async function handleProfileUpdate(event) {
    event.preventDefault();
    const firstName = (document.getElementById('firstName')?.value || '').trim();
    const lastName = (document.getElementById('lastName')?.value || '').trim();
    const phone = (document.getElementById('phone')?.value || '').trim();
    const company = (document.getElementById('company')?.value || '').trim();

    const fullName = `${firstName} ${lastName}`.trim();

    try {
        await putWithAuth('/auth/me', { full_name: fullName, phone });
        await putWithAuth('/customers/profile', {
            company_name: company || fullName || 'Individual',
            phone
        });

        const storedUser = getUser();
        storedUser.full_name = fullName;
        storedUser.phone = phone;
        setUser(storedUser);

        showNotification('Profile updated successfully!', 'success');
    } catch (err) {
        showNotification(err.message || 'Failed to update profile', 'error');
    }
}

async function changePassword() {
    const currentPassword = document.getElementById('currentPassword')?.value || '';
    const newPassword = document.getElementById('newPassword')?.value || '';
    const confirmPassword = document.getElementById('confirmPassword')?.value || '';

    if (!currentPassword || !newPassword) {
        showNotification('Please enter both current and new passwords.', 'error');
        return;
    }
    if (newPassword.length < 8) {
        showNotification('New password must be at least 8 characters.', 'error');
        return;
    }
    if (newPassword !== confirmPassword) {
        showNotification('New password and confirmation do not match.', 'error');
        return;
    }

    try {
        await postWithAuth('/auth/change-password', {
            old_password: currentPassword,
            new_password: newPassword
        });
        showNotification('Password changed successfully!', 'success');
        const form = document.getElementById('changePasswordForm');
        if (form) form.reset();
    } catch (err) {
        showNotification(err.message || 'Failed to change password', 'error');
    }
}

window.changePassword = changePassword;
