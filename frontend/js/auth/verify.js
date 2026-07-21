// Auth section JS files
// verify.js - Email verification handler with resend logic

// Constants for resend cooldown
const RESEND_COOLDOWN_SECONDS = 60;
let resendCooldownActive = false;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form handlers
    const form = document.getElementById('verifyEmailForm');
    const resendLink = document.getElementById('resendLink');
    const codeInput = document.getElementById('code');
    
    if (form) {
        form.addEventListener('submit', handleVerifyEmail);
    }
    
    if (resendLink) {
        resendLink.addEventListener('click', handleResendCode);
    }
    
    // Auto-format code input - only allow numbers and max 6 digits
    if (codeInput) {
        codeInput.addEventListener('input', function(e) {
            // Remove any non-numeric characters
            this.value = this.value.replace(/[^0-9]/g, '');
            
            // Limit to 6 digits
            if (this.value.length > 6) {
                this.value = this.value.slice(0, 6);
            }
            
            // Clear status message when user starts typing
            const status = document.getElementById('verificationStatus');
            if (status) {
                status.classList.remove('show');
            }
        });
    }
});

/**
 * Handle email verification form submission
 */
async function handleVerifyEmail(e) {
    e.preventDefault();
    
    const code = document.getElementById('code')?.value?.trim();
    const verificationStatus = document.getElementById('verificationStatus');
    const statusIcon = document.getElementById('statusIcon');
    const statusText = document.getElementById('statusText');
    const submitBtn = document.getElementById('submitBtn');
    const submitText = document.getElementById('submitText');
    const submitSpinner = document.getElementById('submitSpinner');
    
    // Clear previous status
    if (verificationStatus) {
        verificationStatus.classList.remove('show', 'success-status', 'error-status', 'info-status');
    }
    
    // ============ VALIDATION ============
    
    if (!code || code.length === 0) {
        showVerificationStatus(
            'error',
            '<i class="fas fa-exclamation-circle"></i>Please enter the verification code',
            verificationStatus,
            statusIcon,
            statusText
        );
        return;
    }
    
    if (!/^\d{6}$/.test(code)) {
        showVerificationStatus(
            'error',
            '<i class="fas fa-exclamation-circle"></i>Verification code must be 6 digits',
            verificationStatus,
            statusIcon,
            statusText
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
        // Send verification request to backend
        const response = await post('/auth/verify-email', { code });
        
        // Success handling
        if (response && response.status === 'success') {
            showVerificationStatus(
                'success',
                '<i class="fas fa-check-circle"></i> Email verified successfully! Redirecting to dashboard...',
                verificationStatus,
                statusIcon,
                statusText
            );
            
            // Store auth tokens if provided
            if (response.access_token) {
                if (typeof setAuthToken === 'function') {
                    setAuthToken(response.access_token);
                }
                if (response.refresh_token) {
                    localStorage.setItem('refresh_token', response.refresh_token);
                }
            }
            
            // Redirect to dashboard after brief delay
            setTimeout(() => {
                const userRole = response.user?.role || 'customer';
                if (userRole === 'partner') {
                    window.location.href = '/partner/dashboard';
                } else if (userRole === 'admin') {
                    window.location.href = '/admin/dashboard';
                } else {
                    window.location.href = '/customer/dashboard';
                }
            }, 1500);
        } else {
            showVerificationStatus(
                'error',
                '<i class="fas fa-exclamation-circle"></i>Unexpected response from server',
                verificationStatus,
                statusIcon,
                statusText
            );
            
            // Reset button state
            if (submitBtn && submitText && submitSpinner) {
                submitBtn.disabled = false;
                submitText.style.display = 'inline';
                submitSpinner.style.display = 'none';
            }
        }
    } catch (error) {
        // Error handling
        let errorMsg = '<i class="fas fa-exclamation-circle"></i>';
        
        if (error.response && error.response.status === 400) {
            errorMsg += 'Invalid verification code. Please try again.';
        } else if (error.response && error.response.status === 401) {
            errorMsg += 'Verification code expired. Please request a new one.';
        } else if (error.response && error.response.status === 404) {
            errorMsg += 'User or verification record not found.';
        } else if (error.message) {
            errorMsg += 'Error: ' + error.message;
        } else {
            errorMsg += 'Verification failed. Please try again.';
        }
        
        showVerificationStatus(
            'error',
            errorMsg,
            verificationStatus,
            statusIcon,
            statusText
        );
        
        // Reset button state
        if (submitBtn && submitText && submitSpinner) {
            submitBtn.disabled = false;
            submitText.style.display = 'inline';
            submitSpinner.style.display = 'none';
        }
    }
}

/**
 * Handle resend verification code
 */
async function handleResendCode(e) {
    e.preventDefault();
    
    const resendLink = document.getElementById('resendLink');
    const resendTimer = document.getElementById('resendTimer');
    const verificationStatus = document.getElementById('verificationStatus');
    const statusIcon = document.getElementById('statusIcon');
    const statusText = document.getElementById('statusText');
    
    // Prevent multiple rapid clicks
    if (resendCooldownActive) {
        return;
    }
    
    // Disable resend button during cooldown
    resendCooldownActive = true;
    if (resendLink) {
        resendLink.disabled = true;
        resendLink.style.opacity = '0.6';
    }
    
    try {
        // Send resend request to backend
        const response = await post('/auth/resend-verification', {});
        
        // Success handling
        if (response && response.status === 'success') {
            showVerificationStatus(
                'info',
                '<i class="fas fa-envelope"></i> ' + response.message,
                verificationStatus,
                statusIcon,
                statusText
            );
            
            // Start cooldown timer
            startResendCooldown(resendLink, resendTimer);
        } else {
            showVerificationStatus(
                'error',
                '<i class="fas fa-exclamation-circle"></i>Failed to resend verification code',
                verificationStatus,
                statusIcon,
                statusText
            );
            
            // Reset button
            resendCooldownActive = false;
            if (resendLink) {
                resendLink.disabled = false;
                resendLink.style.opacity = '1';
            }
        }
    } catch (error) {
        let errorMsg = '<i class="fas fa-exclamation-circle"></i>';
        
        if (error.message) {
            errorMsg += 'Error: ' + error.message;
        } else {
            errorMsg += 'Failed to resend verification code. Please try again.';
        }
        
        showVerificationStatus(
            'error',
            errorMsg,
            verificationStatus,
            statusIcon,
            statusText
        );
        
        // Reset button
        resendCooldownActive = false;
        if (resendLink) {
            resendLink.disabled = false;
            resendLink.style.opacity = '1';
        }
    }
}

/**
 * Start cooldown timer for resend button
 */
function startResendCooldown(resendLink, resendTimer) {
    let secondsLeft = RESEND_COOLDOWN_SECONDS;
    
    if (resendTimer) {
        resendTimer.textContent = `(${secondsLeft}s)`;
    }
    
    const interval = setInterval(() => {
        secondsLeft--;
        
        if (resendTimer) {
            resendTimer.textContent = secondsLeft > 0 ? `(${secondsLeft}s)` : '';
        }
        
        if (secondsLeft <= 0) {
            clearInterval(interval);
            resendCooldownActive = false;
            
            if (resendLink) {
                resendLink.disabled = false;
                resendLink.style.opacity = '1';
            }
        }
    }, 1000);
}

/**
 * Display verification status message
 * Type can be: 'success', 'error', 'info', 'warning'
 */
function showVerificationStatus(type, message, container, iconElement, textElement) {
    if (container) {
        // Remove previous classes
        container.classList.remove('success-status', 'error-status', 'info-status', 'warning-status');
        
        // Add appropriate class based on type
        switch(type) {
            case 'success':
                container.classList.add('success-status');
                break;
            case 'error':
                container.classList.add('error-status');
                break;
            case 'info':
                container.classList.add('info-status');
                break;
            case 'warning':
                container.classList.add('warning-status');
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
