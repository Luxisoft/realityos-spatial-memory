[Español](../../es/project/GRAPHICS.md) · [RealityOS](../README.md) · [Index](../INDEX.md)

# Graphics and provenance

Headers and thumbnails were generated with Codex’s image tool. They depict fictional people and simulated interfaces. The [original logo](../../../android/app/src/main/res/drawable-nodpi/icon_app.png) is preserved. Graphics present the project; executed tests are recorded in [implementation status](IMPLEMENTATION_STATUS.md).

| Asset | Purpose |
| --- | --- |
| [banner-en.png](../../assets/readme/banner-en.png) · [banner-es.png](../../assets/readme/banner-es.png) | Localized header |
| [example-police.png](../../assets/readme/example-police.png) | Police scenario |
| [example-nursing.png](../../assets/readme/example-nursing.png) | Nursing scenario |
| [example-social.png](../../assets/readme/example-social.png) | Authorized profile lookup |
| [example-memory.png](../../assets/readme/example-memory.png) | Memory scenario |
| [face-lookup.svg](../../assets/readme/face-lookup.svg) | Face flow: portrait, representation, authorized index, candidates and context |

Exact prompts are preserved in [HEADER_PROMPTS.json](../../assets/readme/HEADER_PROMPTS.json) and [THUMBNAIL_PROMPTS.json](../../assets/readme/THUMBNAIL_PROMPTS.json). Masters retain their resolution; headers display at up to 896 px wide and thumbnails at up to 160 × 90 px. SVG and Mermaid diagrams remain editable, with localized explanations outside images.

The [README's local diagram](../README.md#architecture) reflects the four services in [local Compose](../../../infrastructure/docker-compose.local.yml), [worker tasks](../../../backend/app/tasks.py) and [installed Android voices](../../../android/app/src/main/java/com/luxisoft/realityos/MainActivity.kt). Thumbnails link to the conceptual videos preserved in `demo-video/`; the profile illustration represents a feature, not a fourth initial group.

Android entry artwork provenance is recorded in [entry/PROMPTS.json](../../assets/entry/PROMPTS.json); it accompanies resources used by the app.

The local account selector uses profile photos, with an [illustrated default avatar](../../../android/app/src/main/res/drawable-nodpi/default_account_avatar.png) when a photo is missing or cannot load. It was generated using the built-in image tool; the exact prompt is recorded in [DEFAULT_AVATAR_PROMPT.json](../../assets/entry/DEFAULT_AVATAR_PROMPT.json).
