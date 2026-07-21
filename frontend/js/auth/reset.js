// Auth section JS files
// reset.js - Password reset handler with Celery background task integration

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already authenticated
    // guards.js provides the redirectIfAuthenticated() function
    if (typeof redirectIfAuthenticated === 'function') {
        redirectIfAuthenticated();
    }
    
    const form = document.getElementById('forgotPasswordForm');
    if (form) {
        form.addEventListener('submit', handlePasswordReset);
    }
});

/**
 * Main password reset handler
 * Submits email to backend which triggers async Celery task for email delivery
 */
async function handlePasswordReset(e) {
    e.preventDefault();
    
    // Get form values
    const email = document.getElementById('email')?.value?.trim();
    
    // Get UI references
    const responseMessage = document.getElementById('responseMessage');
    const responseIcon = document.getElementById('responseIcon');
    const responseText = document.getElementById('responseText');
    const submitBtn = document.getElementById('submitBtn');
    const submitText = document.getElementById('submitText');
    const submitSpinner = document.getElementById('submitSpinner');
    const form = document.getElementById('forgotPasswordForm');
    
    // Clear previous messages
    if (responseMessage) {
        responseMessage.classList.remove('show', 'success-message', 'error-message', 'info-message');
    }
    
    // ============ VALIDATION ============
    
    if (!email) {
        showResponse(
            'error',
            '<i class="fas fa-exclamation-circle icon-error"></i>Please enter your email address',
            responseMessage,
            responseIcon,
            responseText
        );
        return;
    }
    
    if (!isValidEmail(email)) {
        showResponse(
            'error',
            '<i class="fas fa-exclamation-circle icon-error"></i>Please enter a valid email address',
            responseMessage,
            responseIcon,
            responseText
        );
        return;
    }
    
    // ============ SUBMISSION ============
    
    // Show loading state
    if (submitBtn && submitText && submitSpinner) {
        submitBtn.disabled = true;
        submitText.style.display = 'none';
        submitSpinner.style.display = 'inline';
    }
    
    try {
        // Send password reset request to backend
        // Backend will trigger async Celery task to send email
        const response = await post('/auth/forgot-password', { email });
        
        // Success handling
        if (response && response.message) {
            // Clear the form
            if (form) {
                form.reset();
            }
            
            // Show success message
            showResponse(
                'success',
                '<i class="fas fa-check-circle icon-success"></i>' + response.message,
                responseMessage,
                responseIcon,
                responseText
            );
            
            // Optionally redirect to login after delay
            setTimeout(() => {
                // Uncomment to redirect:
                // window.location.href = '/auth/login';
            }, 3000);
        } else {
            showResponse(
                'error',
                '<i class="fas fa-exclamation-circle icon-error"></i>Unexpected response from server',
                responseMessage,
                responseIcon,
                responseText
            );
        }
    } catch (error) {
        // Error handling
        let errorMsg = '<i class="fas fa-exclamation-circle icon-error"></i>';
        
        if (error.response && error.response.status === 404) {
            // Email not found - don't reveal for security
            errorMsg += 'If an account exists with this email, you will receive a password reset link.';
            showResponse(
                'info',
                errorMsg,
                responseMessage,
                responseIcon,
                responseText
            );
        } else if (error.message) {
            errorMsg += 'Error: ' + error.message;
            showResponse(
                'error',
                errorMsg,
                responseMessage,
                responseIcon,
                responseText
            );
        } else {
            errorMsg += 'An error occurred. Please try again later.';
            showResponse(
                'error',
                errorMsg,
                responseMessage,
                responseIcon,
                responseText
            );
        }
        
        // Reset loading state
        if (submitBtn && submitText && submitSpinner) {
            submitBtn.disabled = false;
            submitText.style.display = 'inline';
            submitSpinner.style.display = 'none';
        }
    }
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Display response message (success, error, or info)
 * No page refresh - just updates UI
 */
function showResponse(type, message, container, iconElement, textElement) {
    if (container) {
        // Remove previous classes
        container.classList.remove('success-message', 'error-message', 'info-message');
        
        // Add appropriate class based on type
        switch(type) {
            case 'success':
                container.classList.add('success-message');
                break;
            case 'error':
                container.classList.add('error-message');
                break;
            case 'info':
                container.classList.add('info-message');
                break;
        }
        
        // Set message content
        if (textElement) {
            textElement.innerHTML = message;
        }
        
        // Show the message with animation
        container.classList.add('show');
        
        // Scroll to message
        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}
