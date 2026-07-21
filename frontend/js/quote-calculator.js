// QUOTE-CALCULATOR.JS - Pricing calculation engine

/**
 * Pricing configuration
 */
const PRICING_CONFIG = {
  local: {
    base_fare: 500,
    distance_rate: 0.50,
    weight_rate: 2.00
  },
  intercity: {
    base_fare: 1500,
    distance_rate: 0.30,
    weight_rate: 1.50
  },
  international: {
    base_fare: 5000,
    distance_rate: 0.15,
    weight_rate: 1.00
  }
};

const SPEED_MULTIPLIERS = {
  economy: 0.8,
  standard: 1.0,
  express: 1.5
};

const INSURANCE_RATE = 0.05; // 5%

/**
 * Calculate shipping quote
 */
function calculateQuote(params) {
  const {
    service_type,
    distance,
    weight,
    speed = 'standard',
    package_value = 0
  } = params;
  
  // Validate inputs
  if (!service_type || !PRICING_CONFIG[service_type]) {
    throw new Error('Invalid service type');
  }
  if (distance <= 0 || weight <= 0) {
    throw new Error('Distance and weight must be greater than 0');
  }
  if (!SPEED_MULTIPLIERS[speed]) {
    throw new Error('Invalid speed option');
  }
  
  const config = PRICING_CONFIG[service_type];
  
  // Calculate base components
  const base_fare = config.base_fare;
  const distance_charge = distance * config.distance_rate;
  const weight_charge = weight * config.weight_rate;
  const subtotal = base_fare + distance_charge + weight_charge;
  
  // Apply speed multiplier
  const speed_multiplier = SPEED_MULTIPLIERS[speed];
  const total_with_speed = subtotal * speed_multiplier;
  
  // Calculate insurance (optional)
  const insurance_charge = package_value > 0 ? package_value * INSURANCE_RATE : 0;
  
  // Final total
  const total_price = total_with_speed + insurance_charge;
  
  return {
    service_type,
    distance,
    weight,
    speed,
    package_value,
    base_fare: Math.round(base_fare),
    distance_charge: Math.round(distance_charge * 100) / 100,
    weight_charge: Math.round(weight_charge * 100) / 100,
    subtotal: Math.round(subtotal * 100) / 100,
    speed_multiplier,
    speed_adjustment: Math.round((subtotal * speed_multiplier - subtotal) * 100) / 100,
    total_with_speed: Math.round(total_with_speed * 100) / 100,
    insurance_charge: Math.round(insurance_charge * 100) / 100,
    total_price: Math.round(total_price * 100) / 100,
    breakdown: {
      base_fare: base_fare,
      distance: `${distance}km @ ₦${config.distance_rate}/km = ₦${Math.round(distance_charge * 100) / 100}`,
      weight: `${weight}kg @ ₦${config.weight_rate}/kg = ₦${Math.round(weight_charge * 100) / 100}`,
      speed: `${speed} (${speed_multiplier}x multiplier)`,
      insurance: package_value > 0 ? `5% of ₦${package_value} = ₦${Math.round(insurance_charge * 100) / 100}` : 'None'
    }
  };
}

/**
 * Get estimated delivery time
 */
function getEstimatedDeliveryTime(serviceType, distance) {
  let daysMin, daysMax;
  
  switch(serviceType) {
    case 'local':
      return {
        min: '2 hours',
        max: '24 hours',
        description: 'Same day or next day'
      };
    case 'intercity':
      daysMin = Math.ceil(distance / 300); // Assume 300km per day
      daysMax = Math.ceil(distance / 200); // Slower estimate
      return {
        min: `${daysMin} day${daysMin > 1 ? 's' : ''}`,
        max: `${daysMax} days`,
        description: `${daysMin}-${daysMax} business days`
      };
    case 'international':
      return {
        min: '7 days',
        max: '30 days',
        description: 'Depends on destination and customs clearance'
      };
    default:
      return {
        min: 'Unknown',
        max: 'Unknown',
        description: 'Contact support'
      };
  }
}

/**
 * Generate tracking number format
 */
function generateTrackingNumberFormat() {
  const prefix = 'GEO';
  const year = new Date().getFullYear().toString().slice(-2);
  const random = Math.random().toString(36).substring(2, 8).toUpperCase();
  return `${prefix}-${year}-${random}`;
}

/**
 * Validate package for shipping
 */
function validatePackage(packageData) {
  const errors = [];
  
  if (!packageData.weight || packageData.weight <= 0) {
    errors.push('Weight must be greater than 0');
  }
  
  if (packageData.weight > 1000) {
    errors.push('Package exceeds maximum weight of 1000kg');
  }
  
  if (!packageData.description || packageData.description.trim().length < 3) {
    errors.push('Please provide package description (min 3 characters)');
  }
  
  if (packageData.value < 0) {
    errors.push('Package value cannot be negative');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Get pricing tiers for bulk orders
 */
function getBulkDiscount(orderCount) {
  if (orderCount >= 100) return 0.15; // 15% discount
  if (orderCount >= 50) return 0.12;  // 12% discount
  if (orderCount >= 20) return 0.10;  // 10% discount
  if (orderCount >= 10) return 0.05;  // 5% discount
  return 0;
}

/**
 * Apply bulk discount to quote
 */
function applyBulkDiscount(quote, orderCount) {
  const discount = getBulkDiscount(orderCount);
  const discount_amount = quote.total_price * discount;
  
  return {
    ...quote,
    original_price: quote.total_price,
    bulk_discount_rate: discount,
    bulk_discount_amount: Math.round(discount_amount * 100) / 100,
    total_price: Math.round((quote.total_price - discount_amount) * 100) / 100,
    per_package_price: Math.round((quote.total_price - discount_amount) / orderCount * 100) / 100
  };
}

/**
 * Compare quotes across service types
 */
function compareQuotes(distance, weight, package_value = 0) {
  const serviceTypes = ['local', 'intercity', 'international'];
  const speeds = ['economy', 'standard', 'express'];
  
  const quotes = {};
  
  serviceTypes.forEach(service => {
    quotes[service] = {};
    speeds.forEach(speed => {
      quotes[service][speed] = calculateQuote({
        service_type: service,
        distance,
        weight,
        speed,
        package_value
      });
    });
  });
  
  return quotes;
}

// Make function globally available
window.calculateQuote = calculateQuote;
window.getEstimatedDeliveryTime = getEstimatedDeliveryTime;
window.generateTrackingNumberFormat = generateTrackingNumberFormat;
window.validatePackage = validatePackage;
window.getBulkDiscount = getBulkDiscount;
window.applyBulkDiscount = applyBulkDiscount;
window.compareQuotes = compareQuotes;
