// TRACKING.JS - Real-time tracking module with WebSocket support

// ============================================================================
// WEBSOCKET REAL-TIME TRACKING CLASS
// ============================================================================

class RealTimeTracking {
  constructor(options = {}) {
    this.wsUrl = options.wsUrl || 'wss://api.georgensen.com/ws/tracking';
    this.reconnectInterval = options.reconnectInterval || 5000;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
    this.reconnectAttempts = 0;
    this.ws = null;
    this.activeTracking = new Map();
    this.subscribers = new Map();
    this.initialized = false;
    
    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.handleMessage = this.handleMessage.bind(this);
    this.handleError = this.handleError.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }
  
  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return;
    }
    
    try {
      this.ws = new WebSocket(this.wsUrl);
      
      this.ws.onopen = () => {
        console.log('Connected to real-time tracking server');
        this.reconnectAttempts = 0;
        this.initialized = true;
        this.emit('connected');
        
        this.activeTracking.forEach((trackingData, orderId) => {
          this.subscribeToTracking(orderId);
        });
      };
      
      this.ws.onmessage = this.handleMessage;
      this.ws.onerror = this.handleError;
      this.ws.onclose = this.handleClose;
      
    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.handleClose();
    }
  }
  
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      
      switch (data.type) {
        case 'tracking_update':
          this.handleTrackingUpdate(data);
          break;
        case 'status_update':
          this.handleStatusUpdate(data);
          break;
        case 'eta_update':
          this.handleETAUpdate(data);
          break;
        case 'notification':
          this.handleNotification(data);
          break;
        case 'error':
          this.handleServerError(data);
          break;
      }
    } catch (error) {
      console.error('Error parsing tracking message:', error);
    }
  }
  
  handleTrackingUpdate(data) {
    const { orderId, latitude, longitude, timestamp, accuracy } = data;
    
    const trackingData = this.activeTracking.get(orderId) || {
      orderId,
      coordinates: [],
      currentLocation: null,
      history: []
    };
    
    trackingData.currentLocation = {
      lat: latitude,
      lng: longitude,
      timestamp,
      accuracy
    };
    
    trackingData.coordinates.push({ lat: latitude, lng: longitude });
    
    if (trackingData.coordinates.length > 100) {
      trackingData.coordinates.shift();
    }
    
    this.activeTracking.set(orderId, trackingData);
    this.emit(`tracking:${orderId}`, trackingData);
  }
  
  handleStatusUpdate(data) {
    const { orderId, status, timestamp, partnerId, message } = data;
    
    const trackingData = this.activeTracking.get(orderId) || {};
    trackingData.status = status;
    trackingData.lastStatusUpdate = { status, timestamp, message };
    trackingData.partnerId = partnerId;
    
    this.activeTracking.set(orderId, trackingData);
    this.emit(`status:${orderId}`, { status, timestamp, message });
    
    displayTrackingUpdate({ orderId, status, message });
  }
  
  handleETAUpdate(data) {
    const { orderId, eta, distanceRemaining, distanceTraveled, progress } = data;
    
    const trackingData = this.activeTracking.get(orderId) || {};
    trackingData.eta = eta;
    trackingData.distance = {
      remaining: distanceRemaining,
      traveled: distanceTraveled,
      total: distanceTraveled + distanceRemaining
    };
    trackingData.progress = progress;
    
    this.activeTracking.set(orderId, trackingData);
    this.emit(`eta:${orderId}`, { eta, distance: trackingData.distance, progress });
  }
  
  handleNotification(data) {
    const { type, message, orderId, severity } = data;
    
    if (severity === 'urgent') {
      showNotification(`⚠️ ${message}`, 'warning');
    } else if (severity === 'error') {
      showNotification(`❌ ${message}`, 'error');
    } else {
      showNotification(message, 'info');
    }
    
    this.emit('notification', { type, message, orderId, severity });
  }
  
  handleServerError(data) {
    const { message, code } = data;
    console.error(`Server error [${code}]: ${message}`);
    showNotification(`Tracking error: ${message}`, 'error');
  }
  
  handleError(error) {
    console.error('WebSocket error:', error);
    this.emit('error', error);
  }
  
  handleClose() {
    console.log('Disconnected from tracking server');
    this.initialized = false;
    this.emit('disconnected');
    
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    }
  }
  
  subscribeToTracking(orderId) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }
    
    const message = {
      type: 'subscribe',
      orderId,
      timestamp: new Date().toISOString()
    };
    
    this.ws.send(JSON.stringify(message));
  }
  
  unsubscribeFromTracking(orderId) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }
    
    const message = {
      type: 'unsubscribe',
      orderId,
      timestamp: new Date().toISOString()
    };
    
    this.ws.send(JSON.stringify(message));
    this.activeTracking.delete(orderId);
  }
  
  getTrackingData(orderId) {
    return this.activeTracking.get(orderId) || null;
  }
  
  getAllTrackingData() {
    return Array.from(this.activeTracking.values());
  }
  
  calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLng / 2) * Math.sin(dLng / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }
  
  estimateETA(distanceKm, averageSpeedKmh = 40) {
    const hours = distanceKm / averageSpeedKmh;
    const minutes = Math.round(hours * 60);
    return new Date(Date.now() + minutes * 60 * 1000);
  }
  
  subscribe(eventName, callback) {
    if (!this.subscribers.has(eventName)) {
      this.subscribers.set(eventName, []);
    }
    this.subscribers.get(eventName).push(callback);
    
    return () => {
      const callbacks = this.subscribers.get(eventName);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    };
  }
  
  emit(eventName, data) {
    if (this.subscribers.has(eventName)) {
      this.subscribers.get(eventName).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in subscriber for ${eventName}:`, error);
        }
      });
    }
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.activeTracking.clear();
    this.initialized = false;
  }
}

// Global WebSocket tracking instance
let realTimeTrackingService = null;

function initializeRealTimeTracking(options = {}) {
  if (!realTimeTrackingService) {
    realTimeTrackingService = new RealTimeTracking(options);
    realTimeTrackingService.connect();
  }
  return realTimeTrackingService;
}

function getRealTimeTrackingService() {
  if (!realTimeTrackingService) {
    realTimeTrackingService = new RealTimeTracking();
    realTimeTrackingService.connect();
  }
  return realTimeTrackingService;
}

// ============================================================================
// POLLING-BASED TRACKING (Legacy - for backward compatibility)
// ============================================================================

/**
 * Fetch tracking information
 */
async function fetchTracking(trackingNumber) {
  try {
    const response = await apiCall(`/tracking/${trackingNumber}`);
    return response;
  } catch (error) {
    handleError(new Error(`Tracking number not found: ${trackingNumber}`));
    return null;
  }
}

/**
 * Start real-time tracking with polling
 */
function startLiveTracking(trackingNumber, updateInterval = 30000) {
  let pollInterval;
  
  const updateTracking = async () => {
    const data = await fetchTracking(trackingNumber);
    if (data) {
      displayTrackingUpdate(data);
      
      // Stop polling if delivered or cancelled
      if (['delivered', 'cancelled'].includes(data.status.toLowerCase())) {
        clearInterval(pollInterval);
        showNotification('Delivery completed', 'success');
      }
    }
  };
  
  // Initial fetch
  updateTracking();
  
  // Start polling
  pollInterval = setInterval(updateTracking, updateInterval);
  
  // Return function to stop tracking
  return () => clearInterval(pollInterval);
}

/**
 * Display tracking information
 */
function displayTrackingUpdate(data) {
  const trackingElement = document.getElementById('tracking-info');
  if (!trackingElement) return;
  
  const statusColor = getStatusColor(data.status);
  const html = `
    <div class="card">
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--spacing-lg); margin-bottom: var(--spacing-xl);">
        <div>
          <div style="font-size: 0.875em; color: var(--gray-500); text-transform: uppercase;">Tracking #</div>
          <div style="font-weight: 600; font-size: 1.1em;">${data.tracking_number}</div>
        </div>
        <div>
          <div style="font-size: 0.875em; color: var(--gray-500); text-transform: uppercase;">Status</div>
          <div style="font-weight: 600; color: ${statusColor};">${data.status}</div>
        </div>
        <div>
          <div style="font-size: 0.875em; color: var(--gray-500); text-transform: uppercase;">Last Update</div>
          <div style="font-weight: 600;">${formatDate(data.updated_at)}</div>
        </div>
      </div>
      
      ${data.current_location ? `
        <div style="background: var(--gray-100); padding: var(--spacing-lg); border-radius: var(--radius-lg); margin-bottom: var(--spacing-lg);">
          <div style="font-weight: 600; margin-bottom: var(--spacing-md);">📍 Current Location</div>
          <div>${data.current_location}</div>
          ${data.latitude && data.longitude ? `
            <small style="display: block; margin-top: var(--spacing-sm); color: var(--gray-600);">
              Coordinates: ${data.latitude}, ${data.longitude}
            </small>
          ` : ''}
        </div>
      ` : ''}
      
      ${data.history && data.history.length > 0 ? `
        <div>
          <div style="font-weight: 600; margin-bottom: var(--spacing-lg);">Delivery Timeline</div>
          <div style="position: relative; padding-left: var(--spacing-lg);">
            ${data.history.map((event, i) => `
              <div style="display: flex; gap: var(--spacing-md); margin-bottom: var(--spacing-lg); position: relative;">
                <div style="position: absolute; left: -var(--spacing-lg); top: 6px; width: 12px; height: 12px; background: var(--accent); border-radius: 50%; border: 3px solid white;"></div>
                <div style="flex: 1;">
                  <div style="font-weight: 600; margin-bottom: 4px;">${event.status}</div>
                  <div style="color: var(--gray-600); font-size: 0.9em;">${event.location}</div>
                  <small style="color: var(--gray-500);">${formatDate(event.updated_at)}</small>
                  ${event.notes ? `<div style="color: var(--gray-600); margin-top: 4px; font-size: 0.9em;"><em>${event.notes}</em></div>` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}
    </div>
  `;
  
  trackingElement.innerHTML = html;
}

/**
 * Get color for status
 */
function getStatusColor(status) {
  const colors = {
    'pending': '#f59e0b',
    'confirmed': '#3b82f6',
    'picked_up': '#8b5cf6',
    'in_transit': '#06b6d4',
    'delivered': '#10b981',
    'cancelled': '#ef4444',
    'failed': '#ef4444'
  };
  return colors[status.toLowerCase()] || '#6b7280';
}

/**
 * Export tracking details
 */
function exportTracking(trackingData, format = 'pdf') {
  if (format === 'json') {
    const dataStr = JSON.stringify(trackingData, null, 2);
    downloadFile(dataStr, `tracking-${trackingData.tracking_number}.json`, 'application/json');
  } else if (format === 'csv') {
    let csv = 'Tracking Number,Status,Location,Updated At\n';
    csv += trackingData.history.map(h => 
      `${trackingData.tracking_number},"${h.status}","${h.location}","${h.updated_at}"`
    ).join('\n');
    downloadFile(csv, `tracking-${trackingData.tracking_number}.csv`, 'text/csv');
  }
}

/**
 * Download file helper
 */
function downloadFile(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Estimate remaining time
 */
function estimateDeliveryTime(trackingData) {
  const lastEvent = trackingData.history[0];
  if (!lastEvent) return 'Calculating...';
  
  const status = lastEvent.status.toLowerCase();
  
  const estimates = {
    'pending': '3-4 hours',
    'confirmed': '2-3 hours',
    'picked_up': '1-2 hours',
    'in_transit': '30-45 minutes',
    'delivered': 'Now'
  };
  
  return estimates[status] || 'Contact support';
}

/**
 * Subscribe to tracking notifications
 */
async function subscribeToTracking(trackingNumber, email) {
  try {
    const response = await apiCall('/tracking/subscribe', {
      method: 'POST',
      body: JSON.stringify({
        tracking_number: trackingNumber,
        email,
        notification_types: ['status_update', 'delivery_attempt', 'delivered']
      })
    });
    
    showNotification('You will receive tracking updates via email', 'success');
    return response;
  } catch (error) {
    handleError(error);
    return null;
  }
}

/**
 * Get tracking history
 */
async function getTrackingHistory(trackingNumber) {
  try {
    const response = await apiCall(`/tracking/history/${trackingNumber}`);
    return response;
  } catch (error) {
    handleError(error);
    return null;
  }
}

/**
 * Report delivery issue
 */
async function reportDeliveryIssue(trackingNumber, issueType, description) {
  try {
    const response = await apiCall('/tracking/report-issue', {
      method: 'POST',
      body: JSON.stringify({
        tracking_number: trackingNumber,
        issue_type: issueType,
        description
      })
    });
    
    showNotification('Issue reported. We will investigate shortly.', 'success');
    return response;
  } catch (error) {
    handleError(error);
    return null;
  }
}

// Make functions globally available
window.fetchTracking = fetchTracking;
window.startLiveTracking = startLiveTracking;
window.displayTrackingUpdate = displayTrackingUpdate;
window.getStatusColor = getStatusColor;
window.exportTracking = exportTracking;
window.estimateDeliveryTime = estimateDeliveryTime;
window.subscribeToTracking = subscribeToTracking;
window.getTrackingHistory = getTrackingHistory;
window.reportDeliveryIssue = reportDeliveryIssue;
// ============================================================================
// WEBSOCKET TRACKING PUBLIC API
// ============================================================================

/**
 * Start real-time WebSocket tracking for an order
 */
function startRealtimeTracking(orderId) {
  const service = getRealTimeTrackingService();
  service.subscribeToTracking(orderId);
}

/**
 * Stop real-time WebSocket tracking
 */
function stopRealtimeTracking(orderId) {
  const service = getRealTimeTrackingService();
  service.unsubscribeFromTracking(orderId);
}

/**
 * Get current tracking data
 */
function getRealtimeTrackingData(orderId) {
  const service = getRealTimeTrackingService();
  return service.getTrackingData(orderId);
}

/**
 * Subscribe to real-time GPS updates
 */
function onTrackingUpdate(orderId, callback) {
  const service = getRealTimeTrackingService();
  return service.subscribe(`tracking:${orderId}`, callback);
}

/**
 * Subscribe to status updates
 */
function onStatusUpdate(orderId, callback) {
  const service = getRealTimeTrackingService();
  return service.subscribe(`status:${orderId}`, callback);
}

/**
 * Subscribe to ETA updates
 */
function onEtaUpdate(orderId, callback) {
  const service = getRealTimeTrackingService();
  return service.subscribe(`eta:${orderId}`, callback);
}

/**
 * Subscribe to notifications
 */
function onTrackingNotification(callback) {
  const service = getRealTimeTrackingService();
  return service.subscribe('notification', callback);
}

// Make WebSocket functions globally available
window.initializeRealTimeTracking = initializeRealTimeTracking;
window.getRealTimeTrackingService = getRealTimeTrackingService;
window.startRealtimeTracking = startRealtimeTracking;
window.stopRealtimeTracking = stopRealtimeTracking;
window.getRealtimeTrackingData = getRealtimeTrackingData;
window.onTrackingUpdate = onTrackingUpdate;
window.onStatusUpdate = onStatusUpdate;
window.onEtaUpdate = onEtaUpdate;
window.onTrackingNotification = onTrackingNotification;