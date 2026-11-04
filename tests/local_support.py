"""Read test identities from the same database used by the application."""

from collections import OrderedDict

from app.local.access import list_accounts
from app.social_features.models import Publication
from app.workspaces.models import Record
from sqlalchemy import select


def catalog(client):
    groups = OrderedDict()
    with client.app.state.database.session_factory() as db:
        for account in list_accounts(db):
            group = groups.setdefault(
                account["workspace_id"],
                {
                    "id": account["workspace_id"],
                    "name": account["workspace_name"],
                    "users": [],
                    "records": {},
                    "publications": {},
                },
            )
            group["users"].append(account)
        for record in db.scalars(select(Record).order_by(Record.external_id)):
            if str(record.workspace_id) in groups:
                groups[str(record.workspace_id)]["records"][record.external_id] = str(
                    record.id
                )
        for post in db.scalars(
            select(Publication).where(Publication.source == "local-evaluation")
        ):
            if str(post.workspace_id) in groups:
                group = groups[str(post.workspace_id)]
                slug, identifier = post.source_ref.split(":", 1)
                group["slug"] = group["media_group"] = slug
                group["publications"][identifier] = str(post.id)
    return {"groups": list(groups.values())}
