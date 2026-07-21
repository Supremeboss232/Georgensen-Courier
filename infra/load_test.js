// Load Test Script - Georgensen Courier API
// k6 script for testing production readiness
// Run: k6 run load_test.js
// Install k6: https://k6.io/docs/getting-started/installation/

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Counter, Trend, Gauge } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const successRate = new Rate('success');
const requestDuration = new Trend('request_duration');
const apiCalls = new Counter('api_calls');
const activeVUs = new Gauge('active_vus');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000/api/v1';
const ADMIN_EMAIL = 'admin@georgensen.com';
const ADMIN_PASSWORD = 'AdminPassword123';

// Test scenarios
export const options = {
  vus: parseInt(__ENV.VUS || '50'),           // Virtual users
  duration: __ENV.DURATION || '5m',           // Test duration
  rampUp: '30s',                              // Ramp up time
  
  // Thresholds - what determines if test passes
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],  // 95th percentile < 500ms
    'http_req_failed': ['rate<0.05'],                  // < 5% failure rate
    'errors': ['rate<0.05'],
  },
  
  // Enable extended debug info
  ext: {
    loadimpact: {
      name: 'Georgensen Load Test',
      projectID: 3385050,
      name: 'staging'
    }
  }
};

// Global variables
let adminToken = '';
let customerToken = '';
let customerId = 0;
let invoiceId = 0;
let shipmentId = 0;

/**
 * SETUP - Run once before test
 */
export function setup() {
  console.log('🔧 Starting load test setup...');
  
  // Get admin token
  const adminLoginRes = http.post(`${BASE_URL}/auth/login`, {
    email: ADMIN_EMAIL,
    password: ADMIN_PASSWORD,
  });
  
  check(adminLoginRes, {
    'Admin login successful': (r) => r.status === 200,
  });
  
  if (adminLoginRes.status === 200) {
    adminToken = JSON.parse(adminLoginRes.body).access_token;
    console.log('✅ Admin token obtained');
  }
  
  return { adminToken, timestamp: new Date().toISOString() };
}

/**
 * MAIN TEST FUNCTION
 */
export default function (data) {
  const testRun = `test_${new Date().getTime()}`;
  
  group('Authentication Flow', () => {
    authenticationTests();
  });
  
  group('Customer Order Flow', () => {
    customerOrderFlow();
  });
  
  group('Order Tracking', () => {
    trackingFlow();
  });
  
  group('Payment Processing', () => {
    paymentFlow();
  });
  
  group('Admin Operations', () => {
    adminOperations(data.adminToken);
  });
  
  group('API Endpoints (General)', () => {
    generalApiTests();
  });
  
  // Metrics
  activeVUs.add(__VU);
  sleep(Math.random() * 3 + 1); // 1-4 second delay between iterations
}

/**
 * Test 1: Authentication Flow
 */
function authenticationTests() {
  // ✅ Register new customer
  const email = `customer_${new Date().getTime()}@test.com`;
  const registerRes = http.post(`${BASE_URL}/auth/register`, {
    email: email,
    password: 'TestPassword123',
    full_name: 'Test Customer',
    company_name: 'Test Company',
    account_type: 'business'
  });
  
  const registerSuccess = check(registerRes, {
    'Registration successful': (r) => r.status === 201 || r.status === 200,
  });
  errorRate.add(!registerSuccess);
  successRate.add(registerSuccess);
  requestDuration.add(registerRes.timings.duration);
  apiCalls.add(1);
  
  // ✅ Login
  const loginRes = http.post(`${BASE_URL}/auth/login`, {
    email: email,
    password: 'TestPassword123'
  });
  
  const loginSuccess = check(loginRes, {
    'Login successful': (r) => r.status === 200,
    'Token returned': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.access_token && body.access_token.length > 0;
      } catch {
        return false;
      }
    }
  });
  errorRate.add(!loginSuccess);
  successRate.add(loginSuccess);
  requestDuration.add(loginRes.timings.duration);
  apiCalls.add(1);
  
  if (loginSuccess) {
    customerToken = JSON.parse(loginRes.body).access_token;
  }
  
  // ✅ Get current user (verify token)
  const meRes = http.get(`${BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${customerToken}` }
  });
  
  const meSuccess = check(meRes, {
    'Get current user successful': (r) => r.status === 200,
  });
  errorRate.add(!meSuccess);
  successRate.add(meSuccess);
  requestDuration.add(meRes.timings.duration);
  apiCalls.add(1);
}

/**
 * Test 2: Customer Order Flow
 */
