<p align="center">
  <a href="DEMO.md"><img src="assets/readme/language-en-active.svg" alt="English — selected" height="32"></a>
  <a href="DEMO.es.md"><img src="assets/readme/language-es.svg" alt="Leer en español" height="32"></a>
</p>

# Evaluation walkthroughs

**Input → candidate or evidence → authorized context → a result the evaluator can inspect.**

[← Project](../README.md) · [Hackathon delivery](HACKATHON.md) · [Android](../android/README.md)

## Prepare

Install the Debug APK and sign in with an invited account. The hosted server has prepared fixtures; local Windows starts empty. Each feature requests its camera, audio, workspace and biometric consent permissions.

| Scenario | Account / workspace | Test data |
| --- | --- | --- |
| Police | `alex-rivera` / Pacific Ridge Police Department | [Manifest](../simulator/workspaces/security.json) |
| Nursing | `elena-marquez` / California Valley Medical Center | [Ana's portrait](../simulator/workspaces/assets/patient-ana.png) · [manifest](../simulator/workspaces/hospital.json) |
| Memory | `noah-brooks` / Sonoran Neurological Institute | [Luis's portrait](../simulator/workspaces/assets/patient-luis.png) · [manifest](../simulator/workspaces/memory.json) |
| Social | Two authorized, enrolled members of the same workspace | [Synthetic directory](../simulator/social-directory/README.md) |

Use the demo password from the invitation. Operators can retrieve it from the private `.runtime/jury-access.json`. Download the portrait to the phone for **Choose photo**. Reusing the enrollment image tests integration; it does not measure accuracy on new people or images.

## 1. Police: case, person and evidence

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | In Work, select Pacific Ridge and open test case 1. | Source, version, related event and attachments. |
| 2 | Read shift notes and open the evidence image. | Original media and context in the selected workspace. |
| 3 | Search for the yellow flashlight or red screwdriver. | Highlighted evidence, source and last-observed date. |
| 4 | To test face→record lookup, first authorize and enroll a fictional person record in the police workspace. Search that portrait. | A candidate linked to the record; the operator confirms the match. |

The included police fixture contains cases, events and objects, without enrolled person records. The six prepared portraits are in nursing and memory. Automatic police alerts and a real institutional data connection remain pending. [Concept video](../demo-video/policial_case.mp4)

## 2. Nursing: face → record → comparison

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | In Find person, select the clinical workspace and Ana Solis's portrait. | A **person-record candidate**, portrait evidence and similarity. |
| 2 | Confirm the candidate and open the record. | Ana's encounter, prescription, notes and related records. |
| 3 | Enter the observed fixture fields, including **20 mg**, against the fictional **10 mg** prescription. Confirm identity and time in the form. | Concentration mismatch with a prescription reference. |
| 4 | Inspect Robert Lane and Fatima Nasser. | Robert's related allergy and Fatima's previous administration, with dates and source. |

The comparator uses explicitly entered fields: it does not read packages automatically, calculate doses, prescribe or record administrations. Clinical verification remains with the professional. [Concept video](../demo-video/nurse_case.mp4)

## 3. Social: face → profile → shared context

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Use two members of the same workspace with consent and enrollment completed. | Each member's authorization and visible profile. |
| 2 | Search the other member with an authorized photo or video. | A **user candidate**, facial evidence and profile link. |
| 3 | Open the profile and ask about information the person has made available. | Authorized context and media; the private CV file is not exposed as a public attachment. |
| 4 | Check restricted media access from an account without permission. | Restricted resources remain inaccessible. |

The synthetic directory is independent; it does not imply all its accounts are available to every evaluator. Facebook references stay within their authorized flows; this is not global Facebook face search. [Concept video](../demo-video/profile_found.mp4)

## 4. Memory: person, reminder and last observation

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Select the memory workspace and search Luis Moreno's portrait. | A candidate linking to his authorized record. |
| 2 | Open his related reminder and event. | Stored context, dates, notes and source. |
| 3 | Ask where the documents, brass keys or blue notebook were last seen. | A highlighted photo/frame, location and last-observed date. |
| 4 | Ask for an object with no evidence. | No match or insufficient evidence; no invented location. |

The feature retrieves recorded information; it does not diagnose or treat memory conditions. “Last seen” does not mean “still there”. [Concept video](../demo-video/memory.mp4)

## Record the product demo

Record Android running: selected workspace, face→record lookup, context and object evidence. Include a no-match case or a permission boundary. Identify whether you use phone preview or physical glasses. Keep concept videos separate from the real recording, and confirm duration/format in the participant portal.

| Documented evidence | Pending |
| --- | --- |
| Six portraits enrolled through the API; Ana Solis query with live InsightFace. | Evaluation with independent portraits and representative data. |
| HTTP imports, contextual queries, object search and permission tests. | A real institutional source and complete journeys on physical phone/glasses. |
| Synthetic images and static-scene MP4s. | A final product recording accessible to evaluators. |

[Implementation status](IMPLEMENTATION_STATUS.md) records dated checks. This document describes the walkthrough; it does not claim a new execution of those journeys.

[← Project](../README.md) · [Español](DEMO.es.md)
