// Auth section JS files
// login.js
document.addEventListener('DOMContentLoaded', function() {
    redirectIfAuthenticated();
    
    const form = document.getElementById('loginForm');
    if (form) {
        form.addEventListener('submit', handleLogin);
    }
});

async function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
        const response = await post('/auth/login', { email, password });
        setAuthToken(response.access_token);
        setUser(response.user);
        
        // Redirect based on role
        switch(response.user.role) {
            case 'customer':
                window.location.href = '/customer/dashboard';
                break;
            case 'partner':
                window.location.href = '/partner/dashboard';
                break;
            case 'admin':
                window.location.href = '/admin/dashboard';
                break;
            default:
                window.location.href = '/';
        }
    } catch (error) {
        alert('Login failed: ' + error.message);
    }
}
