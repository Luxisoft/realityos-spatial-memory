import { t } from "../../language";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { request, type Zone } from "../../api";

export function Register({
  workspaceId,
  token,
}: {
  workspaceId: string;
  token: string;
}) {
  const [zones, setZones] = useState<Zone[]>([]);
  const [zoneId, setZoneId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [profile, setProfile] = useState<"basic" | "detailed">("basic");
  const [priorityTerms, setPriorityTerms] = useState("");
  const [status, setStatus] = useState(
    t("Choose a location and media file to start an explicit capture."),
  );
  useEffect(() => {
    if (!workspaceId) return;
    request<Zone[]>(`/v1/workspaces/${workspaceId}/zones`, token)
      .then(setZones)
      .catch((error: Error) => setStatus(error.message));
  }, [workspaceId, token]);
  async function capture(event: FormEvent) {
    event.preventDefault();
    if (!workspaceId || !file)
      return setStatus(t("Select a workspace and a media file."));
    try {
      setStatus(t("Opening capture session…"));
      const session = await request<{ id: string }>("/v1/sessions", token, {
        method: "POST",
        body: JSON.stringify({
          workspace_id: workspaceId,
          zone_id: zoneId || null,
          consent_confirmed: true,
        }),
      });
      const body = new FormData();
      body.append("session_id", session.id);
      body.append("file", file);
      const capture = await request<{ id: string }>("/v1/captures", token, {
        method: "POST",
        body,
      });
      const job = await request<{ id: string }>(
        `/v1/captures/${capture.id}/process`,
        token,
        {
          method: "POST",
          body: JSON.stringify({
            profile,
            priority_terms: priorityTerms
              .split(",")
              .map((term) => term.trim())
              .filter(Boolean),
          }),
        },
      );
      await request(`/v1/sessions/${session.id}/close`, token, {
        method: "POST",
      });
      setStatus(
        t("Capture stored in PostgreSQL. Job {id} is queued.", {
          id: job.id.slice(0, 8),
        }),
      );
    } catch (reason) {
      setStatus(
        reason instanceof Error ? reason.message : t("Registration failed."),
      );
    }
  }
  return (
    <section className="panel">
      <p className="eyebrow">{t("REGISTER / CONSENT ACTIVE")}</p>
      <h1>{t("New visual evidence")}</h1>
      <form className="capture-form" onSubmit={capture}>
        <label>
          {t("Location")}
          <select
            value={zoneId}
            onChange={(event) => setZoneId(event.target.value)}
          >
            <option value="">{t("No location detail")}</option>
            {zones.map((zone) => (
              <option key={zone.id} value={zone.id}>
                {zone.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          {t("Processing profile")}
          <select
            value={profile}
            onChange={(event) =>
              setProfile(event.target.value as "basic" | "detailed")
            }
          >
            <option value="basic">{t("Basic · Muse Spark catalog")}</option>
            <option value="detailed">
              {t("Detailed · priority tracking")}
            </option>
          </select>
        </label>
        {profile === "detailed" && (
          <label>
            {t("Priority object terms")}
            <input
              value={priorityTerms}
              onChange={(event) => setPriorityTerms(event.target.value)}
              placeholder="yellow drill, battery charger"
            />
            <small>
              {t(
                "Detailed tracking is an explicit paid processing request. Separate terms with commas.",
              )}
            </small>
          </label>
        )}
        <label className="dropzone">
          {t("Original evidence")}
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm"
            onChange={(event: ChangeEvent<HTMLInputElement>) =>
              setFile(event.target.files?.[0] ?? null)
            }
            required
          />
          <strong>{file?.name ?? t("Select a file")}</strong>
          <small>
            {t(
              "JPEG, PNG, WebP or MP4/MOV/WebM video · BYTEA is the source of truth.",
            )}
          </small>
        </label>
        <button className="primary">{t("Store and process")}</button>
      </form>
      <p className="status">{status}</p>
    </section>
  );
}
