/**
 * Georgensen Courier - Contact Form Handler
 * Manages contact form submission, validation, and response handling
 * Supports department routing for customs, international freight, claims, etc.
 */

class GeorgjensenContactSystem {
    constructor() {
        this.form = document.getElementById('contactForm');
        this.messageContainer = document.getElementById('formMessage');
        this.apiEndpoint = '/api/contacts';
        this.init();
    }

    init() {
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleContactSubmit(e));
            this.setupDepartmentRouting();
        }
    }

    /**
     * Configure department-specific routing and handling
     */
    setupDepartmentRouting() {
        const subjectSelect = document.getElementById('contactSubject');
        if (subjectSelect) {
            subjectSelect.addEventListener('change', (e) => {
                this.updateContactInfo(e.target.value);
            });
        }
    }

    /**
     * Update contact info based on selected department
     */
    updateContactInfo(department) {
        const urgentDepartments = ['customs_clearance', 'tracking', 'claims_insurance'];
        
        if (urgentDepartments.includes(department)) {
            console.log(`⚡ Urgent department selected: ${department}`);
            // Could highlight international phone or add urgency badge
        }
    }

    /**
     * Handle form submission
     */
    async handleContactSubmit(e) {
        e.preventDefault();

        // Validate form
        if (!this.validateForm()) {
            this.showMessage('Please fill in all required fields.', 'warning');
            return;
        }

        // Gather form data
        const formData = this.gatherFormData();

        // Show loading state
        const submitBtn = this.form.querySelector('button[type="submit"]');
        const originalButtonText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 8px;"></i>Sending...';

        try {
            // Submit to backend
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                if (response.status === 400) {
                    throw new Error('Invalid form data. Please check and try again.');
                } else if (response.status === 429) {
                    throw new Error('Too many requests. Please wait a moment and try again.');
                } else if (response.status >= 500) {
                    throw new Error('Server error. Please try again later.');
                } else {
                    throw new Error('Failed to send message. Please try again.');
                }
            }

            // Success response
            const data = await response.json();
            this.showMessage(
                `✓ Thank you! We received your message. We'll respond within 2-4 hours during business hours.`,
                'success'
            );
            this.form.reset();

            // Log for analytics
            console.log('Contact message sent successfully:', {
                department: formData.subject,
                timestamp: new Date().toISOString()
            });

        } catch (error) {
            console.error('Contact form error:', error);
            this.showMessage(
                `Error: ${error.message || 'Failed to send message. Please try again.'}`,
                'danger'
            );
        } finally {
            // Restore button state
            submitBtn.disabled = false;
            submitBtn.textContent = originalButtonText;
        }
    }

    /**
     * Validate form before submission
     */
    validateForm() {
        const name = document.getElementById('contactName').value.trim();
        const email = document.getElementById('contactEmail').value.trim();
        const subject = document.getElementById('contactSubject').value.trim();
        const message = document.getElementById('contactMessage').value.trim();
        const agree = document.getElementById('contactAgree').checked;

        if (!name || !email || !subject || !message || !agree) {
            return false;
        }

        // Validate email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return false;
        }

        return true;
    }

    /**
     * Gather form data for submission
     */
    gatherFormData() {
        return {
            name: document.getElementById('contactName').value.trim(),
            email: document.getElementById('contactEmail').value.trim(),
            phone: document.getElementById('contactPhone').value.trim() || null,
            company: document.getElementById('contactCompany').value.trim() || null,
            subject: document.getElementById('contactSubject').value.trim(),
            message: document.getElementById('contactMessage').value.trim(),
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Display message to user
     */
    showMessage(message, type = 'info') {
        const messageDiv = document.getElementById('formMessage');
        if (!messageDiv) return;

        const alertClass = `alert alert-${type} alert-dismissible fade show`;
        messageDiv.className = alertClass;
        messageDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        messageDiv.style.display = 'block';

        // Auto-dismiss non-error messages after 6 seconds
        if (type !== 'danger') {
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 6000);
        }

        // Scroll to message
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    new GeorgjensenContactSystem();
});
