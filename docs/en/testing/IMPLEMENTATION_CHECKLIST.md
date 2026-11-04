[Español](../../es/testing/IMPLEMENTATION_CHECKLIST.md) · [Project](../README.md) · [Visual cards](QA_VISUAL_FIXTURES.md) · [Local setup](../guides/DEMO.md#access) · [Postman](../api/POSTMAN.md)

# Local acceptance checklist

Updated November 4, 2026 for the SQL-based local installation. Every manual case below starts pending. Automated checks and the current APK hash are recorded in [Implementation status](../project/IMPLEMENTATION_STATUS.md); they do not constitute physical-device acceptance.

## Preparation and evidence

Follow the [local setup guide](../guides/DEMO.md). The runtime has four services: PostgreSQL, Redis, API and worker. Use the judge's private Meta key for real direct model calls and installed Android voices. Keep credentials and execution logs private. Use a disposable local installation for edits, deletions and membership tests.

Record the tester, date, app version/hash, operating systems, selected account/group, language, steps, observed result and supporting capture for each case. Mark a case complete only after all its variants pass. Record unavailable devices or integrations as pending.

| Local group | Access accounts | Prepared records | Group publications |
| --- | --- | --- | --- |
| Pacific Ridge Police Department | Alex Rivera, Maya Johnson, Daniel Kim | 16 fictional person records | 16 portraits + 3 videos |
| Meta Social Media | Elena Marquez, Mateo Rios, Sarah Chen | No ordinary workspace records | 3 avatar introductions + 3 videos |

The total is 16 records and 25 publications. The thirteen additional synthetic Meta Social Media profiles are not selector accounts; their three private references per profile remain outside the gallery. Sources and original hashes are in the [media manifest](../../../simulator/media/manifest.csv).

## Installation and local access

- [ ] **P01** — Retrieve code and Git LFS resources, start the local stack and install the canonical Debug APK through the README instructions. Record the exact APK hash and confirm `/health/ready` responds on the local PC.
- [ ] **P02** — Complete first startup on the intended Windows/Linux host, including image/model downloads. Confirm the four services and successful database initialization before evaluating queries.
- [ ] **A01** — Open the local selector: both groups start collapsed. Check all six accounts, their names and avatars. Switching accounts must not reuse another account's group or session.
- [ ] **A02** — Confirm an account sees only authorized groups and resources. A Police account must not read Meta Social Media records, original media or private references.
- [ ] **A03** — Restart local services. Existing edits, hidden/deleted publications and removed memberships must remain unchanged; initialization must not restore them.

## Records and publication data

- [ ] **R01** — Open all 16 Police records and their linked portrait publications. Confirm five active arrest warrants and two active proceedings among those five. Bruno Escobar and Daniel Serrano have arrest warrants without active proceedings or convictions.
- [ ] **R02** — Open Samuel Ortega, Elena Duarte, Isabel Mora and Natalia Campos (PRP-0013–0016): missing-person status and each active search order must be visible separately from arrest fields. Confirm no arrest warrant, criminal history or active proceedings. The other seven clear records retain no history, warrants or proceedings.
- [ ] **R03** — Verify each portrait opens its original media only for an authorized member. Record lookup and sharing must not grant biometric authorization or create enrollments.
- [ ] **G01** — Check all 25 publications across the two groups, including pagination. Verify authors, categories, tags, captions, notes and ES/EN stored display text. Profiles and gallery lists must stay consistent after edits.
- [ ] **G02** — Apply category, tag, author, date and text filters; clear them and switch groups. Open a publication and return. Verify scope, result ordering and retained filter state.
- [ ] **G03** — On a disposable installation, publish explicitly into an existing group with valid classification. Check duplicate handling, ownership restrictions and independent comments/reactions on authorized group copies.

## Videos and object evidence

- [ ] **V01** — Play all six added Police/Meta videos. Verify full originals, playback/seek behavior and access rejection from another group.
- [ ] **V02** — Follow [Video evaluation](VIDEO_EVALUATION.md) to verify scoped playback and downloads. Record any live query result separately; there are no reviewed object/time expectations for these six videos.
- [ ] **V03** — Query for an absent object and query outside the account's groups. Expect no invented evidence and no unauthorized results. A query must not initiate a new Register capture.
- [ ] **V04** — Exercise explicit camera/image input using the [visual cards](QA_VISUAL_FIXTURES.md). Record provider failures and latency separately from visual correctness; do not count a loading state as a pass.

## Privacy and consent

- [ ] **B01** — Verify that the existing biometric search requires its consent and permissions. Importing the Police records or viewing their ordinary portrait publications must not enroll those people automatically.
- [ ] **B02** — Confirm Meta profile results use separate avatars; private reference photos must not appear in the gallery, generic media endpoints or result thumbnails. Recheck access after consent revocation or membership removal in the disposable installation.
- [ ] **B03** — Check private profile/CV ownership and unrelated-workspace isolation. No account credentials, provider keys or private documents may appear in public exports.

## Android and Postman

- [ ] **U01** — Review the exercised screens in ES/EN, narrow widths and 200% text on the actual phone: selector, gallery, filters, viewer and record details. Check clipping, scrolling, focus, labels and touch targets using the established UI.
- [ ] **U02** — Verify phone permissions, local connection recovery, installed offline voices and actual media loading. Physical glasses/DAT interactions require their own device evidence.
- [ ] **S01** — Import the primary collection and open **Localhost requests → 00 Local scenarios**. Use local account selection without passwords. Verify variables and sessions stay isolated between scenarios.
- [ ] **S02** — Confirm **Server requests** is disabled and has no active URL or credentials. Run local prepared requests, including the reviewed video checks; preserve HTTP results separately from visual acceptance.
- [ ] **S03** — Apply the current code/data update, restart and repeat the changed scenarios. Verify new SQL revisions install once and preserve previous content, edits, deletions and memberships.

## Separate external acceptance

Facebook Live, real inbox registration/recovery, server storage integrations, remote voice and physical glasses require separately authorized environments and evidence. They are not part of the local four-service runtime. Use the relevant [integration guides](../INDEX.md) and retain current [rights evidence](../project/THIRD_PARTY.md) for distributed assets and services.
