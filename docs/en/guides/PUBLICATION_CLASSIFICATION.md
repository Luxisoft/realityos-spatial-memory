# Publication catalogs, classification and filters

[Español](../../es/guides/PUBLICATION_CLASSIFICATION.md) · [Project](../README.md) · [API](../api/API.md)

## Each group's catalog

The group owner adds categories and tags during group creation and can rename, archive or restore them under Manage group. Other members can read and select these values without editing the catalog. Values have group-specific identifiers; matching names across groups do not share permissions or identity.

Publishing requires one category and between one and twenty active tags from the selected group. Written or transcribed notes remain optional. Changing groups clears the selection. An empty catalog blocks publication and explains that the group owner must complete it.

The categories and tags in the two local groups have authored Spanish and English names saved in the database. Categories, tags, thumbnails, filters and the viewer select the saved language without translating when a screen opens. Identifiers and associations stay unchanged. Prepared publications, records and descriptive profile fields also retain both versions in the database.

The reviewed copy and classification associations live in the versioned SQL seed under `simulator/database/` and are installed once, without recreating deleted rows or replacing owner edits. No new service, model, queue or automatic translator is involved. Proper names, identifiers and dates are unchanged. Later edits keep the owner's wording and stop showing outdated copy that no longer matches. Archiving preserves existing publication labels and historical filter options while preventing new selections. Manual classification does not become visual evidence or replace object analysis.

## Thumbnails and filtering

Thumbnails show the category and up to two tags, with `+N` for additional tags. The viewer shows the complete classification. Videos have a play icon. The former source badge “MEDIA/Archivo” is removed while internal provenance is retained.

The filter button contains only an icon and an accessibility description. Its dropdown includes categories, tags, authors, From/Through dates and description or note text. Apply restarts pagination; Clear removes the criteria. Changing groups clears filters; opening and closing the viewer preserves them.

Different criteria use AND; multiple choices within one selector use OR. Dates cover complete days in the phone's timezone. Options and results come from all authorized content, including publications beyond the currently loaded thumbnails.

## API

All routes require authentication and enforce the relevant group scope.

| Operation | Contract |
| --- | --- |
| Read catalog | `GET /v1/groups/{workspace_id}/publication-catalog` returns `categories`, `tags` and `can_manage`. |
| Create value | `POST /v1/groups/{workspace_id}/publication-catalog/{kind}`, with `kind=category` or `tag` and `{"name":"Public spaces"}`. Owner only. |
| Rename/archive/restore | `PATCH /v1/groups/{workspace_id}/publication-catalog/{term_id}`, with `name` and `active`. Owner only. |
| Publish or upload | Supply `category_id` and `tag_ids`. In JSON, `tag_ids` is a UUID array; in multipart, it is a text field containing that JSON array. |
| Correct classification | `PATCH /v1/gallery/{post_id}/classification`, with `category_id` and `tag_ids`. Author only. |
| Filter options | `GET /v1/gallery/filter-options`, optionally with `workspace_id`. Returns only values and authors from visible publications. |
| Read publications | `GET /v1/gallery/page` supports repeatable `category_ids`, `tag_ids`, `owner_ids`, plus `published_from`, `published_before` and `description_q`, alongside group and cursor parameters. |

`published_from` is inclusive and `published_before` exclusive; both require a timezone. The phone converts Through to the beginning of the next day. Text matching is case-insensitive and treats `%` and `_` literally.

Copying through `/v1/groups/{workspace_id}/publications/import` accepts `publication_ids` and a `classifications` object keyed by publication ID. Each entry supplies `category_id` and `tag_ids` from the destination group. The app supports individual selection or applying a selection to the batch. Original bytes remain shared and interactions remain independent.

## Imports and synchronization

`POST /v1/me/storage-connections/{connection_id}/imports` accepts `classifications` keyed by object key. An entry with valid classification proceeds to processing. An unclassified file remains in `awaiting_classification`, with private BYTEA originals and no visible publication.

Folder synchronization every 15 minutes uses this same state for new files. In Connections, the owner reviews each preview and chooses its classification. The equivalent API is `POST /v1/me/publication-uploads/{upload_id}/classify`, supplying `category_id` and `tag_ids`. Analysis and any required duplicate confirmation follow.

Retries and subsequent synchronization do not approve pending candidates. Ownership, membership, catalog and source validity are rechecked. Disconnecting or changing the source cancels its candidates and preserves existing retirement rules without deleting remote objects.

## Local initialization and subsequent changes

The shared SQL seed installs the two group catalogs and classifies all 25 prepared publications in the same application tables used by normal uploads and queries. There is no separate classification manifest or publication database. Installation receipts prevent restart from recreating deleted rows or replacing owner edits.

Subsequent corrections use the authenticated catalog and classification APIs above. They preserve original media and enforce group ownership, membership and author permissions. Server storage import and synchronization are available only in the server composition; local evaluation imports its organized fixture bytes directly into BYTEA.
