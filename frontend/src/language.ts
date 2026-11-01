import { useEffect, useState, useSyncExternalStore } from "react";
import { translations } from "./translations";

export type Language = "en" | "es";
type TextKey = keyof typeof translations;
const base = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
let selected: Language =
  localStorage.getItem("realityos.language") === "es" ? "es" : "en";
let revision = 0;
let activeToken = "";
let queue: Promise<unknown> = Promise.resolve();
const listeners = new Set<() => void>();

export function languageTag(): Language {
  return selected;
}
export function languageRevision(): number {
  return revision;
}
export function t(
  key: TextKey,
  values: Record<string, string | number> = {},
): string {
  const text: string = selected === "es" ? translations[key] : key;
  return text.replace(/\{(\w+)\}/g, (match, name: string) =>
    String(values[name] ?? match),
  );
}
export function formatDate(value: string): string {
  return new Intl.DateTimeFormat(selected, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}
export function displayError(status?: number): string {
  return t(
    status === 401
      ? "Your session expired. Sign in again."
      : status === 403
        ? "You do not have permission for this action."
        : "Could not complete the request.",
  );
}
function publish(language: Language) {
  document.documentElement.lang = language;
  if (selected === language) return;
  selected = language;
  revision += 1;
  localStorage.setItem("realityos.language", language);
  stopLocalizedSpeech();
  listeners.forEach((listener) => listener());
}
function serialize<T>(work: () => Promise<T>): Promise<T> {
  const next = queue.then(work, work);
  queue = next.catch(() => undefined);
  return next;
}
async function preference(
  token: string,
  language?: Language,
  initialize = false,
): Promise<Language | null> {
  const response = await fetch(
    `${base}/v1/me/preferences${initialize ? "?initialize=true" : ""}`,
    {
      method: language ? "PATCH" : "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      ...(language
        ? { body: JSON.stringify({ preferred_language: language }) }
        : {}),
    },
  );
  if (!response.ok) throw new Error(displayError(response.status));
  const value = (await response.json()).preferred_language;
  if (value !== null && value !== "en" && value !== "es")
    throw new Error(displayError());
  return value;
}
export function requestLanguage(token: string): Promise<Language> {
  return serialize(async () => {
    const remote =
      (await preference(token)) ?? (await preference(token, selected, true));
    if (!remote) throw new Error(displayError());
    if (token === activeToken) publish(remote);
    return remote;
  });
}
export function useSelectedLanguage(): Language {
  return useSyncExternalStore((listener) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  }, languageTag);
}
export function useLanguage(token: string) {
  const language = useSelectedLanguage();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    stopLocalizedSpeech();
    activeToken = token;
    document.documentElement.lang = selected;
    let mounted = true;
    const sync = () => {
      if (token)
        requestLanguage(token).catch(() => {
          if (mounted)
            setError(t("Could not save the language. Please try again."));
        });
    };
    sync();
    window.addEventListener("focus", sync);
    return () => {
      mounted = false;
      if (activeToken === token) {
        activeToken = "";
        stopLocalizedSpeech();
      }
      window.removeEventListener("focus", sync);
    };
  }, [token]);
  async function save(next: Language) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      if (!token) publish(next);
      else
        await serialize(async () => {
          const confirmed = await preference(token, next);
          if (confirmed && token === activeToken) publish(confirmed);
        });
    } catch {
      setError(t("Could not save the language. Please try again."));
    } finally {
      setBusy(false);
    }
  }
  return { language, save, busy, error };
}
let speechGeneration = 0;
let pendingSpeech: AbortController | null = null;
let activeAudio: HTMLAudioElement | null = null;
let activeAudioUrl = "";

export function stopLocalizedSpeech(): void {
  speechGeneration += 1;
  pendingSpeech?.abort();
  pendingSpeech = null;
  activeAudio?.pause();
  activeAudio = null;
  if (activeAudioUrl) URL.revokeObjectURL(activeAudioUrl);
  activeAudioUrl = "";
  window.speechSynthesis?.cancel();
}

