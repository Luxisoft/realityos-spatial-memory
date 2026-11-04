"""Query photos remain local resources and never become seeded group content."""

import csv
import hashlib
from pathlib import Path

from app.accounts.models import PasswordAccount
from app.models import MediaAsset
from app.social_features.models import UserProfile
from PIL import Image
from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1] / "simulator/media"


def query_resources():
    with (ROOT / "manifest.csv").open() as stream:
        return [
            row
            for row in csv.DictReader(stream)
            if row["path"].startswith("regression/search/")
        ]


def test_query_images_are_complete_and_intact():
    resources = query_resources()
    assert len(resources) == 7
    assert len({item["sha256"] for item in resources}) == 7
    for item in resources:
        path = ROOT / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        with Image.open(path) as image:
            assert image.format == "PNG"
            image.verify()


def test_meta_query_images_are_separate_from_the_existing_avatars(evaluation):
    resources = [row for row in query_resources() if "/meta-social/" in row["path"]]
    assert len(resources) == 3
    with evaluation.app.state.database.session_factory() as db:
        for row in resources:
            username = Path(row["path"]).stem
            profile = db.scalar(
                select(UserProfile)
                .join(PasswordAccount, PasswordAccount.user_id == UserProfile.user_id)
                .where(PasswordAccount.username == username)
            )
            assert profile is not None
            avatar = db.get(MediaAsset, profile.avatar_media_id)
            assert avatar.sha256 != row["sha256"]


def test_initialization_never_imports_query_photos(evaluation):
    query_hashes = {row["sha256"] for row in query_resources()}
    with evaluation.app.state.database.session_factory() as db:
        stored_hashes = set(db.scalars(select(MediaAsset.sha256)))
    assert stored_hashes and query_hashes.isdisjoint(stored_hashes)
