import { t, type Language, type useLanguage } from "./language";

export function LanguagePicker({
  preference,
}: {
  preference: ReturnType<typeof useLanguage>;
}) {
  return (
    <div className="language-picker">
      <label>
        {t("Language")}{" "}
        <select
          aria-label={t("Language")}
          value={preference.language}
          disabled={preference.busy}
          onChange={(event) =>
            void preference.save(event.target.value as Language)
          }
        >
          <option value="en">English</option>
          <option value="es">Español</option>
        </select>
      </label>
      {preference.error && <span role="alert">{preference.error}</span>}
    </div>
  );
}
