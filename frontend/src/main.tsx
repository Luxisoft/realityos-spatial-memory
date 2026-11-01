import { t, useLanguage } from "./language";
import { LanguagePicker } from "./LanguagePicker";
import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { request, type Tokens, type Workspace } from "./api";
import { LocationMap, Objects } from "./explorer";
import { DeviceRegistry, InventoryIntelligence } from "./operations";
import { Login } from "./features/auth/Login";
import { Home } from "./features/home/Home";
import { Register } from "./features/captures/Register";
import { Query } from "./features/queries/Query";

import "./styles.css";

type Page =
  | "inicio"
  | "registrar"
  | "consultar"
  | "objetos"
  | "mapa"
  | "inteligencia"
  | "dispositivos";

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
  const preference = useLanguage(token);
  const pages: { id: Page; label: string }[] = [
    { id: "inicio", label: t("Home") },
    { id: "registrar", label: t("Register") },
    { id: "consultar", label: t("Query") },
    { id: "objetos", label: t("Objects") },
    { id: "mapa", label: t("Map") },
    { id: "inteligencia", label: t("Intelligence") },
    { id: "dispositivos", label: t("Devices") },
  ];
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
    return (
      <>
        <LanguagePicker preference={preference} />
        <Login onLogin={setTokens} />
      </>
    );
  }

  const workspace = workspaces.find((item) => item.id === workspaceId);
  return (
    <main className="shell">
      <aside className="rail">
        <a
          className="wordmark"
          href="#"
          onClick={(event) => event.preventDefault()}
        >
          <span>Reality</span>OS
        </a>
        <p className="rail-label">{t("SPATIAL MEMORY")}</p>
        {pages.map((item) => (
          <button
            className={page === item.id ? "nav active" : "nav"}
            key={item.id}
            onClick={() => setPage(item.id)}
          >
            {item.label}
          </button>
        ))}
        <button className="nav logout" onClick={logout}>
          {t("Sign out")}
        </button>
      </aside>
      <section className="workspace">
        <header className="topline">
          <LanguagePicker preference={preference} />
          <div>
            <p className="eyebrow">{t("AUTHORIZED WORKSPACE")}</p>
            <select
              value={workspaceId}
              onChange={(event) => setWorkspaceId(event.target.value)}
            >
              <option value="">{t("Select a workspace")}</option>
              {workspaces.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </div>
          <div className="mode-pill">
            <i />{" "}
            {page === "registrar"
              ? t("REGISTER · WRITE")
              : t("QUERY · READ ONLY")}
          </div>
        </header>
        {error && <p className="error">{error}</p>}
        {page === "inicio" && (
          <Home
            workspace={workspace}
            onRegister={() => setPage("registrar")}
            onQuery={() => setPage("consultar")}
          />
        )}
        {page === "registrar" && (
          <Register workspaceId={workspaceId} token={token} />
        )}
        {page === "consultar" && (
          <Query workspaceId={workspaceId} token={token} />
        )}
        {page === "objetos" && (
          <Objects workspaceId={workspaceId} token={token} />
        )}
        {page === "mapa" && (
          <LocationMap workspaceId={workspaceId} token={token} />
        )}
        {page === "inteligencia" && (
          <InventoryIntelligence workspaceId={workspaceId} token={token} />
        )}
        {page === "dispositivos" && (
          <DeviceRegistry workspaceId={workspaceId} token={token} />
        )}
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
