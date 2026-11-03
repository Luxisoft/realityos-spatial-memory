<p align="center">
  <a href="HACKATHON.md"><img src="../../assets/readme/language-en-active.svg" alt="English — selected" height="32"></a>
  <a href="../../es/project/HACKATHON.md"><img src="../../assets/readme/language-es.svg" alt="Leer en español" height="32"></a>
</p>

# Submission requirements and review

**[Operational acceptance checklist](../testing/IMPLEMENTATION_CHECKLIST.md)** · [Camera-ready visual cards](../testing/QA_VISUAL_FIXTURES.md). Record manual tests and technical evidence per release before closing the submission.

[← Project](../README.md) · [Demo walkthrough](../guides/DEMO.md) · [Technical status](IMPLEMENTATION_STATUS.md)

**Source:** the complete participant guide supplied by the owner on November 3, 2026, published at [Event Details](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details), and the [official rules](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver). The guide does not mandate a README template. This review organizes evaluator evidence and distinguishes participation, submission and documentation requirements.

## Requirements and evidence

| Guide requirement | Evidence / status |
| --- | --- |
| Address one problem statement | **Documented fit:** Build for Your World, through reusable recognition, context and memory capabilities. The four scenarios are independent examples. Confirm the registered category. |
| Incorporate Meta models | **Implemented:** Muse Spark 1.3, SAM 3.1 and Muse Voice Transcribe, with [contracts](../integrations/META_INTEGRATION.md) and [providers](../../../backend/app/providers/). DAT is the glasses interface; InsightFace and ElevenLabs are separate components. The guide does not require using every listed model. |
| Public / open-source repository | **Verified:** GitHub reports `PUBLIC` and [Apache 2.0](../../../LICENSE). Dependencies retain their own terms. |
| New work and identifiable contributions | **Breakdown below.** A baseline predates the stated building period; the entire repository is not presented as new. |
| Accessible three-minute video | **Pending:** a real recording focused on event contributions. Concept videos alone do not satisfy this evidence. [180-second script](../guides/DEMO.md#video). |
| At most four participants; representative and all contributors declared | **Registration details pending.** Team membership is not inferred from Git authors, and private information is not published. |
| Accepted, eligible participants; rules accepted | **Check registration:** acceptance, geographic/sanctions restrictions, excluded affiliations and acceptance of the rules. The repository cannot establish these personal eligibility conditions. |
| One team project and one track | **Confirm in CV:** Indie Developer or Startups; no selection is invented. |
| Submit by November 4, 9:00 PM EST | **Receipt pending:** [CV portal](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit). Also 9:00 PM in Bogotá. A GitHub push does not submit the entry. |
| Usage rights and policy compliance | **Review open:** see exclusions and licenses below. Full compliance is not asserted. |

The guide separates an initial viability/Meta-use gate, scoring from 0–10 and a final round for five projects per track. The supplied text omits the scoring table; weights previously published in the rules are impact 30%, Meta tooling 25%, technical depth 20% and demo 25%. Evidence is linked through [capabilities and models](../README.md#architecture), [tests](../../../tests/) and [dated validations](IMPLEMENTATION_STATUS.md).

<a id="contributions"></a>

## Baseline and event contributions

The guide places kickoff on **October 26** and building on **October 27–November 4**. This review conservatively uses the latter interval, converting dates to **America/New_York (ET)**. Git timestamps locate contributions; they do not independently prove when each line was written or establish eligibility.

| Part | Reviewable reference | Presentation |
| --- | --- | --- |
| Baseline through October 26, 11:49 PM ET | [`3ab8c63`](https://github.com/Luxisoft/realityos-spatial-memory/commit/3ab8c63) | Initial platform, object capture/query, deployment, gateway and search already present. Identify as baseline. |
| Bounded video from October 27, 12:01 AM ET | [`5bb0607`](https://github.com/Luxisoft/realityos-spatial-memory/commit/5bb0607) | New video capability; the commit reads October 26, 11:01 PM in Bogotá, which is already October 27 in ET. |
| Segmentation and glasses, October 27 ET | [`a35c9ac`](https://github.com/Luxisoft/realityos-spatial-memory/commit/a35c9ac) · [`8babc43`](https://github.com/Luxisoft/realityos-spatial-memory/commit/8babc43) | SAM refinement and Android/DAT host with capture and voice. |
| Biometrics, social and localization, November 1 ET commit | [`052471e`](https://github.com/Luxisoft/realityos-spatial-memory/commit/052471e) | Consent/enrollment/face search, profiles and social experience. The commit groups work; the technical log records its validations. |
| Records and person-record face search, November 2 ET | [`7f5f79d`](https://github.com/Luxisoft/realityos-spatial-memory/commit/7f5f79d) · [`99a83e0`](https://github.com/Luxisoft/realityos-spatial-memory/commit/99a83e0) | Versioned records, relationships, attachments and explicit portrait-to-record links. |

[Baseline-to-reviewed-state comparison](https://github.com/Luxisoft/realityos-spatial-memory/compare/3ab8c63...5e6fd89). The demo must identify concrete additions; using the baseline to run them does not make it new work. The guide permits existing products for startups; this project's track and an organizer determination on the kickoff/building boundary are not recorded.

## Excluded-project review

| Exclusion | Review finding |
| --- | --- |
| AI-generated medical advice | The [comparator](../../../backend/app/workspaces/clinical.py) checks fields without a model call, requires professional review and records no administration. [Contextual search](../../../backend/app/workspaces/search.py) instructs the model not to prescribe or authorize medication. This does not establish that every generated answer is safe: the actual clinical demo outputs still need review. Present record retrieval and discrepancies without therapeutic advice. |
| Basic RAG or simple image analysis | Implementations include face enrollment, persisted visual evidence, segmentation, DAT capture and versioned integrations. Demonstrate those implementations; prose or an isolated chat does not replace technical evidence. Admission remains the judges' decision. |
| Simple education chatbot; job screening; nutrition; personality; sports | These are not the presented capabilities. An authorized profile or CV is not described as personality evaluation or employment screening. |
| Politics or war | The documented examples are not political or military. Police casework describes authorized records and evidence, not criminal prediction or automated decisions. |
| Legal, ethical or platform-policy violations | Workspace controls, consent and human-confirmed candidates exist. They do not establish organizer/provider approval; confirm applicable terms, especially for biometrics and glasses. |
| Code, data or assets without usage rights | See provenance and license review below. A complete transitive-component audit is not closed. |

<a id="rights"></a>

## Provenance and licenses

- **Project code:** [Apache 2.0](../../../LICENSE). Third-party models and SDKs are not original team contributions.
- **InsightFace:** code is MIT, while downloaded weights have separate non-commercial research conditions. The [Dockerfile](../../../backend/Dockerfile) includes `buffalo_l`; the reviewed documentation contains no record of an additional license. Confirm submission/deployment rights rather than assuming Apache/MIT covers them. [Provider source](https://github.com/deepinsight/insightface#license).
- **DAT:** its [license](https://github.com/meta/meta-wearables-dat-android/blob/main/LICENSE) refers to developer terms and acceptable use. The [policy](https://wearables.developer.meta.com/acceptable-use-policy) requires sign-in in this review; account-based verification remains pending.
- **Graphics and data:** [prompts and provenance](GRAPHICS.md), [synthetic directory](../testing/SOCIAL_DIRECTORY.md) and [workspace fixtures](../guides/WORKSPACE_DATA.md). Graphics are conceptual and contain no real patients or records. Generation provenance is not blanket permission for trademarks or third-party resources; verify video provenance before submission too.

**Outstanding:** three-minute recording, team/track, actual demo-output review, model rights and applicable terms, and submission receipt. Documentation is prepared to review these items; full eligibility or approval is not claimed.

[← Project](../README.md) · [Español](../../es/project/HACKATHON.md)
