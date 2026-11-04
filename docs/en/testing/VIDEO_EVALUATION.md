[ES](../../es/testing/VIDEO_EVALUATION.md) · [RealityOS](../README.md) · [Postman](../api/POSTMAN.md)

# Local video evaluation

Police and Meta Social Media each contain three ordinary video publications. Their six original MP4 files are installed through the shared SQL loader and stored in PostgreSQL BYTEA. Sources, licenses and SHA-256 hashes are recorded in the [media manifest](../../../simulator/media/manifest.csv); the [local guide](../guides/DEMO.md#video) lists the recordings.

Use an authorized account in the selected group. Open its gallery, play each video, seek within the original and download the original bytes. Repeat the download with a byte-range request and confirm the returned interval and content length. An account outside the group must not retrieve the media. Automated coverage is in [the video tests](../../../tests/test_local_videos.py).

Postman provides database-derived gallery, media and query requests under **Localhost requests → 00 Local scenarios → Police / Meta Social Media**. Start the four local services first. Selection uses local accounts without published passwords; Server requests remains disabled.

The six recordings have no reviewed object/time annotation matrix. The retired Memory videos and their specialized QA requests are removed. Do not claim expected detections, localization quality or time intervals without reviewing the actual source and returned evidence. Live Meta queries require the private local key and completed indexing; their results need a separate recorded validation.

Queries do not create Register captures. “Last seen” describes recorded evidence rather than current location. Any returned gallery match must respect the selected workspace, and private social reference images must never become gallery evidence.

Regenerate public requests from the canonical database with `.venv/bin/python scripts/build_api_docs.py`, then run `make docs-check`. Generation uses isolated in-memory SQLite; it never reads an installed runtime or calls providers. Playback tests and documentation checks do not substitute for real Android/glasses or live-model acceptance.
