import { FormEvent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const api = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
type Tokens = { access_token: string };
type Workspace = { id: string; name: string };
type Result = { found: boolean; message: string; tts_text: string; highlighted_media_url?: string; object?: { canonical_name: string }; zone_path: string[]; simulated: boolean };

async function call<T>(path: string, token?: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(`${api}${path}`, { ...init, headers });
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail ?? "No disponible");
  return response.json() as Promise<T>;
}

function Display() {
  const [token, setToken] = useState(() => localStorage.getItem("realityos.display.token") ?? "");
  const [email, setEmail] = useState("admin@realityos.local");
  const [password, setPassword] = useState("ChangeMeNow123!");
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspace, setWorkspace] = useState("");
  const [question, setQuestion] = useState("Where is the yellow drill?");
  const [result, setResult] = useState<Result | null>(null);
  const [image, setImage] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => { if (token) call<Workspace[]>("/v1/workspaces", token).then((items) => { setWorkspaces(items); setWorkspace(items[0]?.id ?? ""); }).catch((error: Error) => setNotice(error.message)); }, [token]);
  useEffect(() => {
    if (!result?.highlighted_media_url) return;
    let url = "";
    fetch(`${api}${result.highlighted_media_url}`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => r.blob()).then((blob) => { url = URL.createObjectURL(blob); setImage(url); });
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [result, token]);
  async function login(event: FormEvent) {
    event.preventDefault();
    try { const value = await call<Tokens>("/v1/auth/login", undefined, { method: "POST", body: JSON.stringify({ email, password }) }); localStorage.setItem("realityos.display.token", value.access_token); setToken(value.access_token); } catch (error) { setNotice(error instanceof Error ? error.message : "No disponible"); }
  }
  async function search(event: FormEvent) {
    event.preventDefault();
    try { setResult(await call<Result>("/v1/queries", token, { method: "POST", body: JSON.stringify({ workspace_id: workspace, question }) })); } catch (error) { setNotice(error instanceof Error ? error.message : "No disponible"); }
  }
  function speak() { if (result && "speechSynthesis" in window) speechSynthesis.speak(new SpeechSynthesisUtterance(result.tts_text)); }
  if (!token) return <main className="screen login"><p>REALITYOS</p><h1>Spatial memory</h1><form onSubmit={login}><input aria-label="Email" value={email} onChange={(e) => setEmail(e.target.value)} /><input aria-label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} /><button>Enter</button></form>{notice && <small>{notice}</small>}</main>;
  return <main className="screen"><header><b>R/OS</b><span>QUERY · NO RECORDING</span></header><form className="question" onSubmit={search}><select value={workspace} onChange={(e) => setWorkspace(e.target.value)}>{workspaces.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select><input value={question} onChange={(e) => setQuestion(e.target.value)} /><button>Search</button></form>
    {result && <section className="answer"><div className="photo">{image && <img src={image} alt="Highlighted object" />}<em>{result.simulated ? "SIMULATED" : "EVIDENCE"}</em></div><h1>{result.object?.canonical_name ?? "No match"}</h1><p>{result.message}</p>{result.found && <><small>{result.zone_path.join(" · ")}</small><button className="listen" onClick={speak}>Listen</button></>}</section>}{notice && <small>{notice}</small>}</main>;
}

createRoot(document.getElementById("root")!).render(<Display />);
