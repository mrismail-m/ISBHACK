import { demoRequest } from '../features/student/demo-store';
export const USE_FIXTURES = import.meta.env.VITE_USE_FIXTURES === '1';
const base = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
export const API_BASE = base.endsWith('/api/v1') ? base : `${base}/api/v1`;
const fixtures = import.meta.glob('../../../fixtures/api/*.json', { import: 'default' });
export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, code: string, message: string) { super(message); this.status = status; this.code = code; }
}
export async function apiClient<T>(endpoint: string, options: RequestInit & { fixtureName?: string } = {}): Promise<T> {
  const { fixtureName, ...request } = options;
  if (USE_FIXTURES) {
    if ((!request.method || request.method === 'GET') && fixtureName) {
      const load = fixtures[`../../../fixtures/api/${fixtureName}.json`];
      if (load) return await load() as T;
    }
    return demoRequest(endpoint, request) as T;
  }
  const headers = new Headers(request.headers);
  headers.set('Content-Type', 'application/json');
  headers.set('X-User-Id', localStorage.getItem('currentUserId') || '');
  const response = await fetch(`${API_BASE}${endpoint}`, { ...request, headers });
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    const error = body && typeof body === 'object' && 'error' in body ? body.error : null;
    const message = error && typeof error === 'object' && 'message' in error ? String(error.message) : `Request failed (${response.status}).`;
    const code = error && typeof error === 'object' && 'code' in error ? String(error.code) : 'request_failed';
    throw new ApiError(response.status, code, message);
  }
  return response.json() as Promise<T>;
}
