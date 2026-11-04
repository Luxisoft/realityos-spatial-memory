"""Shared publication classification examples for both Postman destinations."""

import json

CLASSIFICATION = {"category_id": "{{category_id}}", "tag_ids": ["{{tag_id}}"]}


def classification_examples(examples, notes):
    for name in ("POST /v1/gallery", "POST /v1/gallery/{post_id}/share"):
        if name in examples:
            examples[name].update(CLASSIFICATION)
    examples["POST /v1/groups/{workspace_id}/publications/import"].update(
        classifications={"{{post_id}}": CLASSIFICATION}
    )
    examples["POST /v1/me/storage-connections/{connection_id}/imports"].update(
        classifications={"{{storage_object_key}}": CLASSIFICATION}
    )
    examples["POST /v1/groups"].update(categories=["Equipment"], tags=["Reviewed"])
    examples["POST /v1/groups/{workspace_id}/publication-catalog/{kind}"] = {
        "name": "Equipment"
    }
    examples["PATCH /v1/groups/{workspace_id}/publication-catalog/{term_id}"] = {
        "name": "Equipment",
        "active": True,
    }
    for name in (
        "POST /v1/me/publication-uploads/{upload_id}/classify",
        "PATCH /v1/gallery/{post_id}/classification",
    ):
        examples[name] = dict(CLASSIFICATION)
    selection = (
        " Read GET /v1/groups/{workspace_id}/publication-catalog and explicitly choose an "
        "active category_id and one or more tag IDs from that destination group. "
        "tag_ids is a JSON array; multipart uses its JSON serialization in a text field."
    )
    for name in (
        "POST /v1/gallery",
        "POST /v1/gallery/{post_id}/share",
        "POST /v1/groups/{workspace_id}/publications/import",
        "POST /v1/me/publication-uploads",
        "PATCH /v1/gallery/{post_id}/classification",
        "POST /v1/me/publication-uploads/{upload_id}/classify",
    ):
        notes[name] = notes.get(name, "") + selection
    notes["POST /v1/me/storage-connections/{connection_id}/imports"] += (
        " classifications is keyed by object key. Omit an entry to keep that file private in "
        "awaiting_classification; the connection owner then selects values using the classify "
        "endpoint. Synchronization never selects catalog values automatically."
    ) + selection
    notes["GET /v1/gallery/page"] = (
        "Filters apply before pagination: category_ids, tag_ids and owner_ids are repeatable. "
        "Different filters use AND; choices in one filter use OR. published_from is inclusive "
        "and published_before exclusive, both with timezones. description_q matches literal "
        "description/note text without case sensitivity. Restart without a cursor after changes."
    )


def classification_form(name, fields):
    if name not in {
        "POST /v1/me/publication-uploads",
    }:
        return
    for field in fields:
        if field["key"] == "category_id":
            field.update(value="{{category_id}}", disabled=False)
        elif field["key"] == "tag_ids":
            field.update(value=json.dumps(["{{tag_id}}"]), disabled=False)