function customerOrderFlow() {
  // ✅ Get price quote
  const quoteRes = http.post(`${BASE_URL}/orders/quote`, {
    pickup_zip: '10001',
    delivery_zip: '90001',
    weight: 2.5,
    service_type: 'intercity',
    speed: 'standard'
  });
  
  const quoteSuccess = check(quoteRes, {
    'Get quote successful': (r) => r.status === 200,
    'Quote has price': (r) => {
      try {
        return JSON.parse(r.body).estimated_cost > 0;
      } catch {
        return false;
      }
    }
  });
  errorRate.add(!quoteSuccess);
  successRate.add(quoteSuccess);
  requestDuration.add(quoteRes.timings.duration);
  apiCalls.add(1);
  
  // ✅ Create order
  const createOrderRes = http.post(`${BASE_URL}/orders`, {
    pickup_contact_name: 'John Sender',
    pickup_phone: '555-1234',
    pickup_address: '123 Main St',
    pickup_city: 'New York',
    pickup_state: 'NY',
    pickup_zip: '10001',
    delivery_contact_name: 'Jane Receiver',
    delivery_phone: '555-5678',
    delivery_email: 'jane@example.com',
    delivery_address: '456 Oak Ave',
    delivery_city: 'Los Angeles',
    delivery_state: 'CA',
    delivery_zip: '90001',
    weight: 2.5,
    dimensions: '10x10x10',
    contents_description: 'Books and documents',
    service_type: 'intercity',
    speed: 'standard'
  }, {
    headers: { Authorization: `Bearer ${customerToken}` }
  });
  
  const createOrderSuccess = check(createOrderRes, {
    'Create order successful': (r) => r.status === 201 || r.status === 200,
    'Order has tracking number': (r) => {
      try {
        return JSON.parse(r.body).tracking_number && JSON.parse(r.body).tracking_number.length > 0;
      } catch {
        return false;
      }
    }
  });
  errorRate.add(!createOrderSuccess);
  successRate.add(createOrderSuccess);
  requestDuration.add(createOrderRes.timings.duration);
  apiCalls.add(1);
  
  if (createOrderSuccess) {
    const order = JSON.parse(createOrderRes.body);
    shipmentId = order.id;
  }
  
  // ✅ Get customer dashboard
  const dashboardRes = http.get(`${BASE_URL}/customer/dashboard`, {
    headers: { Authorization: `Bearer ${customerToken}` }
  });
  
  const dashboardSuccess = check(dashboardRes, {
    'Dashboard load successful': (r) => r.status === 200,
  });
  errorRate.add(!dashboardSuccess);
  successRate.add(dashboardSuccess);
  requestDuration.add(dashboardRes.timings.duration);
  apiCalls.add(1);
}

/**
 * Test 3: Order Tracking
 */
function trackingFlow() {
  // Use real tracking number from previous order
  const trackingNumber = 'GEO-2025-001-ABC';
  
  // ✅ Get shipment status
  const statusRes = http.get(`${BASE_URL}/tracking/${trackingNumber}`, {
    headers: { Authorization: `Bearer ${customerToken}` }
  });
  
  const statusSuccess = check(statusRes, {
    'Get tracking status successful': (r) => r.status === 200 || r.status === 404, // 404 is ok for test data
  });
  errorRate.add(statusRes.status >= 500); // Only count 5xx as errors
  requestDuration.add(statusRes.timings.duration);
  apiCalls.add(1);
  
  // ✅ Get tracking events
  const eventsRes = http.get(`${BASE_URL}/tracking/${trackingNumber}/events`, {
    headers: { Authorization: `Bearer ${customerToken}` }
  });
  
  const eventsSuccess = check(eventsRes, {
    'Get tracking events successful': (r) => r.status === 200 || r.status === 404,
  });
  errorRate.add(eventsRes.status >= 500);
  requestDuration.add(eventsRes.timings.duration);
  apiCalls.add(1);
}

/**
 * Test 4: Payment Flow
 */
function paymentFlow() {
  // ✅ Get customer invoices
  const invoicesRes = http.get(`${BASE_URL}/customer/invoices?limit=10`, {
    headers: { Authorization: `Bearer ${customerToken}` }
  });
  
  const invoicesSuccess = check(invoicesRes, {
    'List invoices successful': (r) => r.status === 200,
  });
  errorRate.add(!invoicesSuccess);
  successRate.add(invoicesSuccess);
  requestDuration.add(invoicesRes.timings.duration);
  apiCalls.add(1);
  
  // ✅ Create payment intent (without actually charging card)
  const intentRes = http.post(`${BASE_URL}/payments/intents`, {
    invoice_id: 1,
    amount: 2999,
    currency: 'USD'
  }, {
    headers: { Authorization: `Bearer ${customerToken}` }
  });
  
  const intentSuccess = check(intentRes, {
    'Create payment intent successful': (r) => r.status === 200 || r.status === 201 || r.status === 400, // 400 if no invoice
  });
  errorRate.add(intentRes.status >= 500);
  requestDuration.add(intentRes.timings.duration);
  apiCalls.add(1);
}

