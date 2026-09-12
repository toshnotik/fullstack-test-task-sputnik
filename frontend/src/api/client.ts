export const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

export async function request<T>(path: string, init: RequestInit, errorMessage: string): Promise<T> {
  const response = await fetch(buildApiUrl(path), init);

  if (!response.ok) {
    throw new Error(errorMessage);
  }

  return (await response.json()) as T;
}
