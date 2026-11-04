[ES](../../es/testing/VIDEO_EVALUATION.md) · [RealityOS](../README.md) · [Postman](../api/POSTMAN.md)

# Local video evaluation

The Memory group contains four licensed recordings with two reviewed objects each. The local SQL seed installs their original bytes in the application database. Police contains sixteen portrait publications linked to its records and three video publications; Meta Social Media contains three account introductions and three video publications. The six added recordings are available through their group galleries. The reviewed object intervals below cover the four Memory recordings.

In Postman open **Localhost requests → 00 Local scenarios → Sonoran Neurological Institute → Video …**. Start the four local services and allow indexing with your private Meta key to finish. Account selection is automatic and requires no published password. Server requests remains disabled.

Each video request must retrieve the specified publication, a frame inside the observed interval, SAM localization and the original download. `gallery_matches` contains publication evidence even when Register's `found` field is `false`. “Last seen” describes recorded evidence, not an object's current location. A saved account language preference overrides the requested language.

## Test matrix

### Memory

| Video and author | Owner account | Question | Visible interval |
| --- | --- | --- | --- |
| [7986194](https://www.pexels.com/video/a-person-getting-keys-on-the-table-7986194/) · SHVETS production | `noah-brooks` | Find the keys on the wooden table. | 0–4.5 s |
| [7986194](https://www.pexels.com/video/a-person-getting-keys-on-the-table-7986194/) · SHVETS production | `noah-brooks` | Find the dark sunglasses. | 0–7.04 s |
| [5828599](https://www.pexels.com/video/a-person-putting-things-on-it-s-bag-5828599/) · Polina | `noah-brooks` | Find the laptop beside the backpack. | 0–19 s |
| [5828599](https://www.pexels.com/video/a-person-putting-things-on-it-s-bag-5828599/) · Polina | `noah-brooks` | Find the brown wallet. | 0–27 s |
| [5615158](https://www.pexels.com/video/top-view-of-cooking-vegetables-5615158/) · KATRIN BOLOVTSOVA | `lucia-vega` | Find the kitchen grater. | 0–26.1 s |
| [5615158](https://www.pexels.com/video/top-view-of-cooking-vegetables-5615158/) · KATRIN BOLOVTSOVA | `lucia-vega` | Find the wooden spoon. | 0–26.1 s |
| [8034068](https://www.pexels.com/video/man-looking-a-documents-8034068/) · Edmond Dantès | `owen-patel` | Find the documents with yellow sections. | 0–13.64 s |
| [8034068](https://www.pexels.com/video/man-looking-a-documents-8034068/) · Edmond Dantès | `owen-patel` | Find the round metal-framed eyeglasses. | 0–13.64 s |


## Absences and permissions

Ask for a violin in ES and EN: expect no matching evidence. An account outside the group must receive 403 when querying its workspace and 403/404 when downloading its publication.

## Provenance and reproducibility

Sources, licenses and SHA-256 hashes are retained in the [media manifest](../../../simulator/media/manifest.csv). The [QA matrix](../../../tests/fixtures/video-evaluation.json) contains questions, observed intervals and annotation history. It stores no operational publication IDs and is never loaded as model detections. Postman generation resolves each recording's hash to the publication installed by the same SQL seed as the local application.

```bash
make install
.venv/bin/python scripts/build_api_docs.py
make docs-check
```

Documentation generation uses only an isolated in-memory SQLite database. It does not connect to an installed runtime, log into accounts or call providers. Local PostgreSQL remains the runtime source of truth.

## Execution evidence

The [historical server receipt](../../assets/storage/video-evaluation-verification.json) documents the earlier server evaluation and its retired groups. It is not a result for the current local dataset. Fresh live-model and physical Android/glasses validation require a separate run against the initialized local installation.
