// js/api.js
const API_BASE_URL = 'http://localhost:8000'; // Change to production URL later

const api = {
    getToken() {
        return localStorage.getItem('algoarena_jwt');
    },
    setToken(token) {
        localStorage.setItem('algoarena_jwt', token);
    },
    logout() {
        localStorage.removeItem('algoarena_jwt');
        window.location.href = 'index.html';
    },
    getUserId() {
        // Decode JWT payload to get sub (user ID)
        const token = this.getToken();
        if (!token) return null;
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.sub;
        } catch (e) {
            return null;
        }
    },
    async fetchJSON(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
            const data = await response.json().catch(() => ({}));
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.logout();
                }
                throw new Error(data.detail || 'API Error');
            }
            return data;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
};
