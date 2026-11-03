import { t } from "../../language";
import { FormEvent, useState } from "react";
import { request, type Tokens } from "../../api";

export function Login({ onLogin }: { onLogin: (tokens: Tokens) => void }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      const response = await request<Tokens>(`/v1/auth/${mode}`, undefined, {
        method: "POST",
        body: JSON.stringify({ email, password, username, display_name: name }),
      });
      if (mode === "login") {
        localStorage.setItem("realityos.tokens", JSON.stringify(response));
        onLogin(response);
      } else {
        setMessage(t("Check your email to continue."));
        setPassword("");
      }
    } catch (reason) {
      setMessage(
        reason instanceof Error ? reason.message : t("Sign-in failed."),
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login">
      <form onSubmit={submit}>
        <p className="eyebrow">RealityOS</p>
        <h1>
          {t(
            mode === "login"
              ? "Sign in"
              : mode === "register"
                ? "Create account"
                : "Recover access",
          )}
        </h1>
        {mode === "register" && (
          <>
            <label>
              {t("Name")}
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                maxLength={160}
              />
            </label>
            <label>
              {t("Username")}
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                pattern="[a-zA-Z][a-zA-Z0-9_.-]{2,63}"
                required
                autoComplete="username"
              />
            </label>
          </>
        )}
        <label>
          {t(mode === "login" ? "Username or email" : "Email")}
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type={mode === "login" ? "text" : "email"}
            autoComplete="username"
            required
          />
        </label>
        {(mode === "login" || mode === "register") && (
          <label>
            {t("Password")}
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              autoComplete={
                mode === "register" ? "new-password" : "current-password"
              }
              minLength={mode === "register" ? 12 : 1}
              maxLength={512}
              required
            />
          </label>
        )}
        {message && <p role="status">{message}</p>}
        <button disabled={busy} className="primary">
          {t(busy ? "Loading…" : "Continue")}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => {
            setMode(mode === "register" ? "login" : "register");
            setMessage("");
          }}
        >
          {t(mode === "register" ? "Sign in" : "Create account")}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => setMode("forgot-password")}
        >
          {t("Recover password")}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => setMode("resend-confirmation")}
        >
          {t("Resend confirmation")}
        </button>
        {mode !== "login" && (
          <button
            type="button"
            disabled={busy}
            onClick={() => setMode("login")}
          >
            {t("Sign in")}
          </button>
        )}
      </form>
    </main>
  );
}
