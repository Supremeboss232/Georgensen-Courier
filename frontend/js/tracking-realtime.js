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
        this.reconnectDelay = 3000;
        this.listeners = {
            onUpdate: null,
            onConnected: null,
            onDisconnected: null,
            onDiscnnected: null,
            onError: null
        };
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/v1/tracking/ws/${this.trackingNumber}`;
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.reconnectAttempts = 0;
                if (this.listeners.onConnected) {
                    this.listeners.onConnected();
                }
            };
            
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (this.listeners.onUpdate) {
                    this.listeners.onUpdate(data);
                }
            };
            
            this.ws.onerror = (error) => {
                if (this.listeners.onError) {
                    this.listeners.onError(error);
                }
            };
            
            this.ws.onclose = () => {
                if (this.listeners.onDisconnected) {
                    this.listeners.onDisconnected();
                }
                if (this.listeners.onDiscnnected) {
                    this.listeners.onDiscnnected();
                }
                this.attemptReconnect();
            };
        } catch (error) {
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            setTimeout(() => {
                this.connect();
            }, delay);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    on(event, callback) {
        if (event in this.listeners) {
            this.listeners[event] = callback;
        }
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

function displayTrackingUpdate(data) {
    const container = document.getElementById('tracking-status');
    if (!container) return;

    const statusEl = container.querySelector('[data-field="status"]');
    if (statusEl) {
        statusEl.textContent = data.status || 'Unknown';
        statusEl.className = `badge badge-${getStatusColor(data.status)}`;
    }

    const locationEl = container.querySelector('[data-field="location"]');
    if (locationEl) {
        locationEl.textContent = data.location || `${data.latitude}, ${data.longitude}`;
    }

    const timeEl = container.querySelector('[data-field="timestamp"]');
    if (timeEl) {
        const time = new Date(data.timestamp).toLocaleTimeString();
        timeEl.textContent = time;
    }

    addToTrackingHistory(data);

    if (typeof updateMapLocation === 'function') {
        updateMapLocation(data.latitude, data.longitude, data.location);
    }
}

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

function addToTrackingHistory(data) {
    const historyContainer = document.getElementById('tracking-history');
    if (!historyContainer) return;

    const historyItem = document.createElement('div');
    historyItem.className = 'timeline-item';
    
    const time = new Date(data.timestamp).toLocaleTimeString();
    
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
    
    historyContainer.insertBefore(historyItem, historyContainer.firstChild);
    
    while (historyContainer.children.length > 20) {
        historyContainer.removeChild(historyContainer.lastChild);
    }
}

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

function initializeTracking(trackingNumber) {
    const client = new TrackingClient(trackingNumber);
    
    client.on('onConnected', () => {
        const indicator = document.getElementById('connection-status');
        if (indicator) {
            indicator.className = 'badge badge-success';
            indicator.textContent = 'Live Tracking';
        }
    });
    
    client.on('onUpdate', (data) => {
        displayTrackingUpdate(data);
    });
    
    client.on('onDisconnected', () => {
        const indicator = document.getElementById('connection-status');
        if (indicator) {
            indicator.className = 'badge badge-warning';
            indicator.textContent = 'Reconnecting...';
        }
    });
    
    client.on('onError', () => {
        const indicator = document.getElementById('connection-status');
        if (indicator) {
            indicator.className = 'badge badge-danger';
            indicator.textContent = 'Connection Error';
        }
    });
    
    client.connect();
    window._trackingClient = client;
    return client;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TrackingClient, initializeTracking };
}
