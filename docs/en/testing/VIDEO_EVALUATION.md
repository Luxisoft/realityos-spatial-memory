[ES](../../es/testing/VIDEO_EVALUATION.md) · [RealityOS](../README.md) · [Postman](../api/POSTMAN.md)

# Evaluation with real videos

Twelve licensed recordings, four per existing group. They show complete actions with identifiable objects: picking up keys, packing belongings, preparing instruments, transporting samples and inspecting evidence. The scenarios are fictional; analysis and evidence must come from the real provider.

In Postman: **Server requests → 00 Live scenarios → Police / Nursing / Memory → Video …**. Each request includes its account, group and question. Public accounts are listed in [API](../api/API.md#quick-start). In Android, sign in with that account, select its group and use the listed question.

The answer must retrieve the specified publication, a frame inside the interval, the object localized by SAM and the downloadable original. `gallery_matches` contains publication evidence even when `found` is `false`: that field belongs to Register. “Last seen” describes recorded evidence; it does not prove that the object remains there. A saved account language preference overrides the requested language.

## Test matrix

### Police

| Video and author | Owner account | Question | Visible interval |
| --- | --- | --- | --- |
| [10482314](https://www.pexels.com/video/lifting-keys-from-ground-with-pliers-10482314/) · cottonbro studio | `alex-rivera` | Find the keys collected from the ground. | 0–11 s |
| [10482314](https://www.pexels.com/video/lifting-keys-from-ground-with-pliers-10482314/) · cottonbro studio | `alex-rivera` | Find the yellow evidence marker. | 0–9 s |
| [10482446](https://www.pexels.com/video/technician-taking-picture-of-evidence-at-night-10482446/) · cottonbro studio | `alex-rivera` | Find the open evidence collection case. | 0–26.76 s |
| [10482446](https://www.pexels.com/video/technician-taking-picture-of-evidence-at-night-10482446/) · cottonbro studio | `alex-rivera` | Find the barrier tape. | 0–26.76 s |
| [8382402](https://www.pexels.com/video/detective-reviewing-evidences-8382402/) · cottonbro studio | `maya-johnson` | Find the adjustable desk lamp. | 0–8 s |
| [8382402](https://www.pexels.com/video/detective-reviewing-evidences-8382402/) · cottonbro studio | `maya-johnson` | Find the printed photographs on the desk. | 0–8 s |
| [8963860](https://www.pexels.com/video/close-up-footage-of-a-man-using-walkie-talkie-8963860/) · Mikael Blomkvist | `daniel-kim` | Find the handheld communication radio. | 0–7.54 s |
| [8963860](https://www.pexels.com/video/close-up-footage-of-a-man-using-walkie-talkie-8963860/) · Mikael Blomkvist | `daniel-kim` | Find the yellow hearing protection earmuffs around the neck. | 0–7.54 s |

### Nursing

| Video and author | Owner account | Question | Visible interval |
| --- | --- | --- | --- |
| [8413544](https://www.pexels.com/video/syringes-on-metal-tray-8413544/) · SHVETS production | `elena-marquez` | Find the syringes on the tray. | 0–8.4 s |
| [8413544](https://www.pexels.com/video/syringes-on-metal-tray-8413544/) · SHVETS production | `elena-marquez` | Find the metal tweezers beside the tray. | 0–8.4 s |
| [8381611](https://www.pexels.com/video/medical-practitioner-walking-in-the-hallway-while-holding-a-cart-with-samples-of-specimen-8381611/) · Pavel Danilyuk | `elena-marquez` | Find the supply cart in the hallway. | 0–9.68 s |
| [8381611](https://www.pexels.com/video/medical-practitioner-walking-in-the-hallway-while-holding-a-cart-with-samples-of-specimen-8381611/) · Pavel Danilyuk | `elena-marquez` | Find the test tubes on the cart. | 3–9.68 s |
| [6036527](https://www.pexels.com/video/a-person-getting-dental-tools-from-the-drawer-6036527/) · Gustavo Fring | `mateo-rios` | Find the dental instruments inside the drawer. | 0–15.215 s |
| [6036527](https://www.pexels.com/video/a-person-getting-dental-tools-from-the-drawer-6036527/) · Gustavo Fring | `mateo-rios` | Find the forceps in the instrument drawer. | 0–15.215 s |
| [7585003](https://www.pexels.com/video/assisting-with-medical-equipment-7585003/) · cottonbro studio | `sarah-chen` | Find the scissors on the blue cloth. | 0–21.76 s |
| [7585003](https://www.pexels.com/video/assisting-with-medical-equipment-7585003/) · cottonbro studio | `sarah-chen` | Find the mallet among the instruments. | 0–21.76 s |

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

Ask for a violin in each group, in ES and EN: expect `no_match` and no invented evidence. An account from another group must receive 403 when querying the workspace and 403/404 when downloading its publication.

## Provenance and maintenance

Sources, authors, licenses, hashes and duration: [candidate manifest](../../../simulator/real-scenes/video-candidate-manifest.json). Questions, intervals and expected publications: [evaluation annotations](../../../simulator/real-scenes/video-evaluation.json). Annotations were prepared by reviewing the recordings and are never loaded as model detections. Revisions preserve the initial questions that failed. This matrix is a curated demonstration, not a general accuracy measurement. Recordings remain complete, without loops, arbitrary cuts or enlargement from low resolution.

```bash
python scripts/prepare_evaluation_videos.py
# Run inside the authenticated backend runtime:
python scripts/renew_evaluation_videos.py --phase inventory --journal .runtime/video-evaluation/journal.json
python scripts/renew_evaluation_videos.py --phase stage --journal .runtime/video-evaluation/journal.json
python scripts/renew_evaluation_videos.py --phase index --journal .runtime/video-evaluation/journal.json
python scripts/verify_evaluation_videos.py --journal .runtime/video-evaluation/journal.json --output .runtime/video-evaluation/acceptance.json --resume
```

Activation requires 48 positive searches, six negatives, six isolation checks, 12 downloads with matching hashes and visual review of evidence frames. The HTTP receipt alone does not approve that visual review. `activate` also requires private `--receipt` and `--credentials-file` inputs; it verifies bucket originals, binds their provenance and selects the new folder for synchronization every 15 minutes. It preserves all 36 photo identifiers.

The preparation commands above document this release and must not be repeated against its final state. After accepting the replacement, the owner requested deletion of previous videos and unused copies. Cleanup checked exact references and hashes. The journal marks `retired_media_deleted=true`; `rollback` and reactivation of the same release are rejected to prevent recreating deleted media. The HTTP evaluation queries remain available.

## Execution status

Activation completed: **12 videos, 48 ES/EN queries, six negatives, six cross-group checks and 12 verified originals**. Boxes were visually inspected on the actual returned evidence. The [public receipt](../../assets/storage/video-evaluation-verification.json) includes preservation auditing and two full scans of all nine sources. All 36 photos and existing records remain. The owner requested deletion of the 12 previous videos, the rejected candidate and obsolete copies; they are no longer retained for rollback. Physical Android and glasses testing was not performed for this renewal.
