import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { apiUrl, request, type QueryResult, type Tokens, type Workspace, type Zone } from "./api";
import "./styles.css";

type Page = "inicio" | "registrar" | "consultar";

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
        <p className="rail-label">MEMORIA ESPACIAL</p>
        {(["inicio", "registrar", "consultar"] as Page[]).map((item) => (
          <button className={page === item ? "nav active" : "nav"} key={item} onClick={() => setPage(item)}>
            {item}
          </button>
        ))}
        <button className="nav logout" onClick={logout}>Cerrar sesión</button>
      </aside>
      <section className="workspace">
        <header className="topline">
          <div>
            <p className="eyebrow">ESPACIO AUTORIZADO</p>
            <select value={workspaceId} onChange={(event) => setWorkspaceId(event.target.value)}>
              <option value="">Selecciona un espacio</option>
              {workspaces.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </div>
          <div className="mode-pill"><i /> {page === "registrar" ? "REGISTRAR · ESCRITURA" : "CONSULTAR · SOLO LECTURA"}</div>
        </header>
        {error && <p className="error">{error}</p>}
        {page === "inicio" && <Home workspace={workspace} onRegister={() => setPage("registrar")} onQuery={() => setPage("consultar")} />}
        {page === "registrar" && <Register workspaceId={workspaceId} token={token} />}
        {page === "consultar" && <Query workspaceId={workspaceId} token={token} />}
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
      setError(reason instanceof Error ? reason.message : "No se pudo iniciar sesión.");
    }
  }
  return <main className="login"><form onSubmit={submit}>
    <p className="eyebrow">REALITYOS / ACCESO SEGURO</p><h1>Encuentra la evidencia.</h1>
    <p>Consulta observaciones registradas; nunca se inicia una captura desde esta pantalla.</p>
    <label>Correo<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required /></label>
    <label>Contraseña<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" required /></label>
    {error && <p className="error">{error}</p>}<button className="primary">Entrar al espacio</button>
  </form></main>;
}

function Home({ workspace, onRegister, onQuery }: { workspace?: Workspace; onRegister: () => void; onQuery: () => void }) {
  return <section className="hero">
    <p className="eyebrow">PANEL DE EVIDENCIA</p><h1>{workspace?.name ?? "Selecciona un espacio"}</h1>
    <p className="lead">Dos acciones, dos permisos: captura deliberada para actualizar la memoria o lectura de evidencia ya guardada.</p>
    <div className="action-grid">
      <button className="action-card" onClick={onRegister}><span>01</span><strong>Registrar una observación</strong><small>Abre una sesión, carga una foto y procesa la evidencia.</small></button>
      <button className="action-card evidence" onClick={onQuery}><span>02</span><strong>Consultar la memoria</strong><small>Busca la última evidencia verificada. No activa la cámara.</small></button>
    </div>
  </section>;
}

function Register({ workspaceId, token }: { workspaceId: string; token: string }) {
  const [zones, setZones] = useState<Zone[]>([]);
  const [zoneId, setZoneId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("Elige una ubicación y una foto para iniciar una captura explícita.");
  useEffect(() => {
    if (!workspaceId) return;
    request<Zone[]>(`/v1/workspaces/${workspaceId}/zones`, token).then(setZones).catch((error: Error) => setStatus(error.message));
  }, [workspaceId, token]);
  async function capture(event: FormEvent) {
    event.preventDefault();
    if (!workspaceId || !file) return setStatus("Selecciona un espacio y una imagen.");
    try {
      setStatus("Abriendo sesión de captura…");
      const session = await request<{ id: string }>("/v1/sessions", token, { method: "POST", body: JSON.stringify({ workspace_id: workspaceId, zone_id: zoneId || null, consent_confirmed: true }) });
      const body = new FormData(); body.append("session_id", session.id); body.append("file", file);
      const capture = await request<{ id: string }>("/v1/captures", token, { method: "POST", body });
      const job = await request<{ id: string }> (`/v1/captures/${capture.id}/process`, token, { method: "POST" });
      await request(`/v1/sessions/${session.id}/close`, token, { method: "POST" });
      setStatus(`Captura guardada en PostgreSQL. Trabajo ${job.id.slice(0, 8)} en cola.`);
    } catch (reason) { setStatus(reason instanceof Error ? reason.message : "No se pudo registrar."); }
  }
  return <section className="panel"><p className="eyebrow">REGISTRAR / CONSENTIMIENTO ACTIVO</p><h1>Nueva evidencia visual</h1>
    <form className="capture-form" onSubmit={capture}><label>Ubicación<select value={zoneId} onChange={(event) => setZoneId(event.target.value)}><option value="">Sin detalle de ubicación</option>{zones.map((zone) => <option key={zone.id} value={zone.id}>{zone.name}</option>)}</select></label>
    <label className="dropzone">Fotografía original<input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event: ChangeEvent<HTMLInputElement>) => setFile(event.target.files?.[0] ?? null)} required /><strong>{file?.name ?? "Seleccionar imagen"}</strong><small>JPEG, PNG o WebP · la fuente de verdad se guarda como BYTEA.</small></label>
    <button className="primary">Guardar y procesar</button></form><p className="status">{status}</p></section>;
}

function Query({ workspaceId, token }: { workspaceId: string; token: string }) {
  const [question, setQuestion] = useState("¿Dónde está el taladro amarillo?");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [imageUrl, setImageUrl] = useState("");
  useEffect(() => {
    if (!result?.highlighted_media_url) { setImageUrl(""); return; }
    let objectUrl = "";
    fetch(apiUrl(result.highlighted_media_url), { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => response.ok ? response.blob() : Promise.reject(new Error("No se pudo recuperar la evidencia.")))
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
  return <section className="panel query"><p className="eyebrow">CONSULTAR / SOLO LECTURA</p><h1>¿Qué estás buscando?</h1>
    <form className="search" onSubmit={ask}><input value={question} onChange={(event) => setQuestion(event.target.value)} aria-label="Pregunta sobre un objeto" /><button className="primary" disabled={busy}>{busy ? "Buscando…" : "Buscar evidencia"}</button></form>
    {result && <article className="result"><div className="evidence-plate">{result.found && <img src={imageUrl} alt={`Evidencia de ${result.object?.canonical_name ?? "objeto"}`} />}<span>BYTEA / EVIDENCIA {result.simulated ? "SIMULADA" : "VERIFICADA"}</span></div>
      <div><p className="eyebrow">{result.found ? "ÚLTIMA OBSERVACIÓN" : result.ambiguous ? "AMBIGÜEDAD" : "SIN EVIDENCIA"}</p><h2>{result.object?.canonical_name ?? "No confirmado"}</h2><p>{result.message}</p>
      {result.found && <dl><div><dt>Ubicación</dt><dd>{result.zone_path.join(" · ")}</dd></div><div><dt>Confianza visual</dt><dd>{Math.round((result.retrieval_confidence ?? 0) * 100)}%</dd></div></dl>}
      <button className="voice" onClick={speak} disabled={!result.found || !("speechSynthesis" in window)}>Escuchar respuesta</button></div>
    </article>}</section>;
}

createRoot(document.getElementById("root")!).render(<App />);
