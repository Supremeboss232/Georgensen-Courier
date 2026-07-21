/**
 * Georgensen Courier - Real-time Tracking System
 * Supports global shipments with customs tracking, timezone localization, and bilingual status
 */

class GeorgjensenTrackingSystem {
    constructor() {
        this.currentTracker = null;
        this.currentLanguage = localStorage.getItem('appLanguage') || 'en';
        this.currentTrackingData = null;
        
        // Timezone database for major hubs
        this.timezones = {
            'CA': 'EST', // Canada - Eastern
            'ON': 'EST', 'QC': 'EST', 'MB': 'CST', 'AB': 'MST', 'BC': 'PST',
            'US': 'EST', // USA - varies
            'NY': 'EST', 'IL': 'CST', 'TX': 'CST', 'CA': 'PST', 'WA': 'PST',
            'GB': 'GMT', 'UK': 'GMT',
            'DE': 'CET', 'EU': 'CET',
            'SG': 'SGT', 'HK': 'HKT', 'AU': 'AEST'
        };
        
        // Country flag mapping
        this.countryFlags = {
            'CA': '🇨🇦', 'US': '🇺🇸', 'GB': '🇬🇧', 'DE': '🇩🇪',
            'FR': '🇫🇷', 'SG': '🇸🇬', 'HK': '🇭🇰', 'AU': '🇦🇺',
            'JP': '🇯🇵', 'CN': '🇨🇳', 'MX': '🇲🇽', 'BR': '🇧🇷'
        };
        
        // Status translations
        this.statusTranslations = {
            'en': {
                'order_received': 'Order Received',
                'processing': 'Processing',
                'picked_up': 'Picked Up',
                'in_transit': 'In Transit',
                'in_customs': 'In Customs',
                'cleared_customs': 'Customs Cleared',
                'duties_pending': 'Duties Pending',
                'release_pending': 'Release Pending',
                'out_for_delivery': 'Out for Delivery',
                'delivered': 'Delivered',
                'failed_delivery': 'Delivery Failed',
                'cancelled': 'Cancelled',
                'pending': 'Pending'
            },
            'fr': {
                'order_received': 'Commande Reçue',
                'processing': 'Traitement',
                'picked_up': 'En Attente',
                'in_transit': 'En Transit',
                'in_customs': 'En Douane',
                'cleared_customs': 'Douane Dédouanée',
                'duties_pending': 'Droits en Attente',
                'release_pending': 'Libération en Attente',
                'out_for_delivery': 'Livraison en Cours',
                'delivered': 'Livré',
                'failed_delivery': 'Livraison Échouée',
                'cancelled': 'Annulé',
                'pending': 'En Attente'
            }
        };
        
        this.init();
    }

    init() {
        // Bind form submission
        const form = document.getElementById('trackingForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleTrackingSubmit(e));
        }

        // Focus on input
        const input = document.getElementById('trackingInput');
        if (input) {
            input.focus();
        }

        // Listen for language changes
        window.addEventListener('languageChanged', (e) => {
            this.currentLanguage = e.detail.language;
            if (this.currentTrackingData) {
                this.refreshTrackingDisplay();
            }
        });
    }

