import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { apiUrl, request, type QueryResult, type Tokens, type Workspace, type Zone } from "./api";
import { LocationMap, Objects } from "./explorer";
import "./styles.css";

type Page = "inicio" | "registrar" | "consultar" | "objetos" | "mapa";

const pages: { id: Page; label: string }[] = [
  { id: "inicio", label: "Home" },
  { id: "registrar", label: "Register" },
  { id: "consultar", label: "Query" },
  { id: "objetos", label: "Objects" },
  { id: "mapa", label: "Map" },
];

function App() {
  const [tokens, setTokens] = useState<Tokens | null>(() => {
    const stored = localStorage.getItem("realityos.tokens");
    return stored ? (JSON.parse(stored) as Tokens) : null;
  });
  const [page, setPage] = useState<Page>("inicio");
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspaceId, setWorkspaceId] = useState("");
  const [error, setError] = useState("");

  const token = tokens?.access_token ?? "";
  useEffect(() => {
    if (!token) return;
    request<Workspace[]>("/v1/workspaces", token)
      .then((items) => {
        setWorkspaces(items);
        setWorkspaceId((current) => current || items[0]?.id || "");
      })
      .catch((reason: Error) => setError(reason.message));
  }, [token]);

  function logout() {
    localStorage.removeItem("realityos.tokens");
    setTokens(null);
    setWorkspaces([]);
    setWorkspaceId("");
  }

  if (!tokens) {
    return <Login onLogin={setTokens} />;
  }

  const workspace = workspaces.find((item) => item.id === workspaceId);
  return (
    <main className="shell">
      <aside className="rail">
        <a className="wordmark" href="#" onClick={(event) => event.preventDefault()}>
          <span>Reality</span>OS
        </a>
        <p className="rail-label">SPATIAL MEMORY</p>
        {pages.map((item) => (
          <button className={page === item.id ? "nav active" : "nav"} key={item.id} onClick={() => setPage(item.id)}>
            {item.label}
          </button>
        ))}
        <button className="nav logout" onClick={logout}>Sign out</button>
      </aside>
      <section className="workspace">
        <header className="topline">
          <div>
            <p className="eyebrow">AUTHORIZED WORKSPACE</p>
            <select value={workspaceId} onChange={(event) => setWorkspaceId(event.target.value)}>
              <option value="">Select a workspace</option>
              {workspaces.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </div>
          <div className="mode-pill"><i /> {page === "registrar" ? "REGISTER · WRITE" : "QUERY · READ ONLY"}</div>
        </header>
        {error && <p className="error">{error}</p>}
        {page === "inicio" && <Home workspace={workspace} onRegister={() => setPage("registrar")} onQuery={() => setPage("consultar")} />}
        {page === "registrar" && <Register workspaceId={workspaceId} token={token} />}
        {page === "consultar" && <Query workspaceId={workspaceId} token={token} />}
        {page === "objetos" && <Objects workspaceId={workspaceId} token={token} />}
        {page === "mapa" && <LocationMap workspaceId={workspaceId} token={token} />}
      </section>
    </main>
  );
}

function Login({ onLogin }: { onLogin: (tokens: Tokens) => void }) {
  const [email, setEmail] = useState("admin@realityos.local");
  const [password, setPassword] = useState("ChangeMeNow123!");
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const tokens = await request<Tokens>("/v1/auth/login", undefined, { method: "POST", body: JSON.stringify({ email, password }) });
      localStorage.setItem("realityos.tokens", JSON.stringify(tokens));
      onLogin(tokens);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sign-in failed.");
    }
  }
  return <main className="login"><form onSubmit={submit}>
    <p className="eyebrow">REALITYOS / SECURE ACCESS</p><h1>Find the evidence.</h1>
    <p>Query recorded observations; this screen never starts capture.</p>
    <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required /></label>
    <label>Password<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required /></label>
    {error && <p className="error">{error}</p>}<button className="primary">Enter workspace</button>
  </form></main>;
}

function Home({ workspace, onRegister, onQuery }: { workspace?: Workspace; onRegister: () => void; onQuery: () => void }) {
  return <section className="hero">
    <p className="eyebrow">EVIDENCE CONSOLE</p><h1>{workspace?.name ?? "Select a workspace"}</h1>
    <p className="lead">Two actions, two permissions: deliberate capture updates memory; query reads stored evidence.</p>
    <div className="action-grid">
      <button className="action-card" onClick={onRegister}><span>01</span><strong>Register an observation</strong><small>Open a session, upload media and process the evidence.</small></button>
      <button className="action-card evidence" onClick={onQuery}><span>02</span><strong>Query memory</strong><small>Find the last verified evidence. It never activates a camera.</small></button>
    </div>
  </section>;
}

