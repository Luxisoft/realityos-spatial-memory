import {
  t,
  useLanguage,
  requestLanguage,
  languageTag,
  languageRevision,
  speakLocalized,
  stopLocalizedSpeech,
  displayError,
} from "./language";
import { LanguagePicker } from "./LanguagePicker";
import { FormEvent, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const api = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
type Tokens = { access_token: string };
type Workspace = { id: string; name: string };
type Result = {
  response_language: "en" | "es";
  found: boolean;
  message: string;
  tts_text: string;
  highlighted_media_url?: string;
  highlight_quality?: "sam_mask" | "approximate_box" | "none";
  object?: { canonical_name: string };
  zone_path: string[];
  simulated: boolean;
};

async function call<T>(
  path: string,
  token?: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  const response = await fetch(`${api}${path}`, { ...init, headers });
  if (!response.ok) throw new Error(displayError(response.status));
  return response.json() as Promise<T>;
}

function Display() {
  const [token, setToken] = useState(
    () => localStorage.getItem("realityos.display.token") ?? "",
  );
  const preference = useLanguage(token);
  const [email, setEmail] = useState("admin@realityos.local");
  const [password, setPassword] = useState("ChangeMeNow123!");
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspace, setWorkspace] = useState("");
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [image, setImage] = useState("");
  const [notice, setNotice] = useState("");
  const requestVersion = useRef(0);
  const context = `${token}\u0000${workspace}`;
  const activeContext = useRef(context);
  activeContext.current = context;
  useEffect(
    () => () => {
      requestVersion.current += 1;
      stopLocalizedSpeech();
    },
    [],
  );
  useEffect(() => {
    if (token)
      call<Workspace[]>("/v1/workspaces", token)
        .then((items) => {
          setWorkspaces(items);
          setWorkspace(items[0]?.id ?? "");
        })
        .catch((error: Error) => setNotice(error.message));
  }, [token]);
  useEffect(() => {
    if (!result?.highlighted_media_url) {
      setImage("");
      return;
    }
    let active = true;
    let url = "";
    fetch(`${api}${result.highlighted_media_url}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => {
        if (!r.ok) throw new Error(displayError(r.status));
        return r.blob();
      })
      .then((blob) => {
        if (!active) return;
        url = URL.createObjectURL(blob);
        setImage(url);
      })
      .catch(() => {
        if (active) setImage("");
      });
    return () => {
      active = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [result, token]);
  async function login(event: FormEvent) {
    event.preventDefault();
    try {
      const value = await call<Tokens>("/v1/auth/login", undefined, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("realityos.display.token", value.access_token);
      setToken(value.access_token);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : t("Unavailable"));
    }
  }
  useEffect(() => {
    stopLocalizedSpeech();
    setResult(null);
    setImage("");
    setNotice("");
  }, [preference.language, token, workspace]);
  async function search(event: FormEvent) {
    event.preventDefault();
    stopLocalizedSpeech();
    if (!workspace || question.trim().length < 2) return;
    const version = ++requestVersion.current;
    let revision = languageRevision();
    const current = () =>
      version === requestVersion.current &&
      context === activeContext.current &&
      revision === languageRevision();
    setNotice("");
    try {
      const language = await requestLanguage(token);
      revision = languageRevision();
      if (!current()) return;
      const response = await call<Result>("/v1/queries", token, {
        method: "POST",
        body: JSON.stringify({ workspace_id: workspace, question, language }),
      });
      if (current() && response.response_language === languageTag())
        setResult(response);
    } catch (error) {
      if (current())
        setNotice(error instanceof Error ? error.message : t("Unavailable"));
    }
  }
  function speak() {
    if (result)
      speakLocalized(result.tts_text, result.response_language, setNotice);
  }
  if (!token)
    return (
      <main className="screen login">
        <LanguagePicker preference={preference} />
        <p>REALITYOS</p>
        <h1>{t("Spatial memory")}</h1>
        <form onSubmit={login}>
          <input
            aria-label={t("Email")}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            aria-label={t("Password")}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button>{t("Enter")}</button>
        </form>
        {notice && <small>{notice}</small>}
      </main>
    );
  return (
    <main className="screen">
      <header>
        <LanguagePicker preference={preference} />
        <b>R/OS</b>
        <span>{t("QUERY · NO RECORDING")}</span>
      </header>
      <form className="question" onSubmit={search}>
        <select
          value={workspace}
          onChange={(e) => setWorkspace(e.target.value)}
        >
          {workspaces.map((item) => (
            <option value={item.id} key={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          aria-label={t("Object query")}
          placeholder={t("Where is the yellow drill?")}
        />
        <button disabled={question.trim().length < 2}>{t("Search")}</button>
      </form>
      {result && (
        <section className="answer">
          <div className="photo">
            {image && <img src={image} alt={t("Highlighted object")} />}
            <em>
              {result.simulated
                ? t("SIMULATED")
                : result.highlight_quality === "sam_mask"
                  ? t("SAM MASK")
                  : t("APPROXIMATE BOX")}
            </em>
          </div>
          <h1>{result.object?.canonical_name ?? t("No match")}</h1>
          <p>{result.message}</p>
          {result.found && <small>{result.zone_path.join(" · ")}</small>}
          {result.tts_text && (
            <>
              <button className="listen" onClick={speak}>
                {t("Listen")}
              </button>
              <button className="listen" onClick={stopLocalizedSpeech}>
                {t("Stop audio")}
              </button>
            </>
          )}
        </section>
      )}
      {notice && <small>{notice}</small>}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<Display />);
