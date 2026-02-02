/**
 * Fresas Standalone - API Client
 */
// In Docker: uses relative URL; In dev: uses localhost
const API_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? ''
    : 'http://localhost:8002';

export async function apiGet(endpoint: string, params?: Record<string, any>) {
    const url = new URL(`${API_URL}/api${endpoint}`);
    if (params) {
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                url.searchParams.append(key, String(value));
            }
        });
    }

    const response = await fetch(url.toString());
    if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
}

export async function apiPost(endpoint: string, data?: any) {
    const response = await fetch(`${API_URL}/api${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: data ? JSON.stringify(data) : undefined
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `API Error: ${response.status}`);
    }
    return response.json();
}
