import { FormEvent, useEffect, useRef, useState } from "react";
import { apiUrl, request } from "../../api";
import { MedicationCheck } from "./MedicationCheck";
import { t } from "../../language";

type Entry = {
  id: string;
  external_id: string;
  title: string;
  kind: string;
  version: number;
  occurred_at: string;
  simulated: boolean;
  data: Record<string, unknown>;
  related?: Entry[];
  notes?: { id: string; text: string; occurred_at: string }[];
  media?: { id: string; url: string; mime_type: string }[];
};
type Connection = {
  id: string;
  name: string;
  active: boolean;
  source_url?: string;
  integration_key?: string;
};
export function Records({
  token,
  workspaceId,
  admin,
  canWrite,
}: {
  token: string;
  workspaceId: string;
  admin: boolean;
  canWrite: boolean;
}) {
  const [rows, setRows] = useState<Entry[]>([]),
    [selected, setSelected] = useState<Entry | null>(null),
    [q, setQ] = useState(""),
    [note, setNote] = useState(""),
    [message, setMessage] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const selectedId = useRef("");
  const detailRequest = useRef(0);
  const [attachment, setAttachment] = useState<{
    url: string;
    mime: string;
  } | null>(null);
  useEffect(
    () => () => {
      if (attachment) URL.revokeObjectURL(attachment.url);
    },
    [attachment],
  );
  useEffect(() => {
    setAttachment(null);
  }, [selected?.id, workspaceId]);
  const [connections, setConnections] = useState<Connection[]>([]),
    [name, setName] = useState(""),
    [url, setUrl] = useState(""),
    [sourceToken, setSourceToken] = useState(""),
    [key, setKey] = useState(""),
    [busy, setBusy] = useState(false);
  const base = `/v1/workspaces/${workspaceId}`;
  useEffect(() => {
    let current = true;
    detailRequest.current++;
    selectedId.current = "";
    setSelected(null);
    setBusy(false);
    setRows([]);
    setMessage("");
    if (!workspaceId) return;
    setLoading(true);
    request<Entry[]>(
      `${base}/records?q=${encodeURIComponent(q)}&offset=${offset}`,
      token,
    )
      .then((v) => {
        if (current) setRows(v);
      })
      .catch((e) => {
        if (current) setMessage(e.message);
      })
      .finally(() => {
        if (current) setLoading(false);
      });
    return () => {
      current = false;
      detailRequest.current++;
      selectedId.current = "";
    };
  }, [base, token, q, workspaceId, offset]);
  useEffect(() => {
    let current = true;
    setConnections([]);
    setKey("");
    if (admin)
      request<Connection[]>(`${base}/connections`, token)
        .then((v) => {
          if (current) setConnections(v);
        })
        .catch((e) => {
          if (current) setMessage(e.message);
        });
    return () => {
      current = false;
    };
  }, [base, token, admin]);
  async function open(id: string) {
    const requestId = ++detailRequest.current;
    selectedId.current = id;
    setSelected(null);
    setAttachment(null);
    setNote("");
    setBusy(true);
    try {
      const entry = await request<Entry>(`${base}/records/${id}`, token);
      if (requestId === detailRequest.current) setSelected(entry);
    } catch (e) {
      if (requestId === detailRequest.current) setMessage(String(e));
    } finally {
      if (requestId === detailRequest.current) setBusy(false);
    }
  }
  async function addNote(e: FormEvent) {
    e.preventDefault();
    if (!selected) return;
    setBusy(true);
    try {
      await request(`${base}/records/${selected.id}/notes`, token, {
        method: "POST",
        body: JSON.stringify({
          text: note,
          occurred_at: new Date().toISOString(),
        }),
      });
      if (selectedId.current !== selected.id) return;
      setNote("");
      await open(selected.id);
    } catch (e) {
      if (selectedId.current === selected.id) setMessage(String(e));
    } finally {
      if (selectedId.current === selected.id) setBusy(false);
    }
  }
  async function connect(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const c = await request<Connection>(`${base}/connections`, token, {
        method: "POST",
        body: JSON.stringify({
          name,
          source_url: url || null,
          source_token: sourceToken || null,
        }),
      });
      setConnections([...connections, c]);
      setKey(c.integration_key || "");
      setSourceToken("");
      setName("");
    } catch (e) {
      setMessage(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <section>
      <h1>{t("Workspace records")}</h1>
      <p>
        {t("People, cases and recorded events from your connected sources.")}
      </p>
      <label>
        {t("Search records")}
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOffset(0);
          }}
        />
      </label>
      {message && <p role="status">{message}</p>}
      <div className="record-layout">
        <div>
          {rows.map((r) => (
            <button key={r.id} onClick={() => open(r.id)} disabled={busy}>
              <strong>{r.title}</strong>
              <br />
              {r.kind} · {r.external_id}
              {r.simulated ? " · Simulated" : ""}
            </button>
          ))}
          {loading && <p role="status">{t("Loading…")}</p>}
          {!loading && !rows.length && <p>{t("No records found.")}</p>}
          <nav aria-label={t("Record pages")} className="record-pages">
            <button
              disabled={loading || offset === 0}
              onClick={() => setOffset(Math.max(0, offset - 50))}
            >
              {t("Previous records")}
            </button>
            <button
              disabled={loading || rows.length < 50}
              onClick={() => setOffset(offset + 50)}
            >
              {t("Next records")}
            </button>
          </nav>
        </div>
        {selected && (
          <article>
            <h2>{selected.title}</h2>
            <p>
              {selected.external_id} · v{selected.version} ·{" "}
              {new Date(selected.occurred_at).toLocaleString()}
            </p>
            <dl>
              {Object.entries(selected.data).map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{typeof v === "string" ? v : JSON.stringify(v)}</dd>
                </div>
              ))}
            </dl>
            <h3>{t("Related records")}</h3>
            {selected.related?.map((r) => (
              <button key={r.id} onClick={() => open(r.id)}>
                {r.title}
              </button>
            ))}
            {selected.kind === "person" && (
              <MedicationCheck
                key={selected.id}
                token={token}
                base={base}
                personId={selected.id}
                prescriptions={selected.related || []}
              />
            )}
            <h3>{t("Timeline")}</h3>
            {selected.notes?.map((n) => (
              <p key={n.id}>
                <time>{new Date(n.occurred_at).toLocaleString()}</time>
                <br />
                {n.text}
              </p>
            ))}
            {canWrite && (
              <form onSubmit={addNote}>
                <label>
                  {t("Add note")}
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    required
                    maxLength={10000}
                  />
                </label>
                <button disabled={busy}>{t("Save note")}</button>
              </form>
            )}
            <h3>{t("Attachments")}</h3>
            {selected.media?.map((m) => (
              <button
                key={m.id}
                onClick={async () => {
                  try {
                    const response = await fetch(apiUrl(m.url), {
                      headers: { Authorization: `Bearer ${token}` },
                    });
                    if (!response.ok)
                      throw Error(t("Unable to open attachment"));
                    const blob = await response.blob();
                    if (selectedId.current !== selected.id) return;
                    const objectUrl = URL.createObjectURL(blob);
                    setAttachment({ url: objectUrl, mime: m.mime_type });
                  } catch (e) {
                    setMessage(String(e));
                  }
                }}
              >
                {t("Open attachment")}
              </button>
            ))}
            {attachment &&
              (attachment.mime.startsWith("video/") ? (
                <video
                  src={attachment.url}
                  controls
                  style={{ width: "100%" }}
                />
              ) : (
                <img
                  src={attachment.url}
                  alt={selected.title}
                  style={{ maxWidth: "100%" }}
                />
              ))}
          </article>
        )}
      </div>
      {admin && (
        <details>
          <summary>{t("Connections")}</summary>
          {connections.map((c) => (
            <div key={c.id}>
              <strong>{c.name}</strong> ·{" "}
              {c.active ? t("Active") : t("Revoked")}
              {c.active && c.source_url && (
                <button
                  disabled={busy}
                  onClick={async () => {
                    setBusy(true);
                    try {
                      await request(`${base}/connections/${c.id}/sync`, token, {
                        method: "POST",
                      });
                      setMessage(
                        t(
                          "Import completed. Refresh the records to view changes.",
                        ),
                      );
                    } catch (e) {
                      setMessage(String(e));
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  {t("Sync now")}
                </button>
              )}
            </div>
          ))}
          <form onSubmit={connect}>
            <label>
              {t("Connection name")}
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </label>
            <label>
              {t("Source URL (optional)")}
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                type="url"
              />
            </label>
            <label>
              {t("Source token (optional)")}
              <input
                type="password"
                value={sourceToken}
                onChange={(e) => setSourceToken(e.target.value)}
                autoComplete="off"
              />
            </label>
            <button disabled={busy}>{t("Create connection")}</button>
          </form>
          {key && (
            <p>
              {t("Copy this credential now. It is shown only once.")}
              <code>{key}</code>
              <button onClick={() => setKey("")}>{t("Dismiss")}</button>
            </p>
          )}
        </details>
      )}
    </section>
  );
}
