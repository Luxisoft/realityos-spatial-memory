export type Tokens = { access_token: string; refresh_token: string };
export type Workspace = { id: string; name: string; description?: string; role: string };
export type Zone = { id: string; name: string; kind: string; parent_id?: string | null };
export type TrackedObject = { id: string; canonical_name: string; category?: string | null; attributes: Record<string, unknown> };
export type Observation = {
  id: string;
  media_asset_id: string;
  seen_at: string;
  visual_confidence: number;
  spatial_description?: string | null;
  verification_status: string;
};
export type ObjectFact = {
  id: string;
  fact_type: string;
  value_text?: string | null;
  normalized_value?: string | null;
  numeric_value?: number | null;
  unit?: string | null;
  confidence: number;
  provenance: string;
  verification_status: string;
};
export type Device = {
  id: string;
  workspace_id: string;
  device_identifier: string;
  label: string;
  status: "active" | "revoked";
  last_seen_at?: string | null;
  revoked_at?: string | null;
  metadata: Record<string, unknown>;
};
export type DeviceEnrollment = Device & { device_key: string };
export type DeviceAssignment = {
  id: string;
  device_id: string;
  operator_label: string;
  external_reference?: string | null;
  effective_from: string;
  effective_to?: string | null;
  notice_version: string;
};
export type InventoryAnalytics = {
  workspace_id: string;
  verified_object_count: number;
  provisional_fact_count: number;
  brands: { value: string; count: number }[];
  categories: { value: string; count: number }[];
  conditions: { value: string; count: number }[];
  usage_states: { value: string; count: number }[];
  devices: { label: string; device_id: string; capture_sessions: number }[];
};
export type QueryResult = {
  found: boolean;
  ambiguous: boolean;
  message: string;
  media_id?: string;
  highlighted_media_url?: string;
  highlight_quality: "sam_mask" | "approximate_box" | "none";
  segmentation_status: "not_requested" | "queued" | "processing" | "ready" | "no_match" | "failed";
  segmentation_job_id?: string;
  can_refine: boolean;
  retrieval_confidence?: number;
  simulated: boolean;
  zone_path: string[];
  tts_text: string;
  object?: { canonical_name: string };
  observation?: { id: string; seen_at: string; visual_confidence: number };
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
