<p align="center"><a href="IMPLEMENTATION_CHECKLIST.md"><img src="../../assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="../../es/testing/IMPLEMENTATION_CHECKLIST.md"><img src="../../assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# RealityOS manual checklist — acceptance and Hackathon 2026

[← Project](../README.md) · [Camera-ready visual cards](QA_VISUAL_FIXTURES.md) · [Access and scenarios](../guides/DEMO.md#access) · [Postman](../api/API.md#quick-start) · [Submission](../project/HACKATHON.md)

**Start at P01.** Follow P → S → A → C → F → R → M → O → B → G → V → D → U → T → K → H. Test a **physical Android phone and Display with Mock Device Kit**, real email and real Facebook. Point the phone camera at the images open on the computer. Physical glasses and Windows local are outside this run.

## Marking and recording results

Every case starts pending. Mark `[x]` only after performing every step and recording evidence. Previous API checks do not automatically pass screen tests. Do not use “not applicable” to conceal failures or missing preparation.

In a private checklist copy or `.runtime/acceptance-run.csv`, record each ID with **PENDIENTE / APROBADO / FALLIDO / BLOQUEADO** (pending / passed / failed / blocked), timestamp, account, observed result, evidence, issue and retest. For multi-account/language cases, attach each result before passing the ID. Save screenshots/logs in `.runtime/acceptance-evidence/`; never publish tokens, passwords, private email addresses or personal media. Spreadsheet columns:

```csv
id,estado,fecha_hora,cuenta,resultado,evidencia,incidencia,repeticion
A01,PENDIENTE,,,,,,
```

| Run identification | Complete before passing |
| --- | --- |
| Tester and date / timezone | — |
| Phone and Android version | — |
| Initial / second language | ES / EN (test both) |
| APK full version, build date, SHA-256 | —; 0.1.6 alone does not distinguish builds |
| Commit / backend release / contract | — |
| Display | Mock Device Kit, phone camera and microphone |
| User-reported history | APK installed; build identity to be corroborated in P01 |

## Prepared accounts and data

The three primary accounts and their passwords are in the [public access table](../api/API.md#quick-start), published with owner authorization. The remaining six accounts and four QA accounts are supplied in the private `.runtime/accesos-prueba.txt` card; QA IDs are in `.runtime/acceptance-qa.json`. Sign in through **Continue with email → Sign in → Username or email**. Provisioned `example.test` accounts cannot receive mail.

| Group | Accounts in order | Initial data |
| --- | --- | --- |
| Pacific Ridge Police Department | `alex-rivera`, `maya-johnson`, `daniel-kim` | 9 records, 7 posts; each worker has an avatar and 2/3/2 own posts. |
| California Valley Medical Center | `elena-marquez`, `mateo-rios`, `sarah-chen` | 20 records, 7 posts; Ana, Robert and Fatima have attached portraits. |
| Sonoran Neurological Institute | `noah-brooks`, `lucia-vega`, `owen-patel` | 18 records, 7 posts; Luis, Grace and Hiro have attached portraits. |
| QA Hackathon — disposable tests | `qa-hackathon-admin`, `qa-hackathon-member`, `qa-hackathon-reader` | Admin / register / query. Two users have explicit synthetic consent/enrollment; reader has no consent. |
| Outside the QA group | `qa-hackathon-outsider` | Prepared private profile; initially outside QA, for invitation/removal. |
| Real email / Facebook | Evaluator's own | Registration/correction use new QA accounts with real inboxes, not the accounts above. |

All four QA accounts have avatars and one initial private synthetic-scene post. The QA group starts without records; its Work posts will be created in G01. In Postman use the 39 prepared requests in **01 Police**, **02 Nursing** and **03 Memory**. The API guide linked above locates them in the current collection; the full catalog has other operations with their own prerequisites.

**Clinical validity:** the fictional prescriptions cover **November 1–30, 2026 UTC**. Outside this interval expect a validity discrepancy: do not mark a match or change the clock. The organizer must prepare a current QA dataset before rerunning positives. The app sends the current time; technical issues/references are checked in T04.

**Visual-card limits:** recapturing synthetic faces tests integration, camera quality and navigation, not representative accuracy or real-person identity verification. For Facebook login use your own real face and the normal steps. If a screen capture is rejected for quality, record why and adjust framing; do not disable controls.

## Acceptance cases

### P — Preparation — organizer and evaluator

- [ ] **P01** — Receive the APK, open the public access table and receive the private card for the remaining accounts. Retain your previously reported installation as history; now verify the full version, build date and SHA-256 of the installed APK. Expected: it matches the release under test.
- [ ] **P02** — Record phone, Android version, starting language, commit and server release in the run header. Enable Do Not Disturb and hide notifications. Expected: an identifiable run and a recording-ready screen.
- [ ] **P03** — Organizer: supply the nine scenario accounts and the QA accounts from the access card. Verify avatars, posts, roles, groups and permissions before starting. Missing preparation means BLOCKED; the evaluator does not import data.
- [ ] **P04** — Open the linked visual cards on the computer. Show a large portrait and then the three faces together; adjust brightness/zoom to avoid glare. Expected: the phone can frame them without downloading files.
- [ ] **P05** — Prepare your authorized Facebook account and a real inbox with three receiving addresses or aliases: A for C01, B for the pending account and C as the corrected C03 destination. Keep passwords only in your private card. Expected: receipt at A/B/C and access to the test Facebook account.

### S — Server and technical session

- [ ] **S01** — Organizer: request GET /health/live and GET /health/ready. Expected: both return 200; save time and responses. A failure blocks dependent tests.
- [ ] **S02** — Import the public collection from the API guide and select No environment. Locate and run the 01 Police, 02 Nursing and 03 Memory folders: 13 requests per folder, 39 total. Expected: automatic access, existing workspace records/posts, readable images and relevant answers. Save every request result; the old empty workspace does not test the scenarios.
- [ ] **S03** — Organizer: verify rotation with POST /v1/auth/refresh and rejection of the previous refresh token in a separate QA session. Expected: new token works and old token is rejected; redact tokens from evidence. Disable automatic renewal on the negative request to test the consumed token.

### A — Entry and nine prepared accounts

- [ ] **A01** — Open Continue with email → Sign in; enter elena-marquez in Username or email and the password from the public table linked above. Expected: sign-in succeeds without registering again.
- [ ] **A02** — Repeat sign-in, avatar and opening every post for all nine accounts in the table. Initial expectation: 2/3/2 own posts for the three workers in each group; record legitimate changes since the inventory. Save nine results, not one representative result.
- [ ] **A03** — In Work select the assigned group. Initial inventory per group: seven posts; Police 9 records, Nursing 20 and Memory 18. Open Workspace records to count them. Each account retains its own group, not the other scenarios.
- [ ] **A04** — Sign out, enter an incorrect password once and then the correct one. Expected: understandable error and no access with the wrong password; the second attempt succeeds.
- [ ] **A05** — Close and reopen the app, then sign out and change scenarios. Expected: valid session restored after reopening; changing accounts removes the previous account's data and pending actions.

### C — Real email and Facebook

- [ ] **C01** — With a new QA account and your real inbox, use Create account. Open the email and confirm. Expected: RealityOS <support@luxisoft.com> sender, working link and confirmed access. Do not use example.test for this test.
- [ ] **C02** — Attempt registration with the occupied username/email. Expected: identifies the occupied field and offers available actions without creating another account.
- [ ] **C03** — Register another QA account with alias B and keep its link unused. While pending, correct its email to alias C using its current username and password. Expected: the same account changes destination, mail arrives at the new inbox and the old link no longer confirms. Keep this account pending until C04.
- [ ] **C04** — On the pending C03 account use Resend confirmation to alias C and confirm with the latest link. Expected: receipt, confirmation and access succeed without duplicate account creation.
- [ ] **C05** — Recover the confirmed QA account password. Expected: real email, successful change, access with the new password and rejection of the old one. Reusing the consumed link is rejected.
- [ ] **C06** — Attempt the pending-email correction on an already confirmed QA account. Expected: rejection and preservation of its current identity/email. The organizer may check by API if the app no longer offers this action.
- [ ] **C07** — Sign in with real Facebook on the phone and complete the permissions and identity steps shown by the app. Expected: a real session and that account's profile; cancelling returns to a usable screen. A simulated token is not a substitute.

### F — Profile and documents

- [ ] **F01** — On a QA email account edit name, location, hometown, birthday and gender; save and reopen. Expected: persisted values, age derived from the date, and rejection of future or pre-1900 dates. Restore initial values.
- [ ] **F02** — In Facebook verify read-only synchronized name and fields; edit permitted biography/contact details and sign in again. Expected: source rules are respected and available Facebook fields refresh.
- [ ] **F03** — Attach a synthetic PDF/DOCX CV from Edit and replace it with a second version prepared by the organizer. Expected: one current version and updated context; another account cannot download the private CV. Denied download is also checked in T02.
- [ ] **F04** — Open another profile from an authorized candidate and ask “What is this profile called?”. Expected: answer based on permitted information, without private posts or the CV file.

### R — Records and scenarios

- [ ] **R01** — As alex-rivera: Work → Pacific Ridge Police Department → Workspace records → test case 1. Open notes, relationships and attachments. Expected: correct source/version, evidence and author/context. This scenario does not include enrolled police person records.
- [ ] **R02** — As elena-marquez open Ana Solis and her portrait; return to encounter, prescription and notes. Repeat for Robert Lane and Fatima Nasser. Expected: three distinct people, each with their own relationships and attached portrait.
- [ ] **R03** — As noah-brooks open Luis Moreno, his portrait, reminder and event; inspect Grace Wilson and Hiro Tanaka. Expected: correct related records with visible dates/sources.
- [ ] **R04** — Open an image and MP4 from each scenario; play, pause and return to the record. Expected: accessible content and correct return. Prepared MP4s are static synthetic scenes, not real motion.
- [ ] **R05** — Search by name and nonexistent text in Workspace records; open two records in sequence and go back while loading. Expected: correct filtering, understandable empty state and no late response replacing the current record.
- [ ] **R06** — In Search ask “What recorded information is available about Ana Solis?” with Nursing selected, and about Luis's reminder in Memory. Expected: authorized workspace references and contextual answers without invented facts or treatment authorization. Save the full text intended for the video.

### M — Clinical comparison — fictional data

- [ ] **M01** — In Ana Solis → Compare medication fields, select Prescripción ficticia 1, ingredient DEMO MEDICINE and concentration 10 mg; confirm identity. Expected during validity: fields match, with professional review required. The app sends the current time.
- [ ] **M02** — Change only concentration to 20 mg and compare. Expected: editing clears the previous result and the new comparison reports a discrepancy. The organizer verifies the prescription reference in T04.
- [ ] **M03** — For Robert Lane use Prescripción ficticia 2, DEMO MEDICINE and 10 mg. Expected: discrepancy for a recorded allergy; technical detail identifies recorded_allergy.
- [ ] **M04** — For Fatima Nasser use Prescripción ficticia 3, DEMO MEDICINE and 10 mg. Expected: discrepancy for prior administration; technical detail identifies administration_history_requires_review.
- [ ] **M05** — Empty a field, then test without confirming identity. Expected: empty fields prevent comparison; missing confirmation never produces a valid match. Changing prescription or confirmation invalidates the previous result.

### O — Objects and history

- [ ] **O01** — In Police search “yellow flashlight” and “red screwdriver”; in Nursing “medicine cart”, “blue pen”, “disposable gloves”; in Memory “red document folder”, “brass keys”, “blue notebook”. Expected: relevant authorized evidence; record each query, not only the first.
- [ ] **O02** — Open one result per scenario. Expected: image/frame with relevant highlighting, source and last-seen date; identifiable visual confidence. Do not require 1920×1280 for every original or assume the object is still there.
- [ ] **O03** — Ask “Where is the purple submarine?” before adding QA data. Expected: insufficient evidence, without an invented location/photo. If actual evidence exists, the organizer selects and records another absent object.
- [ ] **O04** — Repeat a search in Spanish and English after changing app language; reopen results/history after restarting. Expected: consistent selected language, correct attachments and no cross-account history confusion.
- [ ] **O05** — Use Find object with the camera to frame a scene on the visual cards. Expected: an explicit query returns relevant evidence or an understandable quality rejection; passing positive retrieval requires a valid capture with a match.
- [ ] **O06** — In QA register a new photo from the app, wait for processing to finish, then search for it. Expected: new evidence with source/date. Querying alone does not register the photo; T03 verifies the separation.

### B — Face search — opening a record is not a substitute

- [ ] **B01** — As elena-marquez in Nursing, complete any consent requested by the app and use Find person to capture Ana's card. Expected: Ana Solis candidate, evidence and similarity; opening leads to her record. Adjusting framing is allowed; skipping search does not pass.
- [ ] **B02** — As noah-brooks in Memory capture Luis's card. Expected: Luis Moreno candidate and his record, without Nursing candidates.
- [ ] **B03** — In Nursing capture Ana, Robert and Fatima together. Expected: three faces detected in a quality capture, correct numbered/color box-to-candidate association; open one and return to the group result.
- [ ] **B04** — As qa-hackathon-admin select the QA group and capture the qa-hackathon-member portrait on the cards. Expected: a user candidate, opening their profile and permitted content. Explicit enrollment is checked beforehand, not inferred from the avatar.
- [ ] **B05** — As qa-hackathon-reader without consent, attempt person search. Expected: explanation/consent prompt in the app; the API rejects search without consent. Keep this account without consent for the negative case.
- [ ] **B06** — Capture a face-free object card, then Ana's portrait while in QA. Expected: no-face error first and no clinical record link second. Never invent an identity.
- [ ] **B07** — Organizer, after positive cases: revoke consent only for the QA member, verify candidate exclusion and deletion of their enrollments; explicitly grant consent and enroll their portrait again to restore the fixture. Save before/after evidence.

### G — Posts, groups and privacy

- [ ] **G01** — As qa-hackathon-member publish a photo and a short phone video of a moving object, first in Profile and then in Work → QA. Use note “QA acceptance — photo/video”. Expected: four posts with correct destinations and working viewing/playback.
- [ ] **G02** — Repeat an identical photo and review the duplicate decision; cancel one replacement and confirm another. Expected: the app explains the decision, cancellation preserves the original and confirmation retains the intended history.
- [ ] **G03** — Interrupt connectivity during a QA upload, restore it and retry. Expected: recoverable state and no extra publication caused by retrying the same operation.
- [ ] **G04** — On a QA post add a like, comment and reply; reopen as another authorized account. Expected: persistence and correctly threaded reply. Report only QA content; verify response and moderation visibility in group administration as qa-hackathon-admin and its rejection for reader under T02.
- [ ] **G05** — QA admin creates a single-use invitation; the organizer supplies its code and the qa-hackathon-outsider account. Enter the code in Join (not the shared PIN), attempt reuse and then remove the new member. Expected: first access succeeds, reuse is rejected and removal revokes restricted access. Do not use or delete scenario groups.
- [ ] **G06** — From another account open the QA author's profile. Expected: only permitted public posts; private posts and inaccessible-group posts are not exposed by sharing a link. Also check originals in T02.

### V — Voice and languages

- [ ] **V01** — With Memory selected dictate “¿Dónde se vieron las llaves de latón?” then an equivalent English question after changing language. Expected: relevant transcription and an answer in the selected language.
- [ ] **V02** — Play an answer and use Replay; change language for a new query. Expected: each playback matches its text/language, without reusing another answer's audio.
- [ ] **V03** — Deny microphone permission, then grant it and retry; disconnect during voice and recover. Expected: clear notices, recovery and no old audio presented as a new answer.
- [ ] **V04** — Switch account ES → EN → ES with a test draft where applicable. Expected: UI, examples, answers and voice respect account/language without rewriting the draft or mixing histories.

### D — Display simulator using the phone

- [ ] **D01** — Open Meta Ray-Ban Display → Debug preview and start Mock Device Kit. Grant camera/audio. Expected: connection and home screen; record phone sensors, not physical glasses.
- [ ] **D02** — Search → Find object: point at a computer scene. Expected: visible camera, relevant result and evidence opening without blocking return.
- [ ] **D03** — Search → Find person: repeat Ana, the QA member and the three Nursing faces with their corresponding accounts/groups. Expected: candidates, authorized thumbnails, boxes and correct record/profile opening; returning preserves the group result.
- [ ] **D04** — Voice command: query Ana's information in Nursing, an object in Memory and a greeting. Expected: person queries use workspace records, objects retrieve evidence and greetings receive a response; speech stays coherent. Do not require profiles/search for person queries.
- [ ] **D05** — In QA choose the available destination in Android and capture a photo/video in Display. Review and confirm Publish. Expected: displayed destination matches publication; do not assume automatic Profile upload.
- [ ] **D06** — Cancel a capture, discard a pending one and retry after reconnecting. Switch account during an operation. Expected: recoverable navigation, no publication after discard and no private images restored from another session.

### U — Phone robustness

- [ ] **U01** — Visit Profile / Work / Search / Ray-Ban. Expected: correct header/account, accessible actions and coherent navigation back.
- [ ] **U02** — Deny camera and audio separately, then grant them. Expected: explanation of the missing permission and continuation once granted; no silent capture.
- [ ] **U03** — Disconnect during search and record opening; reconnect. Expected: distinct error/empty/loading states and useful retry, without a stuck screen.
- [ ] **U04** — Pinch in the viewer, release the last finger and drag repeatedly. Expected: stable image without jumps, disappearance or invalid coordinates.
- [ ] **U05** — With a draft, open the keyboard, rotate and background the app; return. Read older messages and receive another. Expected: draft retained and scrolling does not pull you to the bottom while reading above.
- [ ] **U06** — Check account/profile screens at 320 dp and 200% text on a device/emulator configured for that purpose; record the environment. Expected: usable buttons/fields and scroll-accessible content. Restore settings afterwards.

### T — Technical organizer evidence

- [ ] **T01** — Contract: compare public OpenAPI with tests/contracts/openapi.json, normalizing key order only. Run relevant Makefile checks and attach CI for the evaluated commit. Expected: differences explained/fixed and checks passing; a build does not prove physical camera behavior.
- [ ] **T02** — Permissions: with QA sessions check 401 without token, 403 without role/consent, inaccessible foreign resources, media/CV privacy and moderation. Test malformed/missing IDs according to contract, consumed invites and revocation. Accept 403/404 as specified by each route, not a universal 404.
- [ ] **T03** — Evidence: use BYTEA, idempotency, capture-free Query and consented Register regressions; verify original hash before/after translation/refinement. Check SAM with a valid Register observation_id, not a social publication ID.
- [ ] **T04** — Records: verify comparator references/issues, import versions/idempotency, clinical relationships and rejection of deletion leaving active orphan records. Use isolated test fixtures, not scenario patient deletion. Confirm MP4 with a Range request and partial 206 response.
- [ ] **T05** — Languages: prepared information reads from DB; missing content may invoke the separate information/prepare flow to generate/store translations. Check both branches and no silent language substitution. Do not claim every opening is provider-free.
- [ ] **T06** — Providers: retain evidence of Live Muse/SAM/transcription and authenticated ElevenLabs WAV; unauthenticated TTS is rejected. Failures must not silently fall back to mock or old audio. Mock is deterministic/labeled in isolated tests only. Do not switch production to mock to pass.
- [ ] **T07** — Security/errors: verify provider/JWT/DB secrets are absent from APK and evidence; test 409, 422 and 429 in isolation to avoid locking demo accounts. Save redacted results. Confirm biometrics remains isolated from object registration.

### K — R2/S3 buckets — accounts and data prepared by the operator

R2 preparation completed: 426 remote resources verified and ready connections for all 13 accounts. QA admin also has **Directorio social y taller (QA)**. [Preparation receipt](../../assets/storage/demo-verification.json). The following cases remain pending until executed in the app.

- [ ] **K01** — Sign in with each scenario account and the four QA accounts: Profile → My connections shows its prepared source and Test connection succeeds. Missing setup is BLOCKED; the operator follows the [R2 guide](../guides/STORAGE_CONNECTIONS.md), without asking evaluators to find keys.
- [ ] **K02** — As QA admin, create a disposable connection using list/read keys and a limited folder. Reopening never reveals keys. Invalid credentials show a clear error; rotate keys and test again.
- [ ] **K03** — Browse folders and pages; preview a photo and MP4, zoom and seek. Playback and return work; unsupported formats are identified.
- [ ] **K04** — Import a QA image and video into My private profile. Wait for Published and open both from the profile. Another account remains denied access to private media.
- [ ] **K05** — Import another image into QA work group: members can open it and outsiders cannot. Remove membership before a new import: the server rejects it without publishing.
- [ ] **K06** — Repeat K04 with unchanged files: no extra posts. An invalid or oversized resource fails independently; fix it and Retry failed. Preserve evidence of rejection and recovery.
- [ ] **K07** — Configure manual sync for a QA folder. Update now advances pages; repeating does not duplicate. The operator adds a file and replaces one: new content imports while duplicate review and originals are preserved. Remote deletion never deletes posts.
- [ ] **K08** — Enable a 15-minute schedule, add a QA resource and wait for a real cycle. It imports without Update now. Pause, add another and confirm automatic import stops; manual update remains available.
- [ ] **K09** — Select a prepared scene → Search object in the correct space. Open authorized evidence and try an image without matches. Queries create no posts or new evidence.
- [ ] **K10** — In Nursing, select Ana and the clinical space → Search person → explicit consent → candidate → record. As QA reader, decline consent: no search or automatic enrollment occurs. As QA admin, test a user candidate and open its profile.
- [ ] **K11** — In QA, select cv-v1.pdf → Use as CV and confirm. Repeat with cv-v2.pdf: the private CV is replaced without a public post; another account cannot access it.
- [ ] **K12** — Disconnect the disposable K02 connection: listing, downloads and sync stop; imported posts still open. Switch accounts: the previous connection and keys remain hidden. Repeat main text states in ES and EN.

### H — Hackathon closure and submission

- [ ] **H01** — Confirm current deadline/timezone, category, track, team and participation requirements in the portal. Save proof. The supplied reference says November 4, 2026, 21:00 EST/Bogotá; it does not replace portal confirmation.
- [ ] **H02** — Review public repository, project license, InsightFace weight rights, DAT terms and asset provenance. Expected: documented organizer decisions; unresolved rights are not marked approved.
- [ ] **H03** — Check every P–T and K case: no pending, failed or blocked cases, with evidence for the tested release. After code/server changes, repeat affected cases and entry → record → search → Display.
- [ ] **H04** — Record the real three-minute video with passed journeys and event contributions. Include actual consented face search, record, evidence/SAM and explicitly labeled simulated Display. Review any visible clinical answers.
- [ ] **H05** — Open the video link while signed out; check duration, audio, absence of secrets/notifications and README links. Expected: evaluators can view the recording; concept videos are not substitutes.
- [ ] **H06** — Submit in the portal and save receipt, time, project and delivered links. Expected: submission confirmation. A GitHub push or passing all tests is not submission.

## Final result

There are **89 acceptance cases P–T and K** and **6 closure/submission cases H**. Passed coverage = passed P–T and K cases / 89 × 100. Executing a failed case counts as executed, not passed. Every variant must pass; blocked cases remain in the denominator.

- **Tests passed:** 89/89, with evidence and no failures/blocks/pending cases.
- **Submission prepared:** tests passed and H01–H05 complete.
- **Application submitted:** H06 complete with portal receipt.

Closure statement, only when supported:

> 100% of the 89 acceptance cases defined for version [APK/hash], server [release], phone [model/Android] and simulated Display were executed and passed on [date], with evidence [record]. Physical glasses and Windows local are excluded.

Organizer preparation checks are documented separately; this template does not claim the manual run has happened. The portal receipt proves submission. [Official portal](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit).
