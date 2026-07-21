/**
 * Real-time Tracking WebSocket Client
 * Connects to tracking updates and displays them in real-time
 */

class TrackingClient {
    constructor(trackingNumber) {
        this.trackingNumber = trackingNumber;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000; // 3 seconds
        this.listeners = {
            onUpdate: null,
            onConnected: null,
            onDiscnnected: null,
            onError: null
        };
    }

    /**
     * Connect to the tracking WebSocket
     */
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/v1/tracking/ws/${this.trackingNumber}`;
        
        console.log(`🔌 Connecting to tracking: ${wsUrl}`);
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log(`✓ Connected to tracking: ${this.trackingNumber}`);
                this.reconnectAttempts = 0;
                if (this.listeners.onConnected) {
                    this.listeners.onConnected();
                }
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log(`📍 Tracking update:`, data);
                
                if (this.listeners.onUpdate) {
                    this.listeners.onUpdate(data);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error(`✗ WebSocket error:`, error);
                if (this.listeners.onError) {
                    this.listeners.onError(error);
                }
            };
            
            this.ws.onclose = () => {
                console.log(`✗ Disconnected from tracking: ${this.trackingNumber}`);
                if (this.listeners.onDiscnnected) {
                    this.listeners.onDiscnnected();
                }
                
                // Attempt reconnect
                this.attemptReconnect();
            };
        } catch (error) {
            console.error(`✗ Error creating WebSocket:`, error);
            this.attemptReconnect();
        }
    }

    /**
     * Attempt to reconnect with exponential backoff
     */
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            console.log(`⏳ Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error(`✗ Failed to reconnect after ${this.maxReconnectAttempts} attempts`);
        }
    }

    /**
     * Disconnect from tracking
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    /**
     * Register a callback for updates
     */
    on(event, callback) {
        if (event in this.listeners) {
            this.listeners[event] = callback;
        }
    }

    /**
     * Send a message to the server (for future use)
     */
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    /**
     * Get connection status
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// ==================== Visualization Functions ====================

/**
 * Update tracking display with real-time data
 */
function displayTrackingUpdate(data) {
    const container = document.getElementById('tracking-status');
    if (!container) return;

    // Update status badge
    const statusEl = container.querySelector('[data-field="status"]');
    if (statusEl) {
        statusEl.textContent = data.status || 'Unknown';
        statusEl.className = `badge badge-${getStatusColor(data.status)}`;
    }

    // Update location
    const locationEl = container.querySelector('[data-field="location"]');
    if (locationEl) {
        locationEl.textContent = data.location || `${data.latitude}, ${data.longitude}`;
    }

    // Update timestamp
    const timeEl = container.querySelector('[data-field="timestamp"]');
    if (timeEl) {
        const time = new Date(data.timestamp).toLocaleTimeString();
        timeEl.textContent = time;
    }

    // Add to history
    addToTrackingHistory(data);

    // Update map if available
    if (typeof updateMapLocation === 'function') {
        updateMapLocation(data.latitude, data.longitude, data.location);
    }
}

/**
 * Get Bootstrap color for status
 */
function getStatusColor(status) {
    const colors = {
        'pending': 'secondary',
        'order_received': 'secondary',
        'processing': 'info',
        'picked_up': 'primary',
        'in_transit': 'info',
        'out_for_delivery': 'warning',
        'delivered': 'success',
        'failed_delivery': 'danger',
        'cancelled': 'dark'
    };
    return colors[status] || 'secondary';
}

/**
 * Add update to tracking history timeline
 */
function addToTrackingHistory(data) {
    const historyContainer = document.getElementById('tracking-history');
    if (!historyContainer) return;

    const historyItem = document.createElement('div');
    historyItem.className = 'timeline-item';
    
    const time = new Date(data.timestamp).toLocaleTimeString();
    const statusBadge = `<span class="badge badge-${getStatusColor(data.status)}">${data.status}</span>`;
    
    historyItem.innerHTML = `
        <div class="timeline-marker" style="background: ${getStatusColorHex(data.status)}"></div>
        <div class="timeline-content">
            <div class="timeline-header">
                <strong>${data.status}</strong>
                <span class="text-muted">${time}</span>
            </div>
            ${data.location ? `<p class="timeline-location"><strong>📍</strong> ${data.location}</p>` : ''}
            ${data.notes ? `<p class="timeline-notes"><em>${data.notes}</em></p>` : ''}
        </div>
    `;
    
    // Add to beginning of history
    historyContainer.insertBefore(historyItem, historyContainer.firstChild);
    
    // Limit history to last 20 items
    while (historyContainer.children.length > 20) {
        historyContainer.removeChild(historyContainer.lastChild);
    }
}

/**
 * Get hex color for status (for visual timeline)
 */
function getStatusColorHex(status) {
    const colors = {
        'pending': '#6c757d',
        'order_received': '#6c757d',
        'processing': '#17a2b8',
        'picked_up': '#007bff',
        'in_transit': '#17a2b8',
        'out_for_delivery': '#ffc107',
        'delivered': '#28a745',
        'failed_delivery': '#dc3545',
        'cancelled': '#343a40'
    };
    return colors[status] || '#6c757d';
}

/**
 * Initialize tracking on page load
 */
function initializeTracking(trackingNumber) {
    const client = new TrackingClient(trackingNumber);
    
    // Register callbacks
    client.on('onConnected', () => {
        console.log('✓ Real-time tracking connected');
        const indicator = document.getElementById('connection-status');
        if (indicator) {
            indicator.className = 'badge badge-success';
            indicator.textContent = 'Live Tracking';
        }
    });
    
    client.on('onUpdate', (data) => {
        console.log('📍 Update received:', data);
        displayTrackingUpdate(data);
    });
    
    client.on('onDiscnnected', () => {
        console.log('✗ Tracking disconnected');
        const indicator = document.getElementById('connection-status');
        if (indicator) {
            indicator.className = 'badge badge-warning';
            indicator.textContent = 'Reconnecting...';
        }
    });
    
    client.on('onError', (error) => {
        console.error('✗ Tracking error:', error);
        const indicator = document.getElementById('connection-status');
        if (indicator) {
            indicator.className = 'badge badge-danger';
            indicator.textContent = 'Connection Error';
        }
    });
    
    // Connect
    client.connect();
    
    // Return client for external access
    window._trackingClient = client;
    return client;
}

// ==================== Sample Usage ====================
/*
// Example 1: Basic usage
const client = new TrackingClient('GEO-26-ABC123');
client.on('onUpdate', (data) => {
    console.log(`📍 Shipment at: ${data.location}`);
    console.log(`Status: ${data.status}`);
    console.log(`Coordinates: ${data.latitude}, ${data.longitude}`);
});
client.connect();

// Example 2: HTML page with tracking display
document.addEventListener('DOMContentLoaded', () => {
    const tracking = document.querySelector('[data-tracking-number]');
    if (tracking) {
        const trackingNumber = tracking.getAttribute('data-tracking-number');
        initializeTracking(trackingNumber);
    }
});
*/

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TrackingClient, initializeTracking };
}
