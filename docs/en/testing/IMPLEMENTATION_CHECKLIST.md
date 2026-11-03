<p align="center"><a href="IMPLEMENTATION_CHECKLIST.md"><img src="../../assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="../../es/testing/IMPLEMENTATION_CHECKLIST.md"><img src="../../assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# RealityOS manual checklist — acceptance and Hackathon 2026

[← Project](../README.md) · [Camera-ready visual cards](QA_VISUAL_FIXTURES.md) · [Access and scenarios](../guides/DEMO.md#access) · [Postman](../api/API.md#quick-start) · [Submission](../project/HACKATHON.md)

**Updated November 3, 2026 for code `0090bdf`.** Start with the three public accounts and their existing connections. Perform data-changing tests in QA.

## Start in the app now

1. Install the prepared APK: `android/app/build/outputs/apk/debug/app-debug.apk`, version **`0.1.6-debug-20261103-1224`**. Continue if this exact build is already installed. The short `0.1.6` label is insufficient.
2. Open **Continue with email → Sign in → Username or email**. Use **`elena-marquez`** and copy its password from the [public access table](../api/API.md#quick-start). This account is already confirmed.
3. In **Profile**, check the avatar and open a post. In **Work → California Valley Medical Center → Workspace records**, open **Ana Solis** and her portrait. The group has 20 records and seven posts.
4. Open **Profile → My connections → Demo nursing → Test access**. In **Import destination / search workspace**, choose **California Valley Medical Center**.
5. Select **only** `patient-ana.png`, scroll to **Use to find a person** and press it. If consent appears, read it, accept when appropriate and press search again. Open Ana's candidate and record. No portrait download or repeated enrollment is needed.
6. Deselect the previous portrait and select only `medicine-cart.png` → **Use to find an object**. Wait for the response and open its evidence. An image query may take over a minute; the APK waits up to **180 seconds**. Avoid repeated presses and do not count a loading state as a pass.

This walkthrough starts A01, A03, R02, K01, K03, K09 and K10. Pass an ID below only after completing **all** its accounts and variants. Continue in section order: **P → A → R → M → O → B → F → G → K → V → D → U → C → S → T → H**.

For camera and Display tests, open the [visual cards](QA_VISUAL_FIXTURES.md) on a computer and frame them with the phone. Bucket searches and records use files already available inside the app. Full scope includes a **physical Android phone, Display with Mock Device Kit, real email and real Facebook**; physical glasses and Windows local are outside this run.

## Prepared reference for this run

| Item | Verified value |
| --- | --- |
| APK on this host | `0.1.6-debug-20261103-1224` · package `com.luxisoft.realityos` |
| SHA-256 of this host's APK | `56b9a60ca9ec07ceb9e9338ad4b34143969fb6b42c68e3c47891851e5f872965` |
| App / server code | [`0090bdf`](https://github.com/Luxisoft/realityos-spatial-memory/commit/0090bdfcb8d8f298da73ece3c8d6e57e6b5448b6) |
| API | `https://realityos.luxisoft.com/v1` |
| Availability / documentation | [Live](https://realityos.luxisoft.com/health/live) · [Ready](https://realityos.luxisoft.com/health/ready) · [Swagger](https://realityos.luxisoft.com/docs) · [OpenAPI](https://realityos.luxisoft.com/v1/openapi.json) |
| Available technical evidence | **492 backend/gateway tests, 224 Android tests**, Debug/Release builds and emulator tests in [successful CI](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/41684656174). [Successful deployment](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/41684655293), Alembic `20261103_0035`. |
| Available data | 47 records, 21 group posts and six enrolled record portraits; 426 R2 resources and 14 private connections across 13 accounts. |

This technical evidence does not pass manual cases. If you install the Actions APK for the same commit, record **its own** version and hash: its build timestamp and hash may differ from this host's file. If app or server code changes, record a new run and repeat affected cases.

## Marking and recording results

Every case starts pending. Mark `[x]` only after performing every step and recording evidence. Previous API checks do not automatically pass screen tests. Do not use “not applicable” to conceal failures or missing preparation.

In a private checklist copy or `.runtime/acceptance-run.csv`, record each ID with **PENDIENTE / APROBADO / FALLIDO / BLOQUEADO** (pending / passed / failed / blocked), timestamp, account, observed result, evidence, issue and retest. For multi-account/language cases, attach each result before passing the ID. Save screenshots/logs in `.runtime/acceptance-evidence/`; never publish tokens, passwords, private email addresses or personal media. Spreadsheet columns:

```csv
id,estado,fecha_hora,cuenta,resultado,evidencia,incidencia,repeticion
A01,PENDIENTE,,,,,,
```

On this host, `.runtime/acceptance-run.csv` contains all **98 pending rows** (92 tests and six closure steps), in this guide’s order.

| Run identification | Complete before passing |
| --- | --- |
| Tester and date / timezone | — |
| Phone and Android version | — |
| Initial / second language | ES / EN (test both) |
| APK full version, build date, SHA-256 | Reference above; confirm the file you installed |
| Commit / backend release / contract | `0090bdf` / Alembic `20261103_0035`; record changes |
| Display | Mock Device Kit, phone camera and microphone |
| User-reported history | APK installed; build identity to be corroborated in P01 |

## Prepared accounts and data

The three primary accounts and their passwords are in the [public access table](../api/API.md#quick-start), published with owner authorization. The remaining six accounts and four QA accounts are available in the existing private `.runtime/accesos-prueba.txt` card; QA IDs are in `.runtime/acceptance-qa.json`. Sign in through **Continue with email → Sign in → Username or email**. Provisioned `example.test` accounts cannot receive mail.

| Group | Accounts in order | Initial data |
| --- | --- | --- |
| Pacific Ridge Police Department | `alex-rivera`, `maya-johnson`, `daniel-kim` | 9 records, 7 posts; each worker has an avatar and 2/3/2 own posts. |
| California Valley Medical Center | `elena-marquez`, `mateo-rios`, `sarah-chen` | 20 records, 7 posts; Ana, Robert and Fatima have attached portraits. |
| Sonoran Neurological Institute | `noah-brooks`, `lucia-vega`, `owen-patel` | 18 records, 7 posts; Luis, Grace and Hiro have attached portraits. |
| QA Hackathon — disposable tests | `qa-hackathon-admin`, `qa-hackathon-member`, `qa-hackathon-reader` | Admin / register / query. Two users have explicit synthetic consent/enrollment; reader has no consent. |
| Outside the QA group | `qa-hackathon-outsider` | Prepared private profile; initially outside QA, for invitation/removal. |
| Real email / Facebook | Evaluator's own | Registration/correction use new QA accounts with real inboxes, not the accounts above. |

All four QA accounts have avatars and one initial private synthetic-scene post. The QA group starts without records; its Work posts will be created in G01. In Postman use the 39 prepared requests in **01 Police**, **02 Nursing** and **03 Memory**. The API guide linked above locates them in the current collection; the full catalog has other operations with their own prerequisites.

## Exact files to test from R2

In **Profile → My connections**, open the connection, select the correct workspace, then press **Preview** or select one checkbox for a search. Search buttons appear below the file list. Select both files to import a photo and video; select only the PDF to use a CV.

| Account / connection | Available files | Search result / use |
| --- | --- | --- |
| `alex-rivera` / **Demo police** | `evidence-desk.png`, `evidence-desk-1.mp4` | Desk objects; Pacific Ridge Police Department workspace. |
| `elena-marquez` / **Demo nursing** | `patient-ana.png`, `patient-robert.png`, `patient-fatima.png`, `medicine-cart.png`, `medicine-cart-1.mp4` | Clinical records and objects; California Valley Medical Center workspace. |
| `noah-brooks` / **Demo memory** | `patient-luis.png`, `patient-grace.png`, `patient-hiro.png`, `memory-desk.png`, `memory-desk-1.mp4` | Records and visual memory; Sonoran Neurological Institute workspace. |
| QA accounts / **Demo qa** | `alex-rivera.png`, `maya-johnson.png`, `evidence-desk.png`, `evidence-desk-1.mp4`, `cv-v1.pdf`, `cv-v2.pdf` | Enrolled QA admin/member, test posts and CV replacement. |
| QA admin / **Directorio social y taller (QA)** | `source/`, `muse/`, `generated/`, `workshop/` folders | Browse folders/pages among the 327 prepared resources. |

Each scenario connection contains 31 files; **Demo qa** contains six. Seeing a portrait in a bucket does not authorize another organization's record. Selecting **My private profile** does not automatically select the group for a search.

### Before tests that need additional preparation

- **A02, B04–B07, F, G and QA cases in K:** use the existing private `.runtime/accesos-prueba.txt` card. Do not change public passwords or publish them in the results register.
- **K02 and K07–K08:** the maintainer needs Cloudflare access and a temporary folder for this run. Privately supply or enter credentials, and prepare valid photo/video files, an image of an object absent from the dataset, two object keys with identical bytes, a `.png` containing invalid bytes and a media file exceeding the R2 guide’s download limit. Change only that folder; preserve `Demo police`, `Demo nursing`, `Demo memory` and `Demo qa`.
- **K06 and K12–K15:** use K02's files and temporary connection. The maintainer uploads or corrects R2 objects; the app reads/imports them and does not upload into the bucket. Missing preparation blocks only the dependent cases; continue the prepared walkthroughs.
- **C:** use your authorized Facebook account and real inboxes. `example.test` accounts cannot receive messages.

**Clinical validity:** the fictional prescriptions cover **November 1–30, 2026 UTC**. Outside this interval expect a validity discrepancy: do not mark a match or change the clock. The organizer must prepare a current QA dataset before rerunning positives. The app sends the current time; technical issues/references are checked in T04.

**Visual-card limits:** recapturing synthetic faces tests integration, camera quality and navigation, not representative accuracy or real-person identity verification. For Facebook login use your own real face and the normal steps. If a screen capture is rejected for quality, record why and adjust framing; do not disable controls.

## Acceptance cases

### P — Preparation — organizer and evaluator

- [ ] **P01** — Install or verify the APK identified above; open the app and record its full version. Expected: host build `0.1.6-debug-20261103-1224`, or an Actions artifact for the same commit identified by its own hash; production package rather than the `.local` variant.
- [ ] **P02** — Record tester, phone, Android and language in the run header. Use `0090bdf` as the app/server reference and record any change. Enable Do not disturb. Expected: evidence tied to the installed build.
- [ ] **P03** — Check the three public scenario accounts for avatar, posts, group and R2 connection. Before testing the remaining accounts, open the private card for six workers and four QA accounts. Missing access blocks only its cases; the three public accounts are enough to start.
- [ ] **P04** — For B, O05 and D, open the visual cards on a computer and frame them with the phone; prepare the three-face view too. For R and K, use portraits/files already attached or in My connections. Expected: camera testing without downloading portraits to the phone.
- [ ] **P05** — Prepare your authorized Facebook account and a real inbox with three receiving addresses or aliases: A for C01, B for the pending account and C as the corrected C03 destination. Keep passwords only in your private card. Expected: receipt at A/B/C and access to the test Facebook account.

### A — Entry and nine prepared accounts

- [ ] **A01** — Open Continue with email → Sign in; enter elena-marquez in Username or email and the password from the public table linked above. Expected: sign-in succeeds without registering again.
- [ ] **A02** — Repeat sign-in, avatar and opening every post for all nine accounts in the table. Initial expectation: 2/3/2 own posts for the three workers in each group; record legitimate changes since the inventory. Save nine results, not one representative result.
- [ ] **A03** — In Work select the assigned group. Initial inventory per group: seven posts; Police 9 records, Nursing 20 and Memory 18. Open Workspace records to count them. Each account retains its own group, not the other scenarios.
- [ ] **A04** — Sign out, enter an incorrect password once and then the correct one. Expected: understandable error and no access with the wrong password; the second attempt succeeds.
- [ ] **A05** — Close and reopen the app, then sign out and change scenarios. Expected: valid session restored after reopening; changing accounts removes the previous account's data and pending actions.

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
- [ ] **O05** — Use the object camera search to frame a visual-card scene. Wait for the response: image queries may take over a minute and the client timeout is 180 s. Expected: relevant evidence or a clear quality rejection; the positive case needs a valid capture with a match.
- [ ] **O06** — In QA register a new photo from the app, wait for processing to finish, then search for it. Expected: new evidence with source/date. Querying alone does not register the photo; T03 verifies the separation.

### B — Face search — opening a record is not a substitute

- [ ] **B01** — As elena-marquez in Nursing, complete any consent requested by the app and use Find person to capture Ana's card. Expected: Ana Solis candidate, evidence and similarity; opening leads to her record. Adjusting framing is allowed; skipping search does not pass.
- [ ] **B02** — As noah-brooks in Memory capture Luis's card. Expected: Luis Moreno candidate and his record, without Nursing candidates.
- [ ] **B03** — In Nursing capture Ana, Robert and Fatima together. Expected: three faces detected in a quality capture, correct numbered/color box-to-candidate association; open one and return to the group result.
- [ ] **B04** — As qa-hackathon-admin select the QA group and capture the qa-hackathon-member portrait on the cards. Expected: a user candidate, opening their profile and permitted content. Explicit enrollment is checked beforehand, not inferred from the avatar.
- [ ] **B05** — As qa-hackathon-reader without consent, attempt person search. Expected: explanation/consent prompt in the app; the API rejects search without consent. Keep this account without consent for the negative case.
- [ ] **B06** — Capture a face-free object card, then Ana's portrait while in QA. Expected: no-face error first and no clinical record link second. Never invent an identity.
- [ ] **B07** — Organizer, after positive cases: revoke consent only for the QA member, verify candidate exclusion and deletion of their enrollments; explicitly grant consent and enroll their portrait again to restore the fixture. Save before/after evidence.

### F — Profile and documents

- [ ] **F01** — On a QA email account edit name, location, hometown, birthday and gender; save and reopen. Expected: persisted values, age derived from the date, and rejection of future or pre-1900 dates. Restore initial values.
- [ ] **F02** — In Facebook verify read-only synchronized name and fields; edit permitted biography/contact details and sign in again. Expected: source rules are respected and available Facebook fields refresh.
- [ ] **F03** — With QA, open **Profile → My connections → Demo qa**, select only `cv-v1.pdf` → **Use as CV** → confirm. Repeat with `cv-v2.pdf` and reopen the profile. Expected: updated current CV, no gallery post and no download for another account (T02). No PDF transfer to the phone is needed.
- [ ] **F04** — Open another profile from an authorized candidate and ask “What is this profile called?”. Expected: answer based on permitted information, without private posts or the CV file.

### G — Posts, groups and privacy

- [ ] **G01** — As qa-hackathon-member publish a photo and a short phone video of a moving object, first in Profile and then in Work → QA. Use note “QA acceptance — photo/video”. Expected: four posts with correct destinations and working viewing/playback.
- [ ] **G02** — Repeat an identical photo and review the duplicate decision; cancel one replacement and confirm another. Expected: the app explains the decision, cancellation preserves the original and confirmation retains the intended history.
- [ ] **G03** — Interrupt connectivity during a QA upload, restore it and retry. Expected: recoverable state and no extra publication caused by retrying the same operation.
- [ ] **G04** — On a QA post add a like, comment and reply; reopen as another authorized account. Expected: persistence and correctly threaded reply. Report only QA content; verify response and moderation visibility in group administration as qa-hackathon-admin and its rejection for reader under T02.
- [ ] **G05** — QA admin creates a single-use invitation; the organizer supplies its code and the qa-hackathon-outsider account. Enter the code in Join (not the shared PIN), attempt reuse and then remove the new member. Expected: first access succeeds, reuse is rejected and removal revokes restricted access. Do not use or delete scenario groups.
- [ ] **G06** — From another account open the QA author's profile. Expected: only permitted public posts; private posts and inaccessible-group posts are not exposed by sharing a link. Also check originals in T02.

### K — R2/S3 buckets — accounts and data prepared by the operator

R2 preparation completed: 426 remote resources verified and ready connections for all 13 accounts. QA admin also has **Directorio social y taller (QA)**. [Preparation receipt](../../assets/storage/demo-verification.json). The following cases remain pending until executed in the app.

- [ ] **K01** — With all nine scenario and four QA accounts, open **Profile → My connections**, the table connection and **Test access**. Expected: successful connection without entering keys. QA admin also has Directorio social y taller (QA). Record all 13 accounts; block only a missing variant and consult the R2 guide.
- [ ] **K02** — With QA admin, create **QA aceptación** using Add bucket; the maintainer privately enters endpoint, bucket, region and valid keys for a temporary folder. Test invalid keys in this disposable connection, then repair with Edit credentials. Expected: clear error, successful connection after repair and hidden keys on reopening. Leave prepared demo connections unchanged.
- [ ] **K03** — In Demo qa preview `evidence-desk.png` and `evidence-desk-1.mp4`; zoom, play and seek. In Directorio social y taller (QA), open folders and Next page when available. Expected: authorized media and correct return navigation. Demo nursing marks `hospital.json` unsupported; it does not import workspace records.
- [ ] **K04** — With QA admin in Demo qa, select `evidence-desk.png` and `evidence-desk-1.mp4` → **My private profile → Import selection → Confirm**. Follow Recent imports to Published; if review is required, open Review result and decide explicitly. Open the media in Profile and verify restriction from another account.
- [ ] **K05** — Import an image to the QA group by selecting its destination. Members can open it; outsider cannot see the group or original. The maintainer forces the same destination through the API with outsider and confirms rejection (T02), without creating a post. Preserve scenario memberships.
- [ ] **K06** — Repeat K04 with the same files/source/destination: no extra posts while the imported copy remains published. In QA aceptación import a batch with valid, invalid and oversized files; observe each result. The maintainer repairs the failed R2 resource; press Retry failed files. Expected: recover the failure without repeating the published file.
- [ ] **K07** — In QA aceptación configure **manual sync** for the temporary folder and select private Profile or the QA group. Press Update now, traverse pages and repeat. The maintainer adds an image and changes another: the new one is imported and replacements retain duplicate review. Removing a remote object preserves its imported post.
- [ ] **K08** — Enable a 15-minute schedule for that temporary folder; the maintainer adds a new file and waits for a real cycle without pressing update. Pause, add another file and verify no automatic import. Press Update now and verify it processes. Record times and filenames; an enabled button alone does not pass scheduling.
- [ ] **K09** — With Elena: Demo nursing → California Valley Medical Center workspace → select only `medicine-cart.png` → **Use to find an object**. Wait up to 180 s. If several results appear, open the first and then another: each viewer must match the selected thumbnail rather than always showing the first. Also test a QA image without matches. Searching creates no posts.
- [ ] **K10** — With Elena: Demo nursing → California Valley Medical Center workspace → `patient-ana.png` → **Use to find a person**. Complete consent and press again if prompted; open Ana’s candidate and record. In Demo qa, QA admin searches `maya-johnson.png` within QA and opens the profile. QA reader declines consent: no search runs and file imports do not enroll faces.
- [ ] **K11** — In Demo qa select only `cv-v1.pdf` → **Use as CV** and confirm; repeat with `cv-v2.pdf`. Expected: current version replaced, no new posts and no download for another account. Do not select a PDF together with an image for Import selection.
- [ ] **K12** — In QA aceptación import two maintainer-prepared objects with **different keys and identical bytes** into the same destination. Publish the first; observe duplicate review for the second and cancel. Select it again and press Import selection to create a fresh import. Expected: duplicate review/confirmation is available again; the previous cancelled operation stays cancelled and the original remains until replacement is confirmed.
- [ ] **K13** — Open a post you created in K04 → Delete → confirm. Reimport the same object from the same connection and destination, resolving duplicate review if offered: it becomes available again without reusing the retired post as current. Repeat after replacing a QA post through duplicate confirmation. Use only this run’s own posts; preserve scenario posts and R2 originals.
- [ ] **K14** — Import a new video from the temporary folder. While Recent imports shows Analyzing, enqueue another file and press Test access; open Ready in a browser. Expected: the new operation is accepted and the API responds before the earlier analysis finishes; the worker may process jobs serially. If processing finishes too soon, repeat with another video and retain evidence during analysis.
- [ ] **K15** — Finally disconnect **QA aceptación**. Expected: no listing/downloads or new syncs; published copies still open. If files were still being analyzed, verify they do not publish after disconnection. Change account: the previous connection and keys remain absent. Repeat main text in ES/EN and preserve original demo connections.

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
- [ ] **D05** — With QA, capture a new photo and video in Display. Expected: sending to **private Profile** starts when capture ends, without choosing a group or pressing Publish for each new file. Reopen both in Profile; they do not appear in Work. If a duplicate or failure occurs, use the displayed review/retry flow.
- [ ] **D06** — With the camera open, press X to cancel, including during capture. Trigger a QA duplicate or failure to test Discard/Retry when offered; recover connectivity and change account during an operation. Expected: usable closing behavior, no sending after cancellation before capture completes and no private media restored into another session. An automatically published capture is distinct from one awaiting review.

### U — Phone robustness

- [ ] **U01** — Visit Profile / Work / Search / Ray-Ban. Expected: correct header/account, accessible actions and coherent navigation back.
- [ ] **U02** — Deny camera and audio separately, then grant them. Expected: explanation of the missing permission and continuation once granted; no silent capture.
- [ ] **U03** — Disconnect during search and record opening; reconnect. Expected: distinct error/empty/loading states and useful retry, without a stuck screen.
- [ ] **U04** — Pinch in the viewer, release the last finger and drag repeatedly. Expected: stable image without jumps, disappearance or invalid coordinates.
- [ ] **U05** — With a draft, open the keyboard, rotate and background the app; return. Read older messages and receive another. Expected: draft retained and scrolling does not pull you to the bottom while reading above.
- [ ] **U06** — Check account/profile screens at 320 dp and 200% text on a device/emulator configured for that purpose; record the environment. Expected: usable buttons/fields and scroll-accessible content. Restore settings afterwards.

### C — Real email and Facebook

- [ ] **C01** — With a new QA account and your real inbox, use Create account. Open the email and confirm. Expected: RealityOS <support@luxisoft.com> sender, working link and confirmed access. Do not use example.test for this test.
- [ ] **C02** — Attempt registration with the occupied username/email. Expected: identifies the occupied field and offers available actions without creating another account.
- [ ] **C03** — Register another QA account with alias B and keep its link unused. While pending, correct its email to alias C using its current username and password. Expected: the same account changes destination, mail arrives at the new inbox and the old link no longer confirms. Keep this account pending until C04.
- [ ] **C04** — On the pending C03 account use Resend confirmation to alias C and confirm with the latest link. Expected: receipt, confirmation and access succeed without duplicate account creation.
- [ ] **C05** — Recover the confirmed QA account password. Expected: real email, successful change, access with the new password and rejection of the old one. Reusing the consumed link is rejected.
- [ ] **C06** — Attempt the pending-email correction on an already confirmed QA account. Expected: rejection and preservation of its current identity/email. The organizer may check by API if the app no longer offers this action.
- [ ] **C07** — Sign in with real Facebook on the phone and complete the permissions and identity steps shown by the app. Expected: a real session and that account's profile; cancelling returns to a usable screen. A simulated token is not a substitute.

### S — Server and technical session

- [ ] **S01** — Open the reference Live and Ready links: both must return 200. Open Swagger and verify its `/v1/openapi.json` contract loads. Save time and response; failure blocks dependent operations.
- [ ] **S02** — Import the public collection from the API guide, keep **No environment** and open **Server requests → 00 Live scenarios → 01 Police / 02 Nursing / 03 Memory**. Run 13 requests per folder, 39 total. Expected: automatic login/refresh and current data for all three groups. Retain results; leave Localhost requests variables unchanged.
- [ ] **S03** — Organizer: verify rotation with POST /v1/auth/refresh and rejection of the previous refresh token in a separate QA session. Expected: new token works and old token is rejected; redact tokens from evidence. Disable automatic renewal on the negative request to test the consumed token.

### T — Technical organizer evidence

- [ ] **T01** — Review the linked successful CI/deployment for `0090bdf` and compare public OpenAPI with `tests/contracts/openapi.json`. Expected: identical contract, 492 backend/gateway tests, 224 Android tests and build/emulator evidence. If code changed, run relevant Makefile checks for that revision. This does not pass physical camera testing.
- [ ] **T02** — Permissions: with QA sessions check 401 without token, 403 without role/consent, inaccessible foreign resources, media/CV privacy and moderation. Test malformed/missing IDs according to contract, consumed invites and revocation. Accept 403/404 as specified by each route, not a universal 404.
- [ ] **T03** — Evidence: use BYTEA, idempotency, capture-free Query and consented Register regressions; verify original hash before/after translation/refinement. Check SAM with a valid Register observation_id, not a social publication ID.
- [ ] **T04** — Records: verify comparator references/issues, import versions/idempotency, clinical relationships and rejection of deletion leaving active orphan records. Use isolated test fixtures, not scenario patient deletion. Confirm MP4 with a Range request and partial 206 response.
- [ ] **T05** — Languages: prepared information reads from DB; missing content may invoke the separate information/prepare flow to generate/store translations. Check both branches and no silent language substitution. Do not claim every opening is provider-free.
- [ ] **T06** — Providers: retain evidence of Live Muse/SAM/transcription and authenticated ElevenLabs WAV; unauthenticated TTS is rejected. Failures must not silently fall back to mock or old audio. Mock is deterministic/labeled in isolated tests only. Do not switch production to mock to pass.
- [ ] **T07** — Security/errors: verify provider/JWT/DB secrets are absent from APK and evidence; test 409, 422 and 429 in isolation to avoid locking demo accounts. Save redacted results. Confirm biometrics remains isolated from object registration.

### H — Hackathon closure and submission

- [ ] **H01** — Open the official portal and verify its current deadline/timezone, category, track, team and participation requirements. Save evidence before preparing submission; do not rely on a date copied from an older checklist.
- [ ] **H02** — Review public repository, project license, InsightFace weight rights, DAT terms and asset provenance. Expected: documented organizer decisions; unresolved rights are not marked approved.
- [ ] **H03** — Check all 92 acceptance cases: no pending, failed or blocked cases, with evidence for the tested release. After code/server changes, repeat affected cases and entry → record → search → Display.
- [ ] **H04** — Record the real three-minute video with passed journeys and event contributions. Include actual consented face search, record, evidence/SAM and explicitly labeled simulated Display. Review any visible clinical answers.
- [ ] **H05** — Open the video link while signed out; check duration, audio, absence of secrets/notifications and README links. Expected: evaluators can view the recording; concept videos are not substitutes.
- [ ] **H06** — Submit in the portal and save receipt, time, project and delivered links. Expected: submission confirmation. A GitHub push or passing all tests is not submission.

## Final result

There are **92 acceptance cases** (all except H) and **6 closure/submission cases H**. Passed coverage = passed acceptance cases / 92 × 100. Executing a failed case counts as executed, not passed. Every variant must pass; blocked cases remain in the denominator.

- **Tests passed:** 92/92, with evidence and no failures/blocks/pending cases.
- **Submission prepared:** tests passed and H01–H05 complete.
- **Application submitted:** H06 complete with portal receipt.

Closure statement, only when supported:

> 100% of the 92 acceptance cases defined for version [APK/hash], server [release], phone [model/Android] and simulated Display were executed and passed on [date], with evidence [record]. Physical glasses and Windows local are excluded.

Organizer preparation checks are documented separately; this template does not claim the manual run has happened. The portal receipt proves submission. [Official portal](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit).
