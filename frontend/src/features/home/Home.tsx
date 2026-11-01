import { t } from "../../language";
import { type Workspace } from "../../api";

export function Home({
  workspace,
  onRegister,
  onQuery,
}: {
  workspace?: Workspace;
  onRegister: () => void;
  onQuery: () => void;
}) {
  return (
    <section className="hero">
      <p className="eyebrow">{t("EVIDENCE CONSOLE")}</p>
      <h1>{workspace?.name ?? t("Select a workspace")}</h1>
      <p className="lead">
        {t(
          "Two actions, two permissions: deliberate capture updates memory; query reads stored evidence.",
        )}
      </p>
      <div className="action-grid">
        <button className="action-card" onClick={onRegister}>
          <span>01</span>
          <strong>{t("Register an observation")}</strong>
          <small>
            {t("Open a session, upload media and process the evidence.")}
          </small>
        </button>
        <button className="action-card evidence" onClick={onQuery}>
          <span>02</span>
          <strong>{t("Query memory")}</strong>
          <small>
            {t("Find the last verified evidence. It never activates a camera.")}
          </small>
        </button>
      </div>
    </section>
  );
}
