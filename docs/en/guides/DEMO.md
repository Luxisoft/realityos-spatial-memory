[Español](../../es/guides/DEMO.md) · [Index](../INDEX.md)

# Local evaluation and test resources

Accounts, groups, profiles, records, publications, classification and authored translations live in PostgreSQL. `simulator/database/` contains installation SQL only. The initializer applies it once in the same transaction that imports original media and records the installed revision. API, Android and worker operations query the application tables.

Original local test resources remain organized under `simulator/media/`:

- `memory/`: scenes, record attachments and account resources for Memory.
- `police/`: sixteen case portraits, Police account resources and three park videos.
- `meta-social/`: avatars, private references for the authorized synthetic profiles and three public-space videos.
- `shared/`: scenario account avatars.
- `regression/`: query photos, documents and historical test resources. They do not recreate retired scenarios or become publications.

`media/manifest.csv` records each resource's path, SHA-256, source, license and delivery status. `repository` means the file ships in Git; `local-only` identifies previous generated resources and archives preserved only in this checkout. This technical inventory contains no publication or profile records.

<a id="access"></a>

Start local evaluation with `make local-start` or the PowerShell launcher. A single initializer prepares the schema and imports original bytes into PostgreSQL BYTEA. Restarts consult durable installation receipts and preserve edits, deletions, memberships and consent revocations. Installation files are never synchronized back over user records. Android Debug and Postman select among nine local accounts without passwords; this access is unavailable on the server.

<a id="video"></a>

Videos use the same publication tables and media routes as images. Queries use indexed evidence; they do not fabricate results or biometric authorizations. Validation questions are documented in [video evaluation](../testing/VIDEO_EVALUATION.md).

The `004-group-videos.sql` revision adds the six requested videos once, preserving existing case publications and introductions:

| Group | Pexels videos |
| --- | --- |
| Police | [Ibirapuera, 25757454](https://www.pexels.com/video/pessoas-caminhando-e-pedalando-no-parque-do-ibirapuera-25757454/), [overcast park, 29401365](https://www.pexels.com/video/busy-park-walkway-on-an-overcast-day-29401365/), [Edinburgh, 30614848](https://www.pexels.com/video/busy-park-pathway-in-edinburgh-during-spring-30614848/) |
| Meta Social Media | [city sidewalk, 33802407](https://www.pexels.com/video/busy-city-sidewalk-with-people-walking-33802407/), [tree-lined park, 12557513](https://www.pexels.com/video/park-with-trees-and-pedestrians-12557513/), [winter park, 3699519](https://www.pexels.com/video/people-spending-their-day-enjoying-the-park-in-winter-season-3699519/) |

The MP4 files ship through Git LFS without transcoding. The owner supplied 29401365 through Drive when Pexels rejected the direct download; its provenance and hash remain recorded. New installations have 41 publications: 19 Police, 6 Meta Social Media and 16 Memory. The `005-police-records.sql` revision adds records 11 and 12 with arrest warrants and records 13 through 16 as missing persons with search orders. Each record shares its original portrait with its linked publication. Updates respect removed groups and memberships instead of recreating them to insert content.

Private references are never publications or public thumbnails. Internal simulation metadata and provenance remain intact. Historical media do not recreate Hospital, Workshop or other retired groups.

<a id="handoff"></a>

New data revisions must be explicit and transactional, with upgrade and restart tests. Do not add business-record JSON catalogs, alternative account generators or copies of records embedded in application code. Delivery includes the [Postman collection](../../postman/RealityOS.postman_collection.json) and the canonical Debug APK linked from the README.
