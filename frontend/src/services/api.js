export const API_BASE_URL = '/api/v1';

export async function fetchWithHandleError(url, options = {}) {
    let response;
    try {
        response = await fetch(`${API_BASE_URL}${url}`, options);
    } catch (networkErr) {
        const err = new Error('Unable to reach the server. Please ensure the backend is running.');
        err.status = 0;
        throw err;
    }

    if (!response.ok) {
        // Friendly message for proxy/gateway errors (backend not running)
        if ([502, 503, 504].includes(response.status)) {
            const err = new Error('Server is unavailable. Please ensure the backend is running on port 8000.');
            err.status = response.status;
            throw err;
        }

        let errorMsg = 'An error occurred';
        try {
            const errorData = await response.json();
            if (typeof errorData.detail === 'string') errorMsg = errorData.detail;
            else if (errorData.detail?.message) errorMsg = errorData.detail.message;
            else if (errorData.message) errorMsg = errorData.message;
        } catch {
            errorMsg = response.statusText;
        }
        const err = new Error(errorMsg);
        err.status = response.status;
        throw err;
    }
    return response.json();
}

export const api = {
    // Config
    getConfig: () => fetchWithHandleError('/config'),

    // ── Users ──────────────────────────────────────
    getUsers: () => fetchWithHandleError('/users'),

    createUser: (displayName, email) => fetchWithHandleError('/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ display_name: displayName, email })
    }),

    loginUser: (email, displayName) => fetchWithHandleError('/users/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: email || undefined,
            display_name: displayName || undefined,
        })
    }),

    deleteUser: (userId) => fetchWithHandleError(`/users/${userId}`, {
        method: 'DELETE',
    }),

    deleteAttempt: (userId, attemptId) => fetchWithHandleError(`/users/${userId}/attempts/${attemptId}`, {
        method: 'DELETE',
    }),

    getUserDashboard: (userId) => fetchWithHandleError(`/users/${userId}/dashboard`),

    // ── History ────────────────────────────────────
    getPoseHistory: (userId, poseName) => fetchWithHandleError(`/users/${userId}/poses/${poseName}/history`),

    // ── Analysis ──────────────────────────────────
    analyzeImage: async (file, userId = null) => {
        const formData = new FormData();
        formData.append('file', file);
        if (userId) {
            formData.append('user_id', userId);
        }

        const response = await fetch(`${API_BASE_URL}/analyze/image`, {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (!response.ok && response.status !== 422) {
            throw new Error(data.detail || data.message || 'Image analysis failed');
        }

        return { status: response.status, data };
    }
};
