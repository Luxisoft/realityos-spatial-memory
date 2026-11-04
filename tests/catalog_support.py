"""Explicit publication catalog setup for existing integration scenarios."""

import json
import uuid

from app.social_features.classification import add_term
from app.social_features.models import PublicationTerm
from sqlalchemy import select


def classification_for(client, workspace_id, *, multipart=False):
    workspace_id = uuid.UUID(str(workspace_id))
    with client.app.state.database.session_factory() as db:
        values = []
        for kind, name in (("category", "Operations"), ("tag", "Reviewed")):
            term = db.scalar(
                select(PublicationTerm)
                .where(
                    PublicationTerm.workspace_id == workspace_id,
                    PublicationTerm.kind == kind,
                    PublicationTerm.active.is_(True),
                )
                .order_by(PublicationTerm.name_key)
            )
            if term is None:
                term = add_term(db, workspace_id, kind, name)
            values.append(str(term.id))
        db.commit()
    return {
        "category_id": values[0],
        "tag_ids": json.dumps([values[1]]) if multipart else [values[1]],
    }


def classified_destination(client, headers, name="Publications"):
    group = client.post("/v1/groups", headers=headers, json={"name": name}).json()["id"]
    return {"workspace_id": group, **classification_for(client, group, multipart=True)}


def published_item(client, headers, upload_response):
    """Read a completed upload through the same cursor feed used by Android."""
    assert upload_response.status_code == 202, upload_response.text
    upload = upload_response.json()
    assert upload["status"] == "published", upload
    items = client.get(
        f"/v1/gallery/page?workspace_id={upload['workspace_id']}&limit=30", headers=headers
    ).json()["items"]
    return next(item for item in items if item["id"] == upload["result_id"])
