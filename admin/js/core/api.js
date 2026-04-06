// Admin API Client - Zentraler API-Wrapper für Admin-Operations
// Extrahiert aus admin.html für bessere Wartbarkeit

export class AdminAPI {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
    }

    /**
     * Internal URL normalizer für Admin-Endpoints
     */
    _normalizeUrl(url) {
        let finalUrl = url;
        
        // Prepend /api if missing for internal paths
        if (url.startsWith('/') && !url.startsWith('/api/') && url !== '/api') {
            finalUrl = '/api' + url;
        }

        // Standardize building/resource internal endpoint names
        finalUrl = finalUrl.replace('/admin/buildings', '/admin/gebaeude_typen');
        finalUrl = finalUrl.replace('/admin/ressourcen', '/admin/rohstoffe');

        return finalUrl;
    }

    /**
     * Generic GET request
     */
    async get(endpoint, token = null) {
        const url = this._normalizeUrl(endpoint);
        const options = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }

        return this._handleResponse(url, options);
    }

    /**
     * Generic POST request
     */
    async post(endpoint, body, token = null) {
        const url = this._normalizeUrl(endpoint);
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        };
        
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }

        return this._handleResponse(url, options);
    }

    /**
     * Generic PATCH request
     */
    async patch(endpoint, id, body, token = null) {
        const url = this._normalizeUrl(`${endpoint}/${id}`);
        const options = {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        };
        
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }

        return this._handleResponse(url, options);
    }

    /**
     * Generic DELETE request
     */
    async delete(endpoint, id, token = null) {
        const url = this._normalizeUrl(`${endpoint}/${id}`);
        const options = {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }

        return this._handleResponse(url, options);
    }

    /**
     * Generic PUT request
     */
    async put(endpoint, id, body, token = null) {
        const url = this._normalizeUrl(`${endpoint}/${id}`);
        const options = {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        };
        
        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }

        return this._handleResponse(url, options);
    }

    /**
     * Generic POST with query params (for token-passing style)
     */
    async postWithToken(endpoint, body, token) {
        const url = `${this._normalizeUrl(endpoint)}?token=${token}`;
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        };

        return this._handleResponse(url, options);
    }

    /**
     * Generic PATCH with query params (for token-passing style)
     */
    async patchWithToken(endpoint, id, body, token) {
        const url = `${this._normalizeUrl(endpoint)}/${id}?token=${token}`;
        const options = {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body)
        };

        return this._handleResponse(url, options);
    }

    /**
     * Generic DELETE with query params (for token-passing style)
     */
    async deleteWithToken(endpoint, id, token) {
        const url = `${this._normalizeUrl(endpoint)}/${id}?token=${token}`;
        const options = {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        };

        return this._handleResponse(url, options);
    }

    /**
     * Generic DELETE with query params (for token-passing style)
     */
    async delete(endpoint, id, token) {
        const url = `${this._normalizeUrl(endpoint)}/${id}?token=${token}`;
        const options = {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        };

        return this._handleResponse(url, options);
    }

    /**
     * Handle response and errors
     */
    async _handleResponse(url, options) {
        try {
            const res = await fetch(url, options);
            
            // Check for auth errors
            if (res.status === 401 || res.status === 403) {
                console.warn("Auth Error:", res.status, url);
                // Don't redirect automatically - let caller handle
            }
            
            return res;
        } catch (err) {
            console.error("Fetch error:", err);
            throw err;
        }
    }
}

// Convenience function for backwards compatibility
export async function adminFetch(url, options = {}) {
    const api = new AdminAPI();
    return api._normalizeUrl(url);
}
