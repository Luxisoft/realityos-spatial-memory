"""Build public examples from the local SQL seed in an isolated in-memory database.

No runtime database, provider, private configuration file or account credential is
used. The only JSON input contains independent video QA questions and intervals.
"""

import json
import uuid
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from app.config import Settings
from app.db import Base, Database
from app.local.access import list_accounts
from app.local.bootstrap import seed_evaluation
from app.models import MediaAsset
from app.social_features import evidence_models  # noqa: F401
from app.social_features.models import Publication
from app.workspaces.models import Record
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parents[1]
ACCOUNT_FIELDS = (
    "email",
    "username",
    "password",
    "display_name",
    "user_id",
    "workspace_id",
)


def scenarios_from_database(db, annotations):
    """Resolve all account/resource identifiers from the installed application tables."""
    representatives = {}
    for account in list_accounts(db):
        representatives.setdefault(account["workspace_id"], account)
    scenarios = []
    for account in representatives.values():
        workspace_id = uuid.UUID(account["workspace_id"])
        posts = db.scalars(
            select(Publication)
            .where(
                Publication.workspace_id == workspace_id, Publication.hidden.is_(False)
            )
            .order_by(Publication.source_ref, Publication.id)
        ).all()
        if not posts:
            raise ValueError("A prepared Postman scenario must have a publication.")
        prefix = posts[0].source_ref.split(":", 1)[0].replace("-", "_")
        record = db.scalar(
            select(Record)
            .where(Record.workspace_id == workspace_id)
            .order_by(Record.external_id, Record.id)
            .limit(1)
        )
        videos = []
        for annotation in annotations["videos"]:
            post = db.scalar(
                select(Publication)
                .join(MediaAsset, MediaAsset.id == Publication.media_id)
                .where(
                    Publication.workspace_id == workspace_id,
                    Publication.hidden.is_(False),
                    MediaAsset.sha256 == annotation["sha256"],
                )
            )
            if post:
                videos.append({**annotation, "post_id": str(post.id)})
        post = next(
            (p for p in posts if videos and str(p.id) == videos[0]["post_id"]), posts[0]
        )
        caption = post.display_text.get("caption", {}).get("en") or post.caption
        scenarios.append(
            {
                "prefix": prefix,
                "name": f"{len(scenarios) + 1:02} {account['workspace_name']}",
                "workspace_name": account["workspace_name"],
                "videos": videos,
                "values": {
                    "email": "",
                    "password": "",
                    "username": account["username"],
                    "display_name": account["display_name"],
                    "user_id": account["id"],
                    "workspace_id": account["workspace_id"],
                    "record_id": str(record.id) if record else "",
                    "post_id": str(post.id),
                    "query": videos[0]["queries"][0]["en"]
                    if videos
                    else f"Find {caption}",
                    "record_question": f"Summarize the record for {record.title}."
                    if record
                    else "",
                    "auth_mode": "local-select",
                },
            }
        )
    resolved = {
        video["sha256"] for scenario in scenarios for video in scenario["videos"]
    }
    if resolved != {video["sha256"] for video in annotations["videos"]}:
        raise ValueError(
            "Every active video QA case must resolve to an installed publication."
        )
    return scenarios


@contextmanager
def local_evaluation_database():
    settings = Settings(
        _env_file=None,
        environment="local",
        database_url="sqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        local_login_enabled=True,
        local_evaluation_enabled=True,
        meta_mode="live",
        face_engine="insightface",
        meta_connection_mode="direct",
        meta_gateway_fallback_enabled=False,
        meta_api_base_url="https://api.meta.ai/v1",
        model_api_key="offline-documentation-placeholder",
        enqueue_processing=False,
    )
    with Database(settings.database_url) as database:
        Base.metadata.create_all(database.engine)
        with database.session() as db:
            seed_evaluation(db, settings)
            yield db


@lru_cache(maxsize=1)
def evaluation_dataset():
    annotations = json.loads(
        (ROOT / "tests/fixtures/video-evaluation.json").read_text()
    )
    with local_evaluation_database() as db:
        scenarios = scenarios_from_database(db, annotations)
        publication_count = db.scalar(select(func.count(Publication.id)))
        account_count = len(list_accounts(db))
    default = next(
        (scenario for scenario in scenarios if scenario["videos"]), scenarios[0]
    )
    return {
        "base_url": "http://localhost:8080",
        "publication_count": publication_count,
        "account_count": account_count,
        "scenarios": scenarios,
        "defaults": {
            "server": {field: "" for field in ACCOUNT_FIELDS},
            "localhost": {field: default["values"][field] for field in ACCOUNT_FIELDS},
        },
    }
