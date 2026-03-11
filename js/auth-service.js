/**
 * Wasteland Authentication Service
 * Handles JWT Storage, Refresh and authenticated Fetch requests.
 */

const AUTH_CONFIG = {
    apiBase: "", // Empty if same origin
    loginPath: "/auth/login",
    refreshPath: "/auth/refresh",
    registerPath: "/auth/register"
};

const AuthService = {
    saveTokens({ access_token, refresh_token, player_id, role, username }) {
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
        localStorage.setItem('player_id', player_id);
        localStorage.setItem('role', role);
        localStorage.setItem('username', username);
    },

    getAccessToken() { return localStorage.getItem('access_token'); },
    getRefreshToken() { return localStorage.getItem('refresh_token'); },
    getPlayerId() { return localStorage.getItem('player_id'); },
    getRole() { return localStorage.getItem('role'); },
    getUsername() { return localStorage.getItem('username'); },
    getUserId() { return localStorage.getItem('user_id'); }, // Optional, check main.py response

    logout() {
        localStorage.clear();
        window.location.href = "/login.html";
    },

    async login(username, password) {
        const res = await fetch(AUTH_CONFIG.loginPath, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (!res.ok) throw new Error("Login fehlgeschlagen");
        const data = await res.json();
        this.saveTokens(data);
        return data;
    },

    async register(username, password, email) {
        const res = await fetch(AUTH_CONFIG.registerPath, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, email })
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Registrierung fehlgeschlagen");
        }
        const data = await res.json();
        this.saveTokens(data);
        return data;
    },

    async refreshToken() {
        const rt = this.getRefreshToken();
        if (!rt) return this.logout();

        const res = await fetch(AUTH_CONFIG.refreshPath, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: rt })
        });

        if (res.ok) {
            const data = await res.json();
            this.saveTokens(data);
            return data.access_token;
        } else {
            this.logout();
            return null;
        }
    },

    /**
     * Fetch wrapper that adds Authorization header and handles 401 automatically
     */
    async fetch(url, options = {}) {
        let token = this.getAccessToken();

        // Backend compatibility: Add token to URL if not present
        let finalUrl = url;
        if (token) {
            const urlObj = new URL(url, window.location.origin);
            if (!urlObj.searchParams.has('token')) {
                urlObj.searchParams.append('token', token);
            }
            finalUrl = urlObj.toString();
        }

        const headers = { ...options.headers };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        let res = await fetch(finalUrl, { ...options, headers });

        if (res.status === 401) {
            // Unauthorized - try refreshing
            token = await this.refreshToken();
            if (token) {
                // Retry with new token
                return this.fetch(url, options);
            }
        }

        return res;
    }
};

window.AuthService = AuthService;