function Register({ workspaceId, token }: { workspaceId: string; token: string }) {
  const [zones, setZones] = useState<Zone[]>([]);
  const [zoneId, setZoneId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("Choose a location and media file to start an explicit capture.");
  useEffect(() => {
    if (!workspaceId) return;
    request<Zone[]>(`/v1/workspaces/${workspaceId}/zones`, token).then(setZones).catch((error: Error) => setStatus(error.message));
  }, [workspaceId, token]);
  async function capture(event: FormEvent) {
    event.preventDefault();
    if (!workspaceId || !file) return setStatus("Select a workspace and a media file.");
    try {
      setStatus("Opening capture session…");
      const session = await request<{ id: string }>("/v1/sessions", token, { method: "POST", body: JSON.stringify({ workspace_id: workspaceId, zone_id: zoneId || null, consent_confirmed: true }) });
      const body = new FormData(); body.append("session_id", session.id); body.append("file", file);
      const capture = await request<{ id: string }>("/v1/captures", token, { method: "POST", body });
      const job = await request<{ id: string }> (`/v1/captures/${capture.id}/process`, token, { method: "POST" });
      await request(`/v1/sessions/${session.id}/close`, token, { method: "POST" });
      setStatus(`Capture stored in PostgreSQL. Job ${job.id.slice(0, 8)} is queued.`);
    } catch (reason) { setStatus(reason instanceof Error ? reason.message : "Registration failed."); }
  }
  return <section className="panel"><p className="eyebrow">REGISTER / CONSENT ACTIVE</p><h1>New visual evidence</h1>
    <form className="capture-form" onSubmit={capture}><label>Location<select value={zoneId} onChange={(event) => setZoneId(event.target.value)}><option value="">No location detail</option>{zones.map((zone) => <option key={zone.id} value={zone.id}>{zone.name}</option>)}</select></label>
    <label className="dropzone">Original evidence<input type="file" accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm" onChange={(event: ChangeEvent<HTMLInputElement>) => setFile(event.target.files?.[0] ?? null)} required /><strong>{file?.name ?? "Select a file"}</strong><small>JPEG, PNG, WebP or MP4/MOV/WebM video · BYTEA is the source of truth.</small></label>
    <button className="primary">Store and process</button></form><p className="status">{status}</p></section>;
}

function Query({ workspaceId, token }: { workspaceId: string; token: string }) {
  const [question, setQuestion] = useState("Where is the yellow drill?");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [imageUrl, setImageUrl] = useState("");
  useEffect(() => {
    if (!result?.highlighted_media_url) { setImageUrl(""); return; }
    let objectUrl = "";
    fetch(apiUrl(result.highlighted_media_url), { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => response.ok ? response.blob() : Promise.reject(new Error("Evidence could not be retrieved.")))
      .then((blob) => { objectUrl = URL.createObjectURL(blob); setImageUrl(objectUrl); })
      .catch(() => setImageUrl(""));
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [result, token]);
  async function ask(event: FormEvent) {
    event.preventDefault(); if (!workspaceId) return;
    setBusy(true);
    try { setResult(await request<QueryResult>("/v1/queries", token, { method: "POST", body: JSON.stringify({ workspace_id: workspaceId, question }) })); }
    finally { setBusy(false); }
  }
  function speak() { if (result?.tts_text && "speechSynthesis" in window) window.speechSynthesis.speak(new SpeechSynthesisUtterance(result.tts_text)); }
  return <section className="panel query"><p className="eyebrow">QUERY / READ ONLY</p><h1>What are you looking for?</h1>
    <form className="search" onSubmit={ask}><input value={question} onChange={(event) => setQuestion(event.target.value)} aria-label="Object query" /><button className="primary" disabled={busy}>{busy ? "Searching…" : "Find evidence"}</button></form>
    {result && <article className="result"><div className="evidence-plate">{result.found && <img src={imageUrl} alt={`Evidence of ${result.object?.canonical_name ?? "object"}`} />}<span>BYTEA / {result.simulated ? "SIMULATED" : "VERIFIED"} EVIDENCE</span></div>
      <div><p className="eyebrow">{result.found ? "LAST OBSERVATION" : result.ambiguous ? "AMBIGUITY" : "NO EVIDENCE"}</p><h2>{result.object?.canonical_name ?? "Not confirmed"}</h2><p>{result.message}</p>
      {result.found && <dl><div><dt>Location</dt><dd>{result.zone_path.join(" · ")}</dd></div><div><dt>Visual confidence</dt><dd>{Math.round((result.retrieval_confidence ?? 0) * 100)}%</dd></div></dl>}
      <button className="voice" onClick={speak} disabled={!result.found || !("speechSynthesis" in window)}>Listen to answer</button></div>
    </article>}</section>;
}

createRoot(document.getElementById("root")!).render(<App />);
