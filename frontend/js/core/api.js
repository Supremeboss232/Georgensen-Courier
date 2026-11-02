// Core API utilities with automatic signature detection, prefix normalization, and auth header injection
const API_BASE_URL = '/api/v1';

const HTTP_METHODS = new Set(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']);

function normalizeEndpoint(rawEndpoint) {
    if (!rawEndpoint) return '';
    if (rawEndpoint.startsWith('http://') || rawEndpoint.startsWith('https://')) {
        return rawEndpoint;
    }
    let ep = String(rawEndpoint).trim();
    // Strip any redundant /api/v1 prefixes (even if repeated like /api/v1/api/v1)
    while (ep.startsWith('/api/v1')) {
        ep = ep.slice(7);
    }
    if (ep.startsWith('/api/') && !ep.startsWith('/api/v1')) {
        // Keep /api/contacts or normalize to /api/v1
        return ep;
    }
    if (!ep.startsWith('/')) {
        ep = '/' + ep;
    }
    return `${API_BASE_URL}${ep}`;
}

/**
 * Universal API call helper supporting both:
 *   apiCall(method, endpoint, data, headers)
 *   apiCall(endpoint, method, data, headers)
 *   apiCall(endpoint)
 */
async function apiCall(arg1, arg2 = 'GET', data = null, headers = {}) {
    let method = 'GET';
    let endpoint = '';

    if (typeof arg1 === 'string' && HTTP_METHODS.has(arg1.toUpperCase())) {
        method = arg1.toUpperCase();
        endpoint = arg2;
    } else {
        endpoint = arg1;
        method = (typeof arg2 === 'string' && HTTP_METHODS.has(arg2.toUpperCase()))
            ? arg2.toUpperCase()
            : 'GET';
        if (arg2 && typeof arg2 === 'object' && data === null) {
            data = arg2;
            method = 'POST';
        }
    }

    const url = normalizeEndpoint(endpoint);
    const token = localStorage.getItem('authToken') || localStorage.getItem('access_token');

    const reqHeaders = {
        'Content-Type': 'application/json',
        ...headers
    };
    if (token && !reqHeaders['Authorization']) {
        reqHeaders['Authorization'] = `Bearer ${token}`;
    }

    const options = {
        method,
        headers: reqHeaders
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        options.body = typeof data === 'string' ? data : JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || `API Error: ${response.status}`);
        }

        if (response.status === 204) {
            return null;
        }
        return await response.json();
    } catch (error) {
        console.error('API Call Failed:', error);
        throw error;
    }
}

// GET request
function get(endpoint, headers = {}) {
    return apiCall('GET', endpoint, null, headers);
}

// POST request
function post(endpoint, data, headers = {}) {
    return apiCall('POST', endpoint, data, headers);
}

// PUT request
function put(endpoint, data, headers = {}) {
    return apiCall('PUT', endpoint, data, headers);
}

// DELETE request
function del(endpoint, headers = {}) {
    return apiCall('DELETE', endpoint, null, headers);
}

// GET with auth token
function getWithAuth(endpoint) {
    const token = localStorage.getItem('authToken') || localStorage.getItem('access_token');
    return get(endpoint, token ? { 'Authorization': `Bearer ${token}` } : {});
}

// POST with auth token
function postWithAuth(endpoint, data) {
    const token = localStorage.getItem('authToken') || localStorage.getItem('access_token');
    return post(endpoint, data, token ? { 'Authorization': `Bearer ${token}` } : {});
}

// PUT with auth token
function putWithAuth(endpoint, data) {
    const token = localStorage.getItem('authToken') || localStorage.getItem('access_token');
    return put(endpoint, data, token ? { 'Authorization': `Bearer ${token}` } : {});
}

// DELETE with auth token
function delWithAuth(endpoint) {
    const token = localStorage.getItem('authToken') || localStorage.getItem('access_token');
    return del(endpoint, token ? { 'Authorization': `Bearer ${token}` } : {});
}

window.apiCall = apiCall;
window.get = get;
window.post = post;
window.put = put;
window.del = del;
window.getWithAuth = getWithAuth;
window.postWithAuth = postWithAuth;
window.putWithAuth = putWithAuth;
window.delWithAuth = delWithAuth;