export function speakLocalized(
  text: string,
  language: Language,
  onUnavailable: (message: string) => void,
): void {
  if (language !== selected || !text.trim()) return;
  stopLocalizedSpeech();
  const generation = speechGeneration;
  const token = activeToken;
  const current = () =>
    generation === speechGeneration &&
    language === selected &&
    token === activeToken;
  if (!token) {
    speakDeviceVoice(text, language, onUnavailable, current);
    return;
  }
  const controller = new AbortController();
  pendingSpeech = controller;
  let timedOut = false;
  let fallbackUsed = false;
  const fallback = () => {
    if (!current() || fallbackUsed) return;
    fallbackUsed = true;
    activeAudio?.pause();
    activeAudio = null;
    if (activeAudioUrl) URL.revokeObjectURL(activeAudioUrl);
    activeAudioUrl = "";
    onUnavailable(t("Using this device's voice for this response."));
    speakDeviceVoice(text, language, onUnavailable, current);
  };
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, 33000);
  void (async () => {
    try {
      const response = await fetch(`${base}/v1/tts`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text, language }),
        signal: controller.signal,
      });
      if (!current()) return;
      if (response.status === 401 || response.status === 403) {
        onUnavailable(displayError(response.status));
        return;
      }
      if (
        !response.ok ||
        !response.headers.get("content-type")?.startsWith("audio/wav")
      )
        throw new Error("Speech unavailable");
      const blob = await response.blob();
      if (!current()) return;
      if (!blob.size || blob.size > 16 * 1024 * 1024)
        throw new Error("Invalid audio");
      activeAudioUrl = URL.createObjectURL(blob);
      const audio = new Audio(activeAudioUrl);
      activeAudio = audio;
      audio.onended = () => {
        if (current()) stopLocalizedSpeech();
      };
      audio.onerror = fallback;
      await audio.play();
    } catch {
      if (!controller.signal.aborted || timedOut) fallback();
    } finally {
      clearTimeout(timer);
      if (pendingSpeech === controller) pendingSpeech = null;
    }
  })();
}

function speakDeviceVoice(
  text: string,
  language: Language,
  onUnavailable: (message: string) => void,
  current: () => boolean,
): void {
  if (!current()) return;
  if (!("speechSynthesis" in window)) {
    onUnavailable(
      t("The selected language voice is unavailable on this device."),
    );
    return;
  }
  const synth = window.speechSynthesis;
  synth.cancel();
  const started = revision;
  void (async () => {
    if (synth.getVoices().length === 0) {
      await new Promise<void>((resolve) => {
        const loaded = () => {
          clearTimeout(timer);
          synth.removeEventListener("voiceschanged", loaded);
          resolve();
        };
        const timer = setTimeout(loaded, 1500);
        synth.addEventListener("voiceschanged", loaded);
      });
    }
    if (!current() || revision !== started || selected !== language) return;
    const voice = synth
      .getVoices()
      .find((item) => item.lang.toLowerCase().split(/[-_]/)[0] === language);
    if (!voice) {
      onUnavailable(
        t("The selected language voice is unavailable on this device."),
      );
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    utterance.voice = voice;
    utterance.onerror = () => {
      if (current() && revision === started)
        onUnavailable(
          t("The selected language voice is unavailable on this device."),
        );
    };
    synth.speak(utterance);
  })();
}

const systemLabels: Record<string, keyof typeof translations> = {
  brand: "Brand",
  manufacturer: "Manufacturer",
  model: "Model",
  product_line: "Product line",
  visible_text: "Visible text",
  color: "Color",
  condition: "Condition",
  usage_state: "Usage state",
  packaging: "Packaging",
  visible_count: "Visible count",
  pending: "Pending",
  verified: "Verified",
  rejected: "Rejected",
  active: "Active",
  revoked: "Revoked",
  room: "Room",
  building: "Building",
  shelf: "Shelf",
  level: "Level",
  area: "Area",
  bin: "Bin",
};
export function systemLabel(value: string): string {
  return systemLabels[value] ? t(systemLabels[value]) : value;
}
