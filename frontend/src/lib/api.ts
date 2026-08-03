const USER_ID_KEY = 'chitfund_user_id'

// sessionStorage, not localStorage: it's scoped per-tab, not per-browser. With
// localStorage, logging in as a second user in another tab silently overwrites
// the identity the first tab was using for its next request - so an action in
// tab 1 could get attributed to whoever most recently logged in in tab 2. That's
// exactly wrong for demoing multiple pool members in one browser without
// incognito, which is the normal way to test this app locally.
export function getStoredUserId(): number | null {
  const raw = sessionStorage.getItem(USER_ID_KEY)
  return raw ? Number(raw) : null
}

export function setStoredUserId(id: number): void {
  sessionStorage.setItem(USER_ID_KEY, String(id))
}

export function clearStoredUserId(): void {
  sessionStorage.removeItem(USER_ID_KEY)
}

export class ApiError extends Error {}

// In dev, '/api' is rewritten to the local backend by Vite's server proxy
// (see vite.config.ts) - there's no such proxy in a production static build,
// so VITE_API_BASE_URL must be set at build time to the deployed backend's
// root URL (no /api suffix - the backend mounts routes at root, e.g.
// /auth/login, not /api/auth/login).
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const userId = getStoredUserId()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }
  if (userId !== null) {
    headers['X-User-Id'] = String(userId)
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(body.detail ?? `Request failed with status ${res.status}`)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return res.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
}
