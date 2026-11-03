<p align="center"><a href="IMPLEMENTATION_CHECKLIST.md"><img src="assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="IMPLEMENTATION_CHECKLIST.es.md"><img src="assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# Acceptance checks

[← Documentation](README.md) · [API / Postman](API.md)

## Reading guide

| Topic | What to know |
| --- | --- |
| **API and permissions** | Verify authentication, roles, workspace isolation and media access; do not mark passed without execution. |
| **Evidence** | Check BYTEA originals, idempotency, last observation, missing evidence and queries without capture. |
| **Biometrics** | Verify consent, authorization and candidates; synthetic samples do not measure representative accuracy. |
| **Client** | Check EN/ES, loading/errors, permissions, navigation and APK; physical checks require a separate record. |
| **Publication** | Review secrets, links, artifacts, CI result and hackathon requirements. Original checklist retains its historical marks. |

```mermaid
flowchart LR
    N0["Change"] --> N1["Tests"] --> N2["Evidence"] --> N3["Handoff"]
```

## Procedures and evidence

The original reference preserves technical details, examples and dated checks in their source language. Retired-component instructions are historical; use the current installation guides to operate.
[↗ Complete original reference](reference/IMPLEMENTATION_CHECKLIST.legacy.md)
[API ](API.md) · [IMPLEMENTATION STATUS ](IMPLEMENTATION_STATUS.md) · [HACKATHON ](HACKATHON.md)

<details>
<summary>Historical sections</summary>

<a id="checklist-por-fases--realityos"></a>
[↗ checklist-por-fases--realityos](reference/IMPLEMENTATION_CHECKLIST.legacy.md#checklist-por-fases--realityos)

<a id="fase-0--fundaciones"></a>
[↗ fase-0--fundaciones](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-0--fundaciones)

<a id="fase-1--api-persistencia-y-seguridad"></a>
[↗ fase-1--api-persistencia-y-seguridad](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-1--api-persistencia-y-seguridad)

<a id="fase-2--memoria-y-consultas"></a>
[↗ fase-2--memoria-y-consultas](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-2--memoria-y-consultas)

<a id="fase-3--meta-jobs-y-vídeo"></a>
[↗ fase-3--meta-jobs-y-vídeo](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-3--meta-jobs-y-vídeo)

<a id="fase-4--panel-web"></a>
[↗ fase-4--panel-web](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-4--panel-web)

<a id="fase-5--android-y-display"></a>
[↗ fase-5--android-y-display](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-5--android-y-display)

<a id="fase-6--operación-demo-y-entrega"></a>
[↗ fase-6--operación-demo-y-entrega](reference/IMPLEMENTATION_CHECKLIST.legacy.md#fase-6--operación-demo-y-entrega)

<a id="criterios-finales-de-aceptación"></a>
[↗ criterios-finales-de-aceptación](reference/IMPLEMENTATION_CHECKLIST.legacy.md#criterios-finales-de-aceptación)

</details>
