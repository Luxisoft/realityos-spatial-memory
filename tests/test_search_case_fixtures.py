"""Query photos stay offline and never become seeded group content."""

import hashlib
import json
from pathlib import Path

from app.models import MediaAsset
from PIL import Image
from sqlalchemy import select
from test_local_evaluation import evaluation  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "simulator/search-cases"


def manifest():
    return json.loads((CASES / "manifest.json").read_text(encoding="utf-8"))


def test_query_images_are_complete_and_intact():
    data = manifest()
    assert data["purpose"] == "query-only"
    assert not any(data[key] for key in ("import_into_runtime", "publish", "enroll"))
    items = data["items"]
    assert len(items) == 7
    assert len({item["sha256"] for item in items}) == len(items)
    assert {item["path"] for item in items} == {
        path.relative_to(CASES).as_posix() for path in CASES.rglob("*.png")
    }
    for item in items:
        path = (CASES / item["path"]).resolve()
        assert path.is_relative_to(CASES.resolve())
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item["sha256"]
        assert len(raw) == item["bytes"]
        with Image.open(path) as image:
            assert image.format == "PNG"
            assert image.size == (item["width"], item["height"])
            image.verify()


def test_meta_photos_reference_only_the_existing_group_avatars():
    catalog = json.loads(
        (ROOT / "simulator/local/catalog.json").read_text(encoding="utf-8")
    )
    group = next(g for g in catalog["groups"] if g["slug"] == "meta-social")
    users = {user["username"]: user for user in group["users"]}
    items = [item for item in manifest()["items"] if item["group"] == "meta-social"]
    assert len(items) == len(users) == 3
    assert {item["intended_profile"] for item in items} == set(users)
    for item in items:
        user = users[item["intended_profile"]]
        assert item["reference"] == "simulator/" + user["avatar"]
        reference_hash = hashlib.sha256(
            (ROOT / item["reference"]).read_bytes()
        ).hexdigest()
        assert reference_hash == item["reference_sha256"] == user["avatar_sha256"]
        assert item["sha256"] != reference_hash
        assert item["people_count"] == 1
    assert group["publications"] == group["records"] == {}


def test_local_seed_never_imports_query_photos(evaluation):  # noqa: F811
    query_hashes = {item["sha256"] for item in manifest()["items"]}
    with evaluation.app.state.database.session_factory() as db:
        stored_hashes = set(db.scalars(select(MediaAsset.sha256)))
    assert stored_hashes
    assert query_hashes.isdisjoint(stored_hashes)
