<p align="center">
  <a href="HACKATHON.md"><img src="assets/readme/language-en-active.svg" alt="English — selected" height="32"></a>
  <a href="HACKATHON.es.md"><img src="assets/readme/language-es.svg" alt="Leer en español" height="32"></a>
</p>

# RealityOS — hackathon delivery

[← Project](../README.md) · [Demo walkthrough](DEMO.md) · [Technical status](IMPLEMENTATION_STATUS.md)

## Project pitch

RealityOS connects what a person sees with information they can retrieve: facial recognition leading to authorized profiles and person records, contextual questions and traceable visual memory. Android and native Meta glasses Display expose image, video, text and voice input. Police, nursing, social and memory workflows demonstrate different applications of these components.

**Proposed theme:** *Build for Your World*. This is a suggested fit, not a claim about the registered category. Track and team details must match the team's registration. [Official event](https://cerebralvalley.ai/e/meta-ai-developer-hackathon)

## Evidence against the criteria

Weights come from [Meta and Cerebral Valley's official rules](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver), checked **November 3, 2026**.

| Criterion | What the project demonstrates | Where to inspect it |
| --- | --- | --- |
| Impact · 30% | Connects person, context and evidence across four concrete workflows. | [Use cases](../README.md#cases) and [evaluation steps](DEMO.md). No unmeasured impact metrics are claimed. |
| Meta AI tooling · 25% | Muse Spark interprets images/context, SAM localizes evidence and Muse Voice Transcribe processes speech; DAT connects glasses. | [Meta contracts](META_INTEGRATION.md), [providers](../backend/app/providers/) and [Android](../android/README.md). InsightFace and ElevenLabs are identified separately. |
| Technical depth · 20% | BYTEA, workspace permissions, explicit enrollment, versioned imports, idempotent workers and persisted evidence. | [Architecture](ARCHITECTURE.md), [API](API.md), [tests](../tests/) and [automated runs](https://github.com/Luxisoft/realityos-spatial-memory/actions/workflows/ci.yml). |
| Demo · 25% | Installable APK, accounts, synthetic data and a walkthrough with inspectable results. | [Walkthrough](DEMO.md). Existing concept videos do not replace a final recording of working software. |

## Delivery material and status

| Item | Repository status |
| --- | --- |
| Explanation and code access | EN/ES README, diagrams and public repository under Apache 2.0. |
| What was built | [Public history](https://github.com/Luxisoft/realityos-spatial-memory/commits/main/), starting October 26, 2026, and [implementation log](IMPLEMENTATION_STATUS.md). Third-party models, SDKs and dependencies are not claimed as team inventions. |
| Installation and evaluator access | [APK/build](../android/README.md#build), demo accounts and server/Windows guides. Demo passwords accompany invitations; service keys stay private. |
| Working demo and video | Walkthrough prepared; a public link to the final product recording is still missing. The header is a graphic simulation. |
| Team and track | Confirm the representative, members and registered selection. The rules provide for one team submission in one track. |
| Sources and rights | [Apache 2.0](../LICENSE) project code, synthetic fixtures and [graphics provenance](assets/readme/PROMPTS.md). The project license does not replace model/SDK/component licenses. |
| Submission receipt | No portal submission receipt is recorded in the repository. Publishing to GitHub does not submit the entry. |

The public page sets the deadline at **November 4, 2026, 9:00 PM ET** (9:00 PM in Bogotá). The [submission portal](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit) is separate from GitHub. [Official schedule](https://cerebralvalley.ai/e/meta-ai-developer-hackathon)

## Scope of this review

The public event page and rules were checked. The [detailed participant guide](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details) redirects to sign-in; its additional requirements, form fields and exact video duration/format **remain unverified**. Complete that review with the participant account before submitting. This mapping does not assert eligibility or full compliance.

Documented technical checks do not replace physical phone/glasses validation, a real institutional integration or representative recognition evaluation. The clinical comparator checks explicit fields; it does not prescribe. Police fixture coverage is explained in the [walkthrough](DEMO.md).

[← Project](../README.md) · [Español](HACKATHON.es.md)
