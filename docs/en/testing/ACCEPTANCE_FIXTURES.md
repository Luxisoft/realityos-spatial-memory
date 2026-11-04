[Español](../../es/testing/ACCEPTANCE_FIXTURES.md) · [RealityOS](../README.md) · [Index](../INDEX.md)

# Synthetic acceptance fixtures

These fixtures support [the manual acceptance checklist](IMPLEMENTATION_CHECKLIST.md) and [the camera cards](QA_VISUAL_FIXTURES.md).

- `cv-v1.pdf`: one-page synthetic CV, role **Inventory assistant**.
- `cv-v2.pdf`: replacement CV, role **Equipment coordinator**.
- Both PDFs contain only fictional QA text, use the standard Helvetica PDF font, and were generated locally without external personal data.
- Camera cards reuse existing synthetic images in `simulator/media/regression/`; no new portraits or customer media are introduced.
- Runtime account credentials, IDs and execution evidence remain under ignored `.runtime/`. Local Postman examples derive their account and resource IDs from an isolated SQL-initialized database; no credentials are published.

Do not overwrite existing execution results when starting another run. Archive the private run log and record the new APK hash, local code revision and date.
