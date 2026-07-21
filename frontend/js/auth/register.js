// Auth section JS files
// register.js - Registration handler with partner-specific field logic

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is already authenticated
    // guards.js provides the redirectIfAuthenticated() function
    if (typeof redirectIfAuthenticated === 'function') {
        redirectIfAuthenticated();
    }
    
    const form = document.getElementById('registerForm');
    if (form) {
        form.addEventListener('submit', handleRegister);
    }
});

/**
 * Main registration handler
 * Processes form data based on account type and sends to backend
 */
async function handleRegister(e) {
    e.preventDefault();
    
    // Get form values
    const fullName = document.getElementById('fullName')?.value?.trim();
    const email = document.getElementById('email')?.value?.trim();
    const phone = document.getElementById('phone')?.value?.trim();
    const password = document.getElementById('password')?.value;
    const confirmPassword = document.getElementById('confirmPassword')?.value;
    const accountType = document.getElementById('accountType')?.value;
    
    // Get references to UI elements
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    const submitBtn = document.getElementById('submitBtn');
    const submitText = document.getElementById('submitText');
    const submitSpinner = document.getElementById('submitSpinner');
    
    // Clear previous error messages
    if (errorMessage) {
        errorMessage.classList.remove('show');
    }
    
    // ============ VALIDATION ============
    
    // Basic validation
    if (!fullName || !email || !password || !confirmPassword || !accountType) {
        showError('Please fill in all required fields', errorMessage, errorText);
        return;
    }
    
    // Email validation
    if (!isValidEmail(email)) {
        showError('Please enter a valid email address', errorMessage, errorText);
        return;
    }
    
    // Password validation
    if (password.length < 8) {
        showError('Password must be at least 8 characters long', errorMessage, errorText);
        return;
    }
    
    if (password !== confirmPassword) {
        showError('Passwords do not match', errorMessage, errorText);
        return;
    }
    
    // Account type validation
    if (!['customer', 'partner'].includes(accountType)) {
        showError('Invalid account type selected', errorMessage, errorText);
        return;
    }
    
    // Partner-specific validation
    let partnerData = null;
    if (accountType === 'partner') {
        partnerData = validatePartnerFields();
        if (!partnerData) {
            showError('Please fill in all required Delivery Partner information', errorMessage, errorText);
            return;
        }
    }
    
    // ============ SUBMISSION ============
    
    // Show loading state
    if (submitBtn && submitText && submitSpinner) {
        submitBtn.disabled = true;
        submitText.style.display = 'none';
        submitSpinner.style.display = 'inline';
    }
    
    try {
        // Build registration payload
        const registrationData = {
            full_name: fullName,
            email: email,
            phone: phone || null,
            password: password,
            role: accountType
        };
        
        // Add partner profile data if applicable
        if (accountType === 'partner' && partnerData) {
            registrationData.profile = {
                vehicle_type: partnerData.vehicleType,
                license_number: partnerData.licenseNumber,
                license_category: partnerData.licenseCategory,
                plate_number: partnerData.plateNumber
            };
        }
        
        // Send registration request to backend
        const response = await post('/auth/register', registrationData);
        
        // Success handling
        if (response && response.access_token) {
            // Store authentication data
            if (typeof setAuthToken === 'function') {
                setAuthToken(response.access_token);
            }
            if (typeof setUser === 'function') {
                setUser(response.user || { role: accountType });
            }
            
            // Store refresh token if available
            if (response.refresh_token) {
                localStorage.setItem('refresh_token', response.refresh_token);
            }
            
            // Show success message
            const successMessage = document.getElementById('successMessage');
            const successText = document.getElementById('successText');
            if (successMessage && successText) {
                successText.textContent = 'Account created successfully! Redirecting to dashboard...';
                successMessage.classList.add('show');
            }
            
            // Redirect based on account type
            setTimeout(() => {
                if (accountType === 'partner') {
                    window.location.href = '/partner/dashboard';
                } else {
                    window.location.href = '/customer/dashboard';
                }
            }, 1500);
        } else {
            showError('Unexpected response from server', errorMessage, errorText);
        }
    } catch (error) {
        // Error handling
        let errorMsg = 'Registration failed: ';
        
        if (error.response && error.response.status === 400) {
            errorMsg += 'Email already registered';
        } else if (error.message) {
            errorMsg += error.message;
        } else {
            errorMsg += 'Please try again';
        }
        
        showError(errorMsg, errorMessage, errorText);
        
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
 * Validate and retrieve partner-specific fields
 */
function validatePartnerFields() {
    const licenseNumber = document.getElementById('licenseNumber')?.value?.trim();
    const licenseCategory = document.getElementById('licenseCategory')?.value;
    const vehicleType = document.getElementById('vehicleType')?.value;
    const plateNumber = document.getElementById('plateNumber')?.value?.trim();
    
    // Check if all required partner fields are filled
    if (!licenseNumber || !licenseCategory || !vehicleType || !plateNumber) {
        return null;
    }
    
    return {
        licenseNumber,
        licenseCategory,
        vehicleType,
        plateNumber
    };
}

/**
 * Display error message
 */
function showError(message, errorContainer, errorText) {
    if (errorContainer && errorText) {
        errorText.textContent = message;
        errorContainer.classList.add('show');
        
        // Scroll to error message
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}
