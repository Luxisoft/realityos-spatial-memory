[Español](../../es/testing/ACCEPTANCE_FIXTURES.md) · [RealityOS](../README.md) · [Index](../INDEX.md)

# Synthetic acceptance fixtures

These fixtures support [the manual acceptance checklist](IMPLEMENTATION_CHECKLIST.md) and [the camera cards](QA_VISUAL_FIXTURES.md).

- `cv-v1.pdf`: one-page synthetic CV, role **Inventory assistant**.
- `cv-v2.pdf`: replacement CV, role **Equipment coordinator**.
- Both PDFs contain only fictional QA text, use the standard Helvetica PDF font, and were generated locally without external personal data.
- Camera cards reuse existing synthetic images in `../workspaces/assets/`; no new portraits or customer media are introduced.
- The isolated runtime QA accounts use those images with explicit consent/enrollment for the admin and member only. Reader retains no biometric consent; outsider starts outside the QA group.
- Runtime account credentials, IDs and execution evidence remain under ignored `.runtime/`. The three separately authorized public jury accounts are described in `../postman/jury.json`.

Do not overwrite existing execution results when starting another run. Archive the private run log and record the new APK hash, server release and date.
