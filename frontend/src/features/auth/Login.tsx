import { t } from "../../language";
import { FormEvent, useState } from "react";
import { request, type Tokens } from "../../api";

export function Login({ onLogin }: { onLogin: (tokens: Tokens) => void }) {
  const [email, setEmail] = useState("admin@realityos.local");
  const [password, setPassword] = useState("ChangeMeNow123!");
  const [error, setError] = useState("");
  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const tokens = await request<Tokens>("/v1/auth/login", undefined, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("realityos.tokens", JSON.stringify(tokens));
      onLogin(tokens);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : t("Sign-in failed."));
    }
  }
  return (
    <main className="login">
      <form onSubmit={submit}>
        <p className="eyebrow">{t("REALITYOS / SECURE ACCESS")}</p>
        <h1>{t("Find the evidence.")}</h1>
        <p>
          {t("Query recorded observations; this screen never starts capture.")}
        </p>
        <label>
          {t("Email")}
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            type="email"
            required
          />
        </label>
        <label>
          {t("Password")}
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="primary">{t("Enter workspace")}</button>
      </form>
    </main>
  );
}
