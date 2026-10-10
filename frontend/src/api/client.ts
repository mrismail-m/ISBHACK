export const USE_FIXTURES = import.meta.env.VITE_USE_FIXTURES === '1';
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit & { fixtureName?: string }
): Promise<T> {
  if (USE_FIXTURES && options?.fixtureName) {
    const module = await import(`../../fixtures/api/${options.fixtureName}.json`);
    return module.default as T;
  }

  if (USE_FIXTURES && !options?.fixtureName) {
    console.warn(`No fixtureName provided for endpoint ${endpoint}, falling back to mock response.`);
    return {} as T;
  }

  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': localStorage.getItem('currentUserId') || '',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let errorMessage = `API error: ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData?.error?.message) {
        errorMessage = errorData.error.message;
      }
    } catch (e) {
      // ignore
    }
    throw new Error(errorMessage);
  }

  return response.json();
}
