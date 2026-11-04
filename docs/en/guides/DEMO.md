<p align="center">
  <a href="DEMO.md"><img src="../../assets/readme/language-en-active.svg" alt="English — selected" height="32"></a>
  <a href="../../es/guides/DEMO.md"><img src="../../assets/readme/language-es.svg" alt="Leer en español" height="32"></a>
</p>

# Evaluation walkthroughs

> Localhost is the current walkthrough. Historical results below describe the server and do not validate the new local installation.


**[Operational acceptance checklist](../testing/IMPLEMENTATION_CHECKLIST.md)** · [Camera-ready visual cards](../testing/QA_VISUAL_FIXTURES.md). Record manual tests and technical evidence per release before closing the submission.

These walkthroughs are independent examples of RealityOS capabilities. They are not a sequence across organizations or an exhaustive list of uses. Each test uses its own workspace's data and permissions.

[← Project](../README.md) · [Hackathon delivery](../project/HACKATHON.md) · [Android](../integrations/ANDROID.md)

The new object tests use [12 complete videos with ES/EN queries and evidence intervals](../testing/VIDEO_EVALUATION.md). The matrix states what to search for and what result to verify.

<a id="handoff"></a>
<a id="access"></a>

## Local access

Start Docker using the [local guide](../deployment/DEPLOYMENT_LOCALHOST.md), install the local APK and connect the phone with `adb reverse tcp:8080 tcp:8080`. Choose one of the nine accounts. No password, Facebook or bucket is needed. Starting data is fictional and public; Meta models use your own key. Consent and enrollment must be performed explicitly to test face search.


## Local jury access

The three scenarios now use local account selection without passwords. The server catalog is disabled. Follow the [API guide](../api/API.md#quick-start).


## 1. Police: case, person and evidence

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | In Work, select Pacific Ridge → Workspace records → case 1. | Source, version, related event and attachments. |
| 2 | Read shift notes and open the evidence image. | Original media and context in the selected workspace. |
| 3 | Search for the yellow flashlight or red screwdriver. | Highlighted evidence, source and last-observed date. |
| 4 | Open a shift post and check its author and group. | An existing post linked to the police workspace. |

The included police fixture contains cases, events and objects, without enrolled person records. The six prepared portraits are in nursing and memory. Automatic police alerts and a real institutional data connection remain pending. [Concept video](../../../demo-video/policial_case.mp4)

## 2. Nursing: prepared record → comparison

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | In Work, select California Valley Medical Center → Workspace records → Ana Solis. | A prepared record with its portrait, opened inside the app. |
| 2 | Open the portrait and return to the related records. | Ana's encounter, prescription and notes, with sources and dates. |
| 3 | Enter the observed fixture fields, including **20 mg**, against the fictional **10 mg** prescription. Confirm identity and time in the form. | Concentration mismatch with a prescription reference. |
| 4 | Inspect Robert Lane and Fatima Nasser. | Robert's related allergy and Fatima's previous administration, with dates and source. |

The comparator uses explicitly entered fields: it does not read packages automatically, calculate doses, prescribe or record administrations. Clinical verification remains with the professional. [Concept video](../../../demo-video/nurse_case.mp4)

## 3. Prepared profile and posts

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | In Profile, check your test account name and photo. | A prepared profile with its own avatar. |
| 2 | Open one of your posts. | A scenario photo or video with its author and group. |
| 3 | Return to Work and browse the group's posts. | Content shared by the scenario's three workers. |
| 4 | To compare scenarios, sign out and use another account supplied by the organizer. | Each account opens its own group and retains its permissions. |

The synthetic directory is independent; it does not imply all its accounts are available to every evaluator. Facebook references stay within their authorized flows; this is not global Facebook face search. [Concept video](../../../demo-video/profile_found.mp4)

## 4. Memory: person, reminder and last observation

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | In Work, select Sonoran Neurological Institute → Workspace records → Luis Moreno. | An authorized record with its portrait already attached. |
| 2 | Open his related reminder and event. | Stored context, dates, notes and source. |
| 3 | Ask where the documents, brass keys or blue notebook were last seen. | A highlighted photo/frame, location and last-observed date. |
| 4 | Ask for an object with no evidence. | No match or insufficient evidence; no invented location. |

The feature retrieves recorded information; it does not diagnose or treat memory conditions. “Last seen” does not mean “still there”. [Concept video](../../../demo-video/memory.mp4)

Face search is an additional test with explicit capture and its own permissions and consent. Having an avatar or opening a record does not automatically enroll an account. The organizer prepares any facial demonstration separately.

<a id="video"></a>

## Record the three-minute demo

**Final recording link: pending.** The guide requires an accessible three-minute video highlighting only features built during the Hackathon. Identify the [existing baseline and new contributions](../project/HACKATHON.md#contributions); concept videos are supporting material.

| Time | What to show in the product | Evidence |
| --- | --- | --- |
| 0:00–0:15 | Problem, scope and what was added during the event. | Distinguish the existing baseline from the features about to be demonstrated. |
| 0:15–1:15 | Authorized workspace, test portrait, facial candidate and record opening. | Consent, evidence and similarity; human confirmation of the candidate. |
| 1:15–1:50 | Record notes, relationships and attachments. | Source, version and queryable context. |
| 1:50–2:25 | SAM refinement and video evidence added during the event. | Frame, geometry and last-observed date; original object lookup belongs to the baseline. |
| 2:25–2:45 | Android/DAT interaction that can actually run. | Identify phone, physical glasses or simulator; label any simulation. |
| 2:45–3:00 | A permission boundary and the contribution breakdown. | Restricted resource, public code link and commits. |

Rehearse before recording. Choose a workspace with prepared data and hide secrets, notifications and unrelated information. Do not present a conceptual scene as a real execution or claim a physical-glasses test when only the phone was used. Verify that the final link opens without requesting access and add it to the README and submission.

| Documented evidence | Pending |
| --- | --- |
| Six portraits enrolled through the API; Ana Solis query with live InsightFace. | Evaluation with independent portraits and representative data. |
| HTTP imports, contextual queries, object search and permission tests. | A real institutional source and complete journeys on physical phone/glasses. |
| 48 licensed scene resources with real moving recordings. | A final product recording accessible to evaluators. |

[Implementation status](../project/IMPLEMENTATION_STATUS.md) records dated checks. This document describes the walkthrough; it does not claim a new execution of those journeys.

[← Project](../README.md) · [Español](../../es/guides/DEMO.md)
