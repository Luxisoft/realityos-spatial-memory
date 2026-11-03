import { FormEvent, useState } from "react";
import { request } from "../../api";
import { t } from "../../language";

export function MedicationCheck({
  token,
  base,
  personId,
  prescriptions,
}: {
  token: string;
  base: string;
  personId: string;
  prescriptions: { id: string; title: string; kind: string }[];
}) {
  const [prescription, setPrescription] = useState(""),
    [ingredient, setIngredient] = useState(""),
    [concentration, setConcentration] = useState(""),
    [confirmed, setConfirmed] = useState(false),
    [result, setResult] = useState<{
      status: string;
      issues: string[];
      missing: string[];
    } | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  function invalidate() {
    setResult(null);
    setError("");
  }
  async function check(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    invalidate();
    try {
      setResult(
        await request(`${base}/records/${personId}/medication-check`, token, {
          method: "POST",
          body: JSON.stringify({
            prescription_id: prescription,
            observed_ingredient: ingredient,
            observed_concentration: concentration,
            patient_confirmed: confirmed,
            checked_at: new Date().toISOString(),
          }),
        }),
      );
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <details>
      <summary>{t("Compare medication fields")}</summary>
      <form onSubmit={check}>
        <label>
          {t("Recorded prescription")}
          <select
            value={prescription}
            disabled={busy}
            onChange={(e) => {
              setPrescription(e.target.value);
              invalidate();
            }}
            required
          >
            <option value="">{t("Select")}</option>
            {prescriptions
              .filter((p) => p.kind === "prescription")
              .map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title}
                </option>
              ))}
          </select>
        </label>
        <label>
          {t("Observed ingredient")}
          <input
            required
            value={ingredient}
            disabled={busy}
            onChange={(e) => {
              setIngredient(e.target.value);
              invalidate();
            }}
          />
        </label>
        <label>
          {t("Observed concentration")}
          <input
            required
            value={concentration}
            disabled={busy}
            onChange={(e) => {
              setConcentration(e.target.value);
              invalidate();
            }}
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={confirmed}
            disabled={busy}
            onChange={(e) => {
              setConfirmed(e.target.checked);
              invalidate();
            }}
          />
          {t("I confirmed the patient identity")}
        </label>
        <button disabled={busy}>{t("Compare")}</button>
      </form>
      {error && <p role="alert">{error}</p>}
      {result && (
        <div role="status">
          <strong>{result.status}</strong>
          <p>{[...result.issues, ...result.missing].join(", ")}</p>
          <p>
            {t(
              "Professional review required. No administration has been recorded.",
            )}
          </p>
        </div>
      )}
    </details>
  );
}
