/**
 * Georgensen Real-Time Tracking System
 * WebSocket-based live delivery tracking with GPS coordinates and status updates
 * 
 * Features:
 * - Live GPS tracking for active deliveries
 * - Real-time status updates
 * - Distance and ETA calculation
 * - Route visualization
 * - Notification system for delivery events
 */

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
    
    // Bind methods
    this.connect = this.connect.bind(this);
    this.disconnect = this.disconnect.bind(this);
    this.handleMessage = this.handleMessage.bind(this);
    this.handleError = this.handleError.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }
  
  /**
   * Connect to WebSocket server
   */
  connect() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('Already connected to tracking server');
      return;
    }
    
    try {
      this.ws = new WebSocket(this.wsUrl);
      
      this.ws.onopen = () => {
        console.log('Connected to tracking server');
        this.reconnectAttempts = 0;
        this.initialized = true;
        this.emit('connected');
        
        // Subscribe to any previously active tracking sessions
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
  
  /**
   * Handle incoming WebSocket messages
   */
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
        default:
          console.log('Unknown message type:', data.type);
      }
    } catch (error) {
      console.error('Error parsing tracking message:', error);
    }
  }
  
  /**
   * Handle tracking coordinate updates (GPS location)
   */
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
    
    // Keep only last 100 coordinates to avoid memory bloat
    if (trackingData.coordinates.length > 100) {
      trackingData.coordinates.shift();
    }
    
    this.activeTracking.set(orderId, trackingData);
    
    // Emit to all subscribers
    this.emit(`tracking:${orderId}`, trackingData);
    this.emit('tracking:all', { orderId, location: trackingData.currentLocation });
  }
  
  /**
   * Handle delivery status changes
   */
  handleStatusUpdate(data) {
    const { orderId, status, timestamp, partnerId, message } = data;
    
    const trackingData = this.activeTracking.get(orderId) || {};
    trackingData.status = status;
    trackingData.lastStatusUpdate = { status, timestamp, message };
    trackingData.partnerId = partnerId;
    
    this.activeTracking.set(orderId, trackingData);
    
    this.emit(`status:${orderId}`, { status, timestamp, message });
    this.emit('status:all', { orderId, status, message });
    
    // Show notification
    if (typeof showNotification !== 'undefined') {
      showNotification(`Order ${orderId}: ${message || status}`, this.getNotificationType(status));
    }
  }
  
  /**
   * Handle ETA and distance calculations
   */
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
  
  /**
   * Handle notifications from the server
   */
  handleNotification(data) {
    const { type, message, orderId, severity } = data;
    
    if (typeof showNotification !== 'undefined') {
      if (severity === 'urgent') {
        showNotification(`⚠️ ${message}`, 'warning');
      } else if (severity === 'error') {
        showNotification(`❌ ${message}`, 'error');
      } else {
        showNotification(message, 'info');
      }
    }
    
    this.emit('notification', { type, message, orderId, severity });
  }
  
  /**
   * Handle server errors
   */
  handleServerError(data) {
    const { message, code } = data;
    console.error(`Server error [${code}]: ${message}`);
    if (typeof showNotification !== 'undefined') {
      showNotification(`Tracking error: ${message}`, 'error');
    }
  }
  
  /**
   * Handle connection errors
   */
  handleError(error) {
    console.error('WebSocket error:', error);
    this.emit('error', error);
  }
  
  /**
   * Handle connection close
   */
  handleClose() {
    console.log('Disconnected from tracking server');
    this.initialized = false;
    this.emit('disconnected');
    
    // Attempt to reconnect
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    }
  }
  
  /**
   * Subscribe to tracking updates for a specific order
   */
  subscribeToTracking(orderId) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected');
      return;
    }
    
    const message = {
      type: 'subscribe',
      orderId,
      timestamp: new Date().toISOString()
    };
    
    this.ws.send(JSON.stringify(message));
    console.log(`Subscribed to tracking: ${orderId}`);
  }
  
  /**
   * Unsubscribe from tracking updates
   */
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
    console.log(`Unsubscribed from tracking: ${orderId}`);
  }
  
  /**
   * Get tracking data for an order
   */
  getTrackingData(orderId) {
    return this.activeTracking.get(orderId) || null;
  }
  
  /**
   * Get all active tracking sessions
   */
  getAllTrackingData() {
    return Array.from(this.activeTracking.values());
  }
  
  /**
   * Calculate distance between two coordinates using Haversine formula
   */
  calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
      Math.sin(dLng / 2) * Math.sin(dLng / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }
  
  /**
   * Estimate ETA based on distance and average speed
   */
  estimateETA(distanceKm, averageSpeedKmh = 40) {
    const hours = distanceKm / averageSpeedKmh;
    const minutes = Math.round(hours * 60);
    return new Date(Date.now() + minutes * 60 * 1000);
  }
  
  /**
   * Subscribe to events
   */
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
  
  /**
   * Emit events
   */
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
  
  /**
   * Get notification type based on status
   */
  getNotificationType(status) {
    const types = {
      'pending': 'info',
      'confirmed': 'info',
      'picked_up': 'info',
      'in_transit': 'success',
      'delivery_ready': 'warning',
      'delivered': 'success',
      'failed': 'error'
    };
    return types[status] || 'info';
  }
  
  /**
   * Disconnect from WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.activeTracking.clear();
    this.initialized = false;
  }
}

// Global instance
let trackingService = null;

/**
 * Initialize the tracking service (call once on app startup)
 */
function initializeTracking(options = {}) {
  if (!trackingService) {
    trackingService = new RealTimeTracking(options);
    trackingService.connect();
  }
  return trackingService;
}

/**
 * Get the tracking service instance
 */
function getTrackingService() {
  if (!trackingService) {
    trackingService = new RealTimeTracking();
    trackingService.connect();
  }
  return trackingService;
}

/**
 * Start tracking an order in real-time
 */
function startTracking(orderId) {
  const service = getTrackingService();
  service.subscribeToTracking(orderId);
}

/**
 * Stop tracking an order
 */
function stopTracking(orderId) {
  const service = getTrackingService();
  service.unsubscribeFromTracking(orderId);
}

/**
 * Get current tracking data for an order
 */
function getOrderTracking(orderId) {
  const service = getTrackingService();
  return service.getTrackingData(orderId);
}

/**
 * Subscribe to tracking updates for an order
 * Usage: trackingUpdates(orderId, (data) => { console.log(data); })
 */
function trackingUpdates(orderId, callback) {
  const service = getTrackingService();
  return service.subscribe(`tracking:${orderId}`, callback);
}

/**
 * Subscribe to status updates for an order
 */
function statusUpdates(orderId, callback) {
  const service = getTrackingService();
  return service.subscribe(`status:${orderId}`, callback);
}

/**
 * Subscribe to ETA updates for an order
 */
function etaUpdates(orderId, callback) {
  const service = getTrackingService();
  return service.subscribe(`eta:${orderId}`, callback);
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    RealTimeTracking,
    initializeTracking,
    getTrackingService,
    startTracking,
    stopTracking,
    getOrderTracking,
    trackingUpdates,
    statusUpdates,
    etaUpdates
  };
}