/**
 * Test 5: Admin Operations
 */
function adminOperations(token) {
  // ✅ List all orders (admin view)
  const ordersRes = http.get(`${BASE_URL}/admin/orders?limit=50`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  
  const ordersSuccess = check(ordersRes, {
    'Admin list orders successful': (r) => r.status === 200,
  });
  errorRate.add(!ordersSuccess);
  successRate.add(ordersSuccess);
  requestDuration.add(ordersRes.timings.duration);
  apiCalls.add(1);
  
  // ✅ Get admin dashboard
  const adminDashRes = http.get(`${BASE_URL}/admin/dashboard`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  
  const adminDashSuccess = check(adminDashRes, {
    'Admin dashboard successful': (r) => r.status === 200 || r.status === 404,
  });
  errorRate.add(adminDashSuccess ? false : (adminDashRes.status >= 500));
  requestDuration.add(adminDashRes.timings.duration);
  apiCalls.add(1);
}

/**
 * Test 6: General API Endpoints
 */
function generalApiTests() {
  // ✅ Health check
  const healthRes = http.get(`http://localhost:8000/health`);
  
  const healthSuccess = check(healthRes, {
    'Health check successful': (r) => r.status === 200,
  });
  errorRate.add(!healthSuccess);
  successRate.add(healthSuccess);
  requestDuration.add(healthRes.timings.duration);
  apiCalls.add(1);
  
  // ✅ API version check
  const versionRes = http.get(`http://localhost:8000/api/v1/`);
  
  const versionSuccess = check(versionRes, {
    'API version check successful': (r) => r.status === 200 || r.status === 404,
  });
  errorRate.add(versionRes.status >= 500);
  requestDuration.add(versionRes.timings.duration);
  apiCalls.add(1);
}

/**
 * TEARDOWN - Run once after test
 */
export function teardown(data) {
  console.log('✅ Load test completed');
  console.log(`ℹ️  Test started at: ${data.timestamp}`);
  console.log(`ℹ️  Test ended at: ${new Date().toISOString()}`);
}

/**
 * HANDLE ERRORS
 */
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'summary.json': JSON.stringify(data),
  };
}

/**
 * TEXT SUMMARY FUNCTION
 */
function textSummary(data, options) {
  let summary = `
╔════════════════════════════════════════════════════════════════╗
║           GEORGENSEN LOAD TEST RESULTS SUMMARY                 ║
╚════════════════════════════════════════════════════════════════╝

📊 TEST CONFIGURATION:
  • Server: ${BASE_URL}
  • Duration: ${options.duration || '5m'}
  • Virtual Users: ${options.vus || '50'}
  • Ramp-up: 30s

📈 RESULTS:
  • Total API Calls: ${Math.round(data.metrics.api_calls?.value || 0)}
  • Passed: ${Math.round(data.metrics.success?.value * 100 || 0)}%
  • Failed: ${Math.round(data.metrics.errors?.value * 100 || 0)}%

⏱️  TIMING:
  • Avg Response: ${Math.round(data.metrics.request_duration?.values?.avg || 0)}ms
  • p95 Response: ${Math.round(data.metrics.request_duration?.values?.p95 || 0)}ms
  • p99 Response: ${Math.round(data.metrics.request_duration?.values?.p99 || 0)}ms
  • Max Response: ${Math.round(data.metrics.request_duration?.values?.max || 0)}ms

🎯 PASS/FAIL CRITERIA:
  ${data.metrics.http_req_duration?.values?.p95 < 500 ? '✅ p95 < 500ms' : '❌ p95 >= 500ms'}
  ${data.metrics.http_req_duration?.values?.p99 < 1000 ? '✅ p99 < 1000ms' : '❌ p99 >= 1000ms'}
  ${data.metrics.http_req_failed?.value < 0.05 ? '✅ Error rate < 5%' : '❌ Error rate >= 5%'}

🏁 FINAL VERDICT:
  ${(data.metrics.http_req_duration?.values?.p95 < 500 && 
    data.metrics.http_req_duration?.values?.p99 < 1000 &&
    data.metrics.http_req_failed?.value < 0.05) ? '✅ PASS - Ready for production!' : '❌ FAIL - Needs optimization'}
  `;
  
  return summary;
}
