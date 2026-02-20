const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = {
    async registerUser(userData) {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }
        return await response.json();
    },

    async loginUser(email, password) {
        const response = await fetch("http://127.0.0.1:8000/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email,
                password
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        // For temporary validation, if there's no token we still return success if the message is there
        if (data.message === "Login successful") {
            // Note: In a real app we'd get a token here. For now we just return.
            return data;
        }

        if (data.access_token) {
            localStorage.setItem('oinzpay_token', data.access_token);
        }
        return data;
    },

    getToken() {
        return localStorage.getItem('oinzpay_token');
    },

    logout() {
        localStorage.removeItem('oinzpay_token');
        window.location.href = 'login.html';
    },

    async getAuthenticated(endpoint) {
        const token = this.getToken();
        if (!token) throw new Error('Not authenticated');

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 401 || response.status === 403) {
            this.logout();
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }

        return await response.json();
    },

    async postAuthenticated(endpoint, body) {
        const token = this.getToken();
        if (!token) throw new Error('Not authenticated');

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(body)
        });

        if (response.status === 401 || response.status === 403) {
            this.logout();
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }

        return await response.json();
    },

    async fetchDashboard() {
        return await this.getAuthenticated('/escrow/dashboard');
    },

    async fetchTransactions() {
        return await this.getAuthenticated('/escrow/user/all');
    },

    async createEscrow(escrowData) {
        return await this.postAuthenticated('/escrow/create', escrowData);
    },

    async fundEscrow(escrowId) {
        return await this.postAuthenticated(`/escrow/${escrowId}/fund`, {});
    },

    async releaseEscrow(escrowId) {
        return await this.postAuthenticated(`/escrow/${escrowId}/release`, {});
    }
};

window.OinzPayAPI = api;
