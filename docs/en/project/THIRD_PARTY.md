[Español](../../es/project/THIRD_PARTY.md) · [Index](../INDEX.md) · [Submission](HACKATHON.md#rights)

# Third parties, assets and usage rights

Reviewed on **November 3, 2026**. Project-owned code remains under [Apache 2.0](../../../LICENSE). That license does not change third-party SDK, model, service or asset terms. This review identifies conditions and available evidence; it does not attest to private agreements that have not been supplied.

## Verifiable inventory

The [dependency inventory](../../assets/legal/dependency-inventory.json) records **93 Python packages** and **210 Android dependencies**, with versions, declared license metadata and hashes of local evidence. Python covers the installed host environment's runtime and `faces` dependency closure; Android covers `debugRuntimeClasspath`, including transitive components and Mock Device Kit. Inherited parent POM licenses were also resolved.

This inventory is a snapshot of the identified environment, not a version lockfile. It does not independently certify every deployed image, system library or future build. Publishing the approved APK and other binaries requires retaining applicable notices and license texts; the inventory links their sources and does not replace them.

## Components and conditions

| Component | Verified use and condition | Review result |
| --- | --- | --- |
| InsightFace 0.7.3 code | Server-side face detection and comparison; MIT metadata. [Provider](https://github.com/deepinsight/insightface#license). | Identified; preserve MIT notices. |
| `buffalo_l` weights | The [Dockerfile](../../../backend/Dockerfile) downloads these weights. The provider distinguishes models from code, limits downloaded models to noncommercial research, and gives a recognition-model licensing contact. | **Authorization for this use is not established.** Hackathon participation, public source code or charging no fee does not automatically establish that condition. Record applicable authorization or an assessment of the specific use. |
| Meta DAT 1.0.1 | Core, Camera, Display and Speech; Mock Device Kit only in Debug. The [SDK license](https://github.com/meta/meta-wearables-dat-android/blob/main/LICENSE) incorporates [developer terms](https://wearables.developer.meta.com/terms) and [acceptable use policy](https://wearables.developer.meta.com/acceptable-use-policy). | **Authenticated text and acceptance evidence are outstanding.** Both pages requested login. SDK access does not establish permission for biometric uses. |
| `meta-sam-parser` 0.1.0 | SAM protocol parser; its metadata includes the [SAM License](https://github.com/meta-models/meta-sam/blob/main/LICENSE). | Identified. Retain the agreement when redistributing materials and acknowledge use in published results; review use restrictions. Meta API access also has account-specific conditions. |
| Facebook Android SDK 18.1.3 | Facebook login and authorized flows. [Facebook Platform License](https://github.com/meta/facebook-android-sdk/blob/main/LICENSE.txt). | Identified. Use in connection with Facebook services/APIs, notice preservation and platform policies apply. It is not presented as MIT/Apache software. |
| ONNX Runtime and Python/Android libraries | Inference, HTTP, processing and UI. The inventory distinguishes MIT, Apache, BSD, LGPL, MPL and composite licenses. | Metadata inventoried. Obligations depend on each component and distributed artifact; not everything is Apache-licensed. |
| Muse, SAM and Transcribe APIs | Meta services called from the server. | A working key does not establish permission for every use. Retain the terms governing event access. |
| ElevenLabs | Synthesis through the project's account. [Service terms](https://elevenlabs.io/terms-of-use). | Output use depends on that account's terms and plan. Record with an authorized voice and retain evidence of usage rights. |

## Asset provenance

| Assets | Evidence and scope |
| --- | --- |
| Headers, thumbnails and Android illustrations | [Graphics and prompts](GRAPHICS.md). Documented synthetic generation; they do not depict real records or patients. |
| Scenarios and test media | [Workspace data](../guides/WORKSPACE_DATA.md), [social directory](../testing/SOCIAL_DIRECTORY.md) and the organized [media manifest](../../../simulator/media/manifest.csv). The manifest preserves source, license, hash and fixture path. Versioned SQL initializes local database rows; preparation does not upload to remote storage. |
| Historical R2 evaluation copies | Earlier private execution receipts retain source and hash verification. They are historical evidence, not the active local dataset or authorization for new uploads. |
| Concept videos under `demo-video/` | They remain labeled conceptual. No generation/license manifest was found alongside those four files; their contributor must confirm provenance and track rights if they are included in the submission. The final recording is a separate deliverable. |
| Final app recordings | Use prepared synthetic data and authorized media. Clinical outputs and visible data are reviewed during acceptance and demo recording. |

## Evidence needed to close usage rights

1. **InsightFace:** applicable `buffalo_l` authorization or use assessment, rights holder, permitted use and date. The provider lists `recognition-oss-pack@insightface.ai` for these models. No communication has been sent on the owner's behalf.
2. **DAT:** the terms and policy version or copy available through the project's Meta account, plus evidence of acceptance/applicability to the presented use.
3. **Final material:** confirm concept-video provenance if reused, voice terms and permission for external assets included in the recording. Record this when completing the video.

Keep private agreements, correspondence and confirmations in `.runtime/rights-evidence/`; publish only a nonsensitive conclusion and reference. The documentary review is complete. Authorization closure awaits that evidence; the biometric feature has not been modified or disabled.
