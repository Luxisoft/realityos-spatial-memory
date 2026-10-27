export type Tokens = { access_token: string; refresh_token: string };
export type Workspace = { id: string; name: string; description?: string; role: string };
export type Zone = { id: string; name: string; kind: string; parent_id?: string };
export type QueryResult = {
  found: boolean;
  ambiguous: boolean;
  message: string;
  media_id?: string;
  highlighted_media_url?: string;
  retrieval_confidence?: number;
  simulated: boolean;
  zone_path: string[];
  tts_text: string;
  object?: { canonical_name: string };
  observation?: { seen_at: string; visual_confidence: number };
};

const origin = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function request<T>(path: string, token?: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(`${origin}${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail ?? `Error ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const apiUrl = (path: string) => `${origin}${path}`;