    /**
     * Handle form submission and validate tracking ID
     */
    async handleTrackingSubmit(event) {
        event.preventDefault();
        
        const trackingNum = document.getElementById('trackingInput').value.trim().toUpperCase();
        
        if (!trackingNum) return;

        // Validate tracking number format: GJ-CC-XXXXXXXX
        if (!this.validateTrackingNumber(trackingNum)) {
            alert('Invalid tracking number format. Expected: GJ-CC-XXXXXXXX (e.g., GJ-CA-TRK001234)');
            return;
        }

        // Close previous tracker
        if (this.currentTracker) {
            this.currentTracker.disconnect();
        }

        // Show display section
        document.getElementById('trackingDisplay').style.display = 'block';
        
        // Update display
        document.getElementById('displayTrackingNum').textContent = trackingNum;
        document.getElementById('displayStatus').innerHTML = '<span class="status-badge" style="background: #e2e3e5; color: #383d41;">Loading...</span>';
        document.getElementById('trackingHistory').innerHTML = '<p class="text-muted text-center">Connecting to live tracking...</p>';

        try {
            // Fetch initial status
            const response = await fetch(`/api/v1/tracking/${trackingNum}`);
            const data = await response.json();

            if (response.ok) {
                this.currentTrackingData = data;
                
                // Update initial display
                document.getElementById('displayPickup').textContent = data.pickup_address || '-';
                document.getElementById('displayDelivery').textContent = data.delivery_address || '-';
                
                // Update service level
                document.getElementById('displayServiceLevel').textContent = 
                    this.getServiceLevelDisplay(data.service_type) || '-';
                
                // Update estimated delivery
                document.getElementById('displayEstimatedDelivery').textContent = 
                    data.estimated_delivery ? this.formatDate(data.estimated_delivery) : '-';
                
                // Show customs section if international
                this.handleCustomsDisplay(data);
                
                // Display initial history
                if (data.raw_history && data.raw_history.length > 0) {
                    document.getElementById('trackingHistory').innerHTML = '';
                    data.raw_history.forEach(update => {
                        this.displayTrackingUpdate(update);
                    });
                } else {
                    document.getElementById('trackingHistory').innerHTML = '<p class="text-muted text-center">No updates yet...</p>';
                }

                // Initialize real-time tracking
                const tracker = new TrackingClient(trackingNum);
                
                tracker.on('onConnected', () => {
                    this.updateConnectionIndicator(true);
                    console.log('✓ Real-time tracking connected');
                });
                
                tracker.on('onUpdate', (data) => {
                    if (data.event === 'location_update') {
                        this.updateTrackingDisplay(data);
                    } else if (data.status) {
                        this.updateTrackingDisplay(data);
                    }
                });
                
                tracker.on('onDisconnected', () => {
                    this.updateConnectionIndicator(false);
                });
                
                tracker.on('onError', () => {
                    this.updateConnectionIndicator(false);
                });
                
                tracker.connect();
                this.currentTracker = tracker;

            } else {
                document.getElementById('displayStatus').innerHTML = '<span class="status-badge" style="background: #f8d7da; color: #721c24;">Not found</span>';
                document.getElementById('trackingHistory').innerHTML = '<p class="text-danger text-center">Tracking number not found</p>';
            }
        } catch (error) {
            console.error('Error fetching tracking data:', error);
            document.getElementById('trackingHistory').innerHTML = `<p class="text-danger text-center">Error: ${error.message}</p>`;
        }
    }

    /**
     * Validate tracking number format: GJ-CC-XXXXXXXX
     */
    validateTrackingNumber(trackingNum) {
        const pattern = /^GJ-[A-Z]{2}-[A-Z0-9]{6,}$/;
        return pattern.test(trackingNum);
    }

    /**
     * Get human-readable service level display
     */
    getServiceLevelDisplay(serviceType) {
        const serviceMap = {
            'zone_1': 'Same-Day Courier',
            'zone_2': 'Regional (2-3 days)',
            'zone_3': 'Continental (3-5 days)',
            'zone_4': 'Global Express Air',
            'zone_5': 'Ocean Freight',
            'economy': 'Economy (5-7 days)',
            'standard': 'Standard (2-3 days)',
            'express': 'Express (24 hours)',
            'overnight': 'Overnight'
        };
        return serviceMap[serviceType] || serviceType;
    }

    /**
     * Handle customs display for international shipments
     */
    handleCustomsDisplay(data) {
        const isInternational = data.origin_country && data.destination_country && 
                               data.origin_country !== data.destination_country;
        
        const customsSection = document.getElementById('customsStatusSection');
        
        if (isInternational && customsSection) {
            customsSection.style.display = 'block';
            
            // Update customs status based on data
            const customsStatus = data.customs_status || 'pending';
            const customsEl = document.getElementById('displayCustomsStatus');
            
            if (customsEl) {
                const statusColor = this.getCustomsStatusColor(customsStatus);
                const statusText = this.getTranslatedText(customsStatus);
                customsEl.innerHTML = `<span class="status-badge" style="background: ${statusColor}; color: white;">${statusText}</span>`;
            }
            
            // Update clearance info
            const clearanceInfo = document.getElementById('displayClearanceInfo');
            if (clearanceInfo && data.estimated_clearance_date) {
                clearanceInfo.textContent = `Estimated clearance: ${this.formatDate(data.estimated_clearance_date)}`;
            }
            
            // Update customs fee if present
            const customsFeeEl = document.getElementById('displayCustomsFee');
            if (customsFeeEl && data.customs_fee) {
                customsFeeEl.textContent = `Customs fee: $${data.customs_fee} CAD`;
            }
        } else if (customsSection) {
            customsSection.style.display = 'none';
        }
    }

