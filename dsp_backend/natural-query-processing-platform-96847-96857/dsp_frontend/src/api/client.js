/**
 * Simple API client that selects the backend base URL.
 * Falls back to http://localhost:3001 when REACT_APP_BACKEND_URL is not defined.
 */

// PUBLIC_INTERFACE
export function getBackendBaseUrl() {
    /** Returns the backend base URL for API calls. */
    const envUrl = process.env.REACT_APP_BACKEND_URL;
    return envUrl && envUrl.trim().length > 0 ? envUrl : "http://localhost:3001";
}

// PUBLIC_INTERFACE
export async function apiPost(path, body, token) {
    /** POST helper with optional Bearer auth. */
    const base = getBackendBaseUrl();
    const headers = {
        "Content-Type": "application/json",
    };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    const resp = await fetch(`${base}${path}`, {
        method: "POST",
        headers,
        body: JSON.stringify(body ?? {}),
    });
    const contentType = resp.headers.get("content-type") || "";
    if (!resp.ok) {
        let detail = await (contentType.includes("application/json") ? resp.json() : resp.text());
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return contentType.includes("application/json") ? resp.json() : resp.text();
}

// PUBLIC_INTERFACE
export async function apiGet(path, token) {
    /** GET helper with optional Bearer auth. */
    const base = getBackendBaseUrl();
    const headers = {};
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    const resp = await fetch(`${base}${path}`, {
        method: "GET",
        headers,
    });
    const contentType = resp.headers.get("content-type") || "";
    if (!resp.ok) {
        let detail = await (contentType.includes("application/json") ? resp.json() : resp.text());
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return contentType.includes("application/json") ? resp.json() : resp.text();
}
