// Core API utilities
const API_BASE_URL = '/api/v1';

async function apiCall(method, endpoint, data = null, headers = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...headers
        }
    };

    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API Error: ${response.status}`);
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
    const token = localStorage.getItem('authToken');
    return get(endpoint, { 'Authorization': `Bearer ${token}` });
}

// POST with auth token
function postWithAuth(endpoint, data) {
    const token = localStorage.getItem('authToken');
    return post(endpoint, data, { 'Authorization': `Bearer ${token}` });
}

// PUT with auth token
function putWithAuth(endpoint, data) {
    const token = localStorage.getItem('authToken');
    return put(endpoint, data, { 'Authorization': `Bearer ${token}` });
}

// DELETE with auth token
function delWithAuth(endpoint) {
    const token = localStorage.getItem('authToken');
    return del(endpoint, { 'Authorization': `Bearer ${token}` });
}