    /**
     * Get color for customs status
     */
    getCustomsStatusColor(status) {
        const colors = {
            'pending': '#fff3cd',
            'in_customs': '#cfe2ff',
            'cleared_customs': '#d1e7dd',
            'duties_pending': '#f8d7da',
            'release_pending': '#fff3cd'
        };
        return colors[status] || '#e2e3e5';
    }

    /**
     * Get country code from location data
     */
    getCountryCodeFromLocation(location, data) {
        if (data && data.country_code) {
            return data.country_code;
        }
        // Try to extract from location string
        if (location && location.includes(',')) {
            const parts = location.split(',');
            const countryPart = parts[parts.length - 1].trim().toUpperCase();
            return countryPart.length === 2 ? countryPart : null;
        }
        return null;
    }

    /**
     * Get timezone for location
     */
    getTimezoneForLocation(countryCode) {
        return this.timezones[countryCode] || 'UTC';
    }

    /**
     * Get flag emoji for country
     */
    getFlagEmoji(countryCode) {
        return this.countryFlags[countryCode] || '📍';
    }

    /**
     * Update tracking display with new data
     */
    updateTrackingDisplay(data) {
        // Update status with translated text
        const statusKey = data.status || 'pending';
        const statusText = this.getTranslatedText(statusKey);
        const statusColor = this.getStatusColor(statusKey);
        document.getElementById('displayStatus').innerHTML = 
            `<span class="status-badge" style="background: var(--bs-${statusColor}) !important; color: white;" data-status-en="${statusKey}" data-status-fr="${statusKey}">${statusText}</span>`;
        
        // Update location with timezone and flag
        if (data.location) {
            const countryCode = this.getCountryCodeFromLocation(data.location, data);
            const timezone = this.getTimezoneForLocation(countryCode);
            const flagEmoji = this.getFlagEmoji(countryCode);
            
            document.getElementById('displayLocation').textContent = 
                `${flagEmoji} ${data.location}`;
            
            const tzElement = document.getElementById('displayLocationTimezone');
            if (tzElement) {
                tzElement.textContent = `Local time: ${timezone}`;
            }
        }
        
        // Update time
        if (data.timestamp) {
            const time = new Date(data.timestamp).toLocaleTimeString();
            document.getElementById('displayTime').textContent = time;
        }
        
        // Add to history
        this.displayTrackingUpdate(data);
    }

    /**
     * Refresh display with current language
     */
    refreshTrackingDisplay() {
        if (!this.currentTrackingData) return;

        // Re-render all status elements with translated text
        const statusElements = document.querySelectorAll('[data-status-en]');
        statusElements.forEach(el => {
            const statusKey = el.getAttribute('data-status-en');
            const statusText = this.getTranslatedText(statusKey);
            el.textContent = statusText;
        });
    }

    /**
     * Get translated text for status
     */
    getTranslatedText(statusKey) {
        const translations = this.statusTranslations[this.currentLanguage] || this.statusTranslations['en'];
        return translations[statusKey] || statusKey.replace(/_/g, ' ');
    }

    /**
     * Update connection status indicator
     */
    updateConnectionIndicator(isConnected) {
        const indicator = document.getElementById('connectionIndicator');
        const badgeEl = document.getElementById('connectionStatus');
        
        if (isConnected) {
            indicator.className = 'connection-indicator connected';
            indicator.innerHTML = '<i class="fas fa-circle" style="font-size: 8px; color: #28a745;"></i> Live';
            if (badgeEl) {
                badgeEl.className = 'badge badge-success';
                badgeEl.textContent = 'Live Tracking';
            }
        } else {
            indicator.className = 'connection-indicator disconnected';
            indicator.innerHTML = '<i class="fas fa-circle-notch" style="font-size: 8px; animation: spin 1s linear infinite;"></i> Reconnecting';
            if (badgeEl) {
                badgeEl.className = 'badge badge-warning';
                badgeEl.textContent = 'Reconnecting...';
            }
        }
    }

