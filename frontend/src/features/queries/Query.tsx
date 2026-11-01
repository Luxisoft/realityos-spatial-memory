import {
  t,
  languageTag,
  languageRevision,
  requestLanguage,
  speakLocalized,
  stopLocalizedSpeech,
  useSelectedLanguage,
} from "../../language";
import { FormEvent, useEffect, useRef, useState } from "react";
import { apiUrl, request, type QueryResult } from "../../api";

export function Query({
  workspaceId,
  token,
}: {
  workspaceId: string;
  token: string;
}) {
  const selectedLanguage = useSelectedLanguage();
  const requestVersion = useRef(0);
  const context = `${token}\u0000${workspaceId}`;
  const activeContext = useRef(context);
  activeContext.current = context;
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [imageUrl, setImageUrl] = useState("");
  const [refining, setRefining] = useState(false);
  const [refinementMessage, setRefinementMessage] = useState("");
  useEffect(() => {
    stopLocalizedSpeech();
    setResult(null);
    setRefinementMessage("");
    setBusy(false);
    setRefining(false);
  }, [selectedLanguage, token, workspaceId]);
  useEffect(
    () => () => {
      requestVersion.current += 1;
      stopLocalizedSpeech();
    },
    [],
  );
  useEffect(() => {
    if (!result?.highlighted_media_url) {
      setImageUrl("");
      return;
    }
    let objectUrl = "";
    let active = true;
    fetch(apiUrl(result.highlighted_media_url), {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((response) =>
        response.ok
          ? response.blob()
          : Promise.reject(new Error(t("Evidence could not be retrieved."))),
      )
      .then((blob) => {
        if (!active) return;
        objectUrl = URL.createObjectURL(blob);
        setImageUrl(objectUrl);
      })
      .catch(() => {
        if (active) setImageUrl("");
      });
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [result, token]);
  async function ask(event: FormEvent) {
    event.preventDefault();
    stopLocalizedSpeech();
    if (!workspaceId || question.trim().length < 2) return;
    const version = ++requestVersion.current;
    let revision = languageRevision();
    const current = () =>
      version === requestVersion.current &&
      context === activeContext.current &&
      revision === languageRevision();
    setBusy(true);
    setRefinementMessage("");
    try {
      const language = await requestLanguage(token);
      revision = languageRevision();
      if (!current()) return;
      const response = await request<QueryResult>("/v1/queries", token, {
        method: "POST",
        body: JSON.stringify({ workspace_id: workspaceId, question, language }),
      });
      if (current() && response.response_language === languageTag())
        setResult(response);
    } catch {
      if (current()) setRefinementMessage(t("Could not complete the request."));
    } finally {
      if (current()) setBusy(false);
    }
  }
  async function refine() {
    if (!result?.observation?.id) return;
    const observationId = result.observation.id;
    const version = requestVersion.current;
    const revision = languageRevision();
    const active = () =>
      version === requestVersion.current &&
      context === activeContext.current &&
      revision === languageRevision();
    setRefining(true);
    setRefinementMessage("");
    try {
      type Job = {
        id: string;
        status: string;
        error_message?: string;
        result_metadata?: { segmentation_status?: string };
      };
      let job = await request<Job>(
        `/v1/observations/${observationId}/segment`,
        token,
        { method: "POST" },
      );
      if (!active()) return;
      setResult((current) =>
        current?.observation?.id === observationId
          ? {
              ...current,
              segmentation_status:
                job.status === "completed"
                  ? job.result_metadata?.segmentation_status === "no_match"
                    ? "no_match"
                    : "ready"
                  : "queued",
              segmentation_job_id: job.id,
              can_refine: false,
            }
          : current,
      );
      for (
        let attempt = 0;
        job.status === "queued" || job.status === "processing";
        attempt += 1
      ) {
        if (attempt >= 30) {
          setRefinementMessage(
            t(
              "SAM refinement {id} is still running. You can return to this evidence later.",
              { id: job.id.slice(0, 8) },
            ),
          );
          return;
        }
        await new Promise((resolve) => window.setTimeout(resolve, 1000));
        job = await request<Job>(`/v1/jobs/${job.id}`, token);
        if (!active()) return;
      }
      if (job.status === "completed") {
        const noMatch = job.result_metadata?.segmentation_status === "no_match";
        setResult((current) =>
          current?.observation?.id === observationId
            ? {
                ...current,
                segmentation_status: noMatch ? "no_match" : "ready",
                highlight_quality: noMatch ? "approximate_box" : "sam_mask",
                can_refine: false,
              }
            : current,
        );
        setRefinementMessage(
          noMatch
            ? t(
                "SAM found no matching pixels; the approximate Muse Spark box remains available.",
              )
            : t("SAM mask cached and applied to this evidence."),
        );
      } else {
        setResult((current) =>
          current?.observation?.id === observationId
            ? { ...current, segmentation_status: "failed", can_refine: true }
            : current,
        );
        setRefinementMessage(t("SAM refinement failed; no mask was stored."));
      }
    } catch (reason) {
      if (!active()) return;
      setRefinementMessage(
        reason instanceof Error
          ? reason.message
          : t("Unable to queue SAM refinement."),
      );
    } finally {
      if (active()) setRefining(false);
    }
  }
  function speak() {
    if (result?.tts_text)
      speakLocalized(
        result.tts_text,
        result.response_language,
        setRefinementMessage,
      );
  }

  return (
    <section className="panel query">
      <p className="eyebrow">{t("QUERY / READ ONLY")}</p>
      <h1>{t("What are you looking for?")}</h1>
      <form className="search" onSubmit={ask}>
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          aria-label={t("Object query")}
          placeholder={t("Where is the yellow drill?")}
        />
        <button
          className="primary"
          disabled={busy || question.trim().length < 2}
        >
          {busy ? t("Searching…") : t("Find evidence")}
        </button>
      </form>
      {result && (
        <article className="result">
          <div className="evidence-plate">
            {result.found && (
              <img
                src={imageUrl}
                alt={t("Evidence of {name}", {
                  name: result.object?.canonical_name ?? "",
                })}
              />
            )}
            <span>
              {t("BYTEA /")} {result.simulated ? t("SIMULATED") : t("VERIFIED")}
              {t("EVIDENCE")}
            </span>
          </div>
          <div>
            <p className="eyebrow">
              {result.found
                ? t("LAST OBSERVATION")
                : result.ambiguous
                  ? t("AMBIGUITY")
                  : t("NO EVIDENCE")}
            </p>
            <h2>{result.object?.canonical_name ?? t("Not confirmed")}</h2>
            <p>{result.message}</p>
            {result.found && (
              <dl>
                <div>
                  <dt>{t("Location")}</dt>
                  <dd>{result.zone_path.join(" · ")}</dd>
                </div>
                <div>
                  <dt>{t("Visual confidence")}</dt>
                  <dd>
                    {Math.round((result.retrieval_confidence ?? 0) * 100)}%
                  </dd>
                </div>
              </dl>
            )}
            {result.found && (
              <p className="geometry-status">
                {result.highlight_quality === "sam_mask"
                  ? t("SAM 3.1 mask cached")
                  : result.highlight_quality === "approximate_box"
                    ? t("Approximate Muse Spark box")
                    : t("No visual geometry available")}
              </p>
            )}
            {result.found && result.can_refine && (
              <button className="refine" onClick={refine} disabled={refining}>
                {refining
                  ? t("Queuing refinement…")
                  : t("Refine with SAM 3.1 · ≈ US$0.0025")}
              </button>
            )}
            {result.found && result.segmentation_status === "queued" && (
              <p className="geometry-status">
                {t(
                  "SAM refinement is queued. This query did not start capture.",
                )}
              </p>
            )}
            <button
              className="voice"
              onClick={speak}
              disabled={!result.tts_text}
            >
              {t("Listen to answer")}
            </button>
            <button className="voice" onClick={stopLocalizedSpeech}>
              {t("Stop audio")}
            </button>
          </div>
        </article>
      )}
      {refinementMessage && (
        <p className="status" role="status">
          {refinementMessage}
        </p>
      )}
    </section>
  );
}