    /**
     * Map status to Bootstrap color
     */
    getStatusColor(status) {
        const colors = {
            'pending': 'secondary',
            'order_received': 'secondary',
            'processing': 'info',
            'picked_up': 'primary',
            'in_transit': 'info',
            'in_customs': 'warning',
            'cleared_customs': 'success',
            'duties_pending': 'danger',
            'release_pending': 'warning',
            'out_for_delivery': 'warning',
            'delivered': 'success',
            'failed_delivery': 'danger',
            'cancelled': 'dark'
        };
        return colors[status] || 'secondary';
    }

    /**
     * Get hex color for status
     */
    getStatusColorHex(status) {
        const colors = {
            'pending': '#6c757d',
            'order_received': '#6c757d',
            'processing': '#17a2b8',
            'picked_up': '#007bff',
            'in_transit': '#17a2b8',
            'in_customs': '#ffc107',
            'cleared_customs': '#28a745',
            'duties_pending': '#dc3545',
            'release_pending': '#ffc107',
            'out_for_delivery': '#ffc107',
            'delivered': '#28a745',
            'failed_delivery': '#dc3545',
            'cancelled': '#343a40'
        };
        return colors[status] || '#6c757d';
    }

    /**
     * Display tracking update in timeline
     */
    displayTrackingUpdate(data) {
        const historyEl = document.getElementById('trackingHistory');
        
        // Clear "no updates" message if this is first update
        if (historyEl.querySelector('.text-muted')) {
            historyEl.innerHTML = '';
        }
        
        const time = new Date(data.timestamp || data.created_at).toLocaleTimeString();
        const statusColor = this.getStatusColorHex(data.status);
        const statusText = this.getTranslatedText(data.status);
        
        // Get country code and flag
        const countryCode = this.getCountryCodeFromLocation(data.location, data);
        const flagEmoji = this.getFlagEmoji(countryCode);
        const timezone = this.getTimezoneForLocation(countryCode);
        
        const item = document.createElement('div');
        item.className = 'timeline-item';
        
        let locationHtml = '';
        if (data.location) {
            locationHtml = `<p class="timeline-location"><i class="fas fa-map-marker-alt"></i> <strong>${flagEmoji} ${data.location}</strong><br><small class="text-muted">Local time: ${timezone}</small></p>`;
        }
        
        let notesHtml = '';
        if (data.notes) {
            notesHtml = `<p class="timeline-notes"><em>${data.notes}</em></p>`;
        }
        
        item.innerHTML = `
            <div class="timeline-marker" style="background: ${statusColor};"></div>
            <div class="timeline-content">
                <div class="timeline-header">
                    <strong style="text-transform: capitalize;" data-status-en="${data.status}" data-status-fr="${data.status}">${statusText}</strong>
                    <span class="text-muted" style="font-size: 12px;">${time}</span>
                </div>
                ${locationHtml}
                ${notesHtml}
            </div>
        `;
        
        historyEl.insertBefore(item, historyEl.firstChild);
        
        // Limit to 20 items
        while (historyEl.children.length > 20) {
            historyEl.removeChild(historyEl.lastChild);
        }
    }

    /**
     * Format date for display
     */
    formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-CA', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch {
            return dateString;
        }
    }
}

// Initialize tracking system when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.trackingSystem = new GeorgjensenTrackingSystem();
    });
} else {
    window.trackingSystem = new GeorgjensenTrackingSystem();
}

// Global functions for backward compatibility
function handleTrackingSubmit(event) {
    if (window.trackingSystem) {
        window.trackingSystem.handleTrackingSubmit(event);
    }
}

function updateConnectionIndicator(isConnected) {
    if (window.trackingSystem) {
        window.trackingSystem.updateConnectionIndicator(isConnected);
    }
}

function displayTrackingUpdate(data) {
    if (window.trackingSystem) {
        window.trackingSystem.displayTrackingUpdate(data);
    }
}

function updateTrackingDisplay(data) {
    if (window.trackingSystem) {
        window.trackingSystem.updateTrackingDisplay(data);
    }
}

function getStatusColor(status) {
    if (window.trackingSystem) {
        return window.trackingSystem.getStatusColor(status);
    }
    return 'secondary';
}

function getStatusColorHex(status) {
    if (window.trackingSystem) {
        return window.trackingSystem.getStatusColorHex(status);
    }
    return '#6c757d';
}

document.addEventListener('DOMContentLoaded', initPublicTracking);
