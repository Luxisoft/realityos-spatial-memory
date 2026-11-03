import io

from app.faces import FaceEnrollment
from app.models import (
    CaptureSession,
    MediaAsset,
    MediaKind,
    Role,
    User,
    Workspace,
    WorkspaceMember,
)
from app.security import create_access_token, hash_password
from PIL import Image


def _png(color: str) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (64, 48), color).save(output, format="PNG")
    return output.getvalue()


def _setup_pair(client):
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).first()
        other = User(
            email="face-other@test.invalid",
            display_name="Face Other",
            password_hash=hash_password("password123456"),
        )
        db.add(other)
        db.flush()
        workspace = Workspace(name="Face Team", created_by_id=owner.id)
        db.add(workspace)
        db.flush()
        db.add(
            WorkspaceMember(
                workspace_id=workspace.id, user_id=owner.id, role=Role.ADMIN
            )
        )
        db.add(
            WorkspaceMember(
                workspace_id=workspace.id, user_id=other.id, role=Role.QUERY
            )
        )
        db.commit()
        settings = client.app.state.settings
        return {
            "workspace_id": str(workspace.id),
            "owner_headers": {
                "Authorization": "Bearer " + create_access_token(owner.id, settings)
            },
            "other_headers": {
                "Authorization": "Bearer " + create_access_token(other.id, settings)
            },
        }


def _consent(client, headers):
    response = client.post("/v1/faces/consent", headers=headers, json={"confirm": True})
    assert response.status_code == 200, response.text


def _enroll_photo(client, headers, color: str):
    data = _png(color)
    response = client.request(
        "POST",
        "/v1/faces/profile-photo",
        headers=headers,
        files={"file": ("face.png", data, "image/png")},
    )
    assert response.status_code == 201, response.text
    return data, response.json()


def _search_probe(client, headers, workspace_id: str, data: bytes):
    return client.request(
        "POST",
        "/v1/faces/search",
        headers=headers,
        data={"workspace_id": workspace_id},
        files={"probe": ("probe.png", data, "image/png")},
    )


def test_faces_require_consent(client):
    env = _setup_pair(client)
    blue = _png("blue")
    assert (
        client.request(
            "POST",
            "/v1/faces/profile-photo",
            headers=env["owner_headers"],
            files={"file": ("face.png", blue, "image/png")},
        ).status_code
        == 403
    )
    assert (
        _search_probe(
            client, env["owner_headers"], env["workspace_id"], blue
        ).status_code
        == 403
    )
    assert (
        client.get("/v1/faces/consent", headers=env["owner_headers"]).json()[
            "consented"
        ]
        is False
    )
    assert (
        client.post(
            "/v1/faces/consent", headers=env["owner_headers"], json={"confirm": False}
        ).status_code
        == 422
    )


def test_enroll_and_ranked_search(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    blue, owner_enroll = _enroll_photo(client, env["owner_headers"], "blue")
    red, _ = _enroll_photo(client, env["other_headers"], "black")
    assert owner_enroll["faces_enrolled"] >= 1
    assert owner_enroll["simulated"] is True

    result = _search_probe(
        client, env["owner_headers"], env["workspace_id"], blue
    ).json()
    assert result["found"] is True
    assert result["simulated"] is True
    assert result["matches"][0]["display_name"] == "Admin Demo"
    assert result["matches"][0]["similarity"] == 1.0
    assert result["matches"] == sorted(
        result["matches"], key=lambda item: item["similarity"], reverse=True
    )

    result = _search_probe(
        client, env["owner_headers"], env["workspace_id"], red
    ).json()
    assert result["matches"][0]["display_name"] == "Face Other"

    unknown = _search_probe(
        client, env["owner_headers"], env["workspace_id"], _png("green")
    ).json()
    assert unknown["found"] is False
    assert unknown["matches"] == []


def test_rank_stage_tracks_winning_probe_face_per_user():
    import struct
    import uuid as uuidlib

    from app.faces import DetectedFace, _rank_stage

    def vec(first: float, second: float) -> bytes:
        return struct.pack("<128f", first, second, *([0.0] * 126))

    left = DetectedFace(
        bounding_box={"x": 0.0, "y": 0.0, "width": 0.5, "height": 0.5},
        embedding=vec(1.0, 0.0),
        quality=0.9,
    )
    right = DetectedFace(
        bounding_box={"x": 0.5, "y": 0.0, "width": 0.5, "height": 0.5},
        embedding=vec(0.0, 1.0),
        quality=0.9,
    )
    user_a, user_b = uuidlib.uuid4(), uuidlib.uuid4()
    enrollments = [
        FaceEnrollment(
            user_id=user_a,
            media_asset_id=uuidlib.uuid4(),
            embedding_model="mock",
            embedding=vec(1.0, 0.0),
            bounding_box={},
            quality=0.9,
        ),
        FaceEnrollment(
            user_id=user_b,
            media_asset_id=uuidlib.uuid4(),
            embedding_model="mock",
            embedding=vec(0.0, 1.0),
            bounding_box={},
            quality=0.9,
        ),
    ]
    ranked = _rank_stage([left, right], enrollments, 0.5, 20)
    assert {user_id: probe_index for user_id, _, _, probe_index in ranked} == {
        user_a: 0,
        user_b: 1,
    }


def test_search_match_reports_probe_box(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    blue, _ = _enroll_photo(client, env["owner_headers"], "blue")
    result = _search_probe(
        client, env["owner_headers"], env["workspace_id"], blue
    ).json()
    assert result["found"] is True
    match = result["matches"][0]
    assert 0 <= match["probe_face_index"] < result["probe_faces"]
    box = match["probe_box"]
    assert set(box) == {"x", "y", "width", "height"}
    assert all(0.0 <= value <= 1.0 for value in box.values())
    assert box["width"] > 0.0 and box["height"] > 0.0


def _two_face_png() -> bytes:
    from app.faces import MockFaceEngine

    engine = MockFaceEngine()
    for tweak in range(256):
        output = io.BytesIO()
        picture = Image.new("RGB", (64, 48), "purple")
        picture.putpixel((tweak % 64, (tweak // 64) % 48), (tweak, 10, 200))
        picture.save(output, format="PNG")
        data = output.getvalue()
        if len(engine.detect_faces(data)) == 2:
            return data
    raise AssertionError("no two-face fixture found")


def test_group_photo_is_rejected_and_never_matches(client):
    """Companion faces must not be attributed to the uploading user."""

    from app.faces import FaceEnrollment

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    _enroll_photo(client, env["owner_headers"], "blue")
    group = _two_face_png()
    for headers in (env["owner_headers"], env["other_headers"]):
        response = client.request(
            "POST",
            "/v1/faces/profile-photo",
            headers=headers,
            files={"file": ("group.png", group, "image/png")},
        )
        assert response.status_code == 422, response.text

    with client.app.state.database.session_factory() as db:
        # The rejected upload keeps the previous valid selfie untouched.
        assert db.query(FaceEnrollment).count() == 1

    result = _search_probe(
        client, env["owner_headers"], env["workspace_id"], group
    ).json()
    assert result["found"] is False
    assert result["matches"] == []


def test_import_skips_group_photos_but_keeps_portraits(client):
    import uuid as uuidlib

    from app.faces import MockFaceEngine, ingest_media_assets

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    engine = MockFaceEngine()
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        workspace_id = uuidlib.UUID(env["workspace_id"])
        assets = []
        for tag, data in (("group", _two_face_png()), ("portrait", _png("black"))):
            asset = MediaAsset(
                workspace_id=workspace_id,
                capture_session_id=None,
                kind=MediaKind.IMAGE,
                mime_type="image/png",
                original_bytes=data,
                sha256=f"import-{tag}",
                byte_size=len(data),
            )
            db.add(asset)
            db.flush()
            assets.append(asset)
        created = ingest_media_assets(db, owner, assets, "facebook-photo", engine)
        db.commit()
        assert len(created) == 1
        assert db.query(FaceEnrollment).count() == 1


def test_match_includes_synced_profile_data(client):
    from app.social import FacebookProfile

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    blue, _ = _enroll_photo(client, env["owner_headers"], "blue")
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        db.add(
            FacebookProfile(
                user_id=owner.id,
                picture_url="https://cdn.invalid/avatar.jpg",
                profile_link="https://facebook.invalid/owner",
            )
        )
        db.commit()
    result = _search_probe(
        client, env["other_headers"], env["workspace_id"], blue
    ).json()
    assert result["matches"][0]["picture_url"] == "https://cdn.invalid/avatar.jpg"
    assert result["matches"][0]["profile_link"] == "https://facebook.invalid/owner"


def _enroll_direct(db, user_id, workspace_id, data: bytes, source: str):
    from app.faces import FaceEnrollment, MockFaceEngine

    engine = MockFaceEngine()
    faces = engine.detect_faces(data)
    asset = MediaAsset(
        workspace_id=workspace_id,
        capture_session_id=None,
        kind=MediaKind.IMAGE,
        mime_type="image/png",
        original_bytes=data,
        sha256="f" * 63 + source[0],
        byte_size=len(data),
    )
    db.add(asset)
    db.flush()
    for index, face in enumerate(faces):
        db.add(
            FaceEnrollment(
                user_id=user_id,
                media_asset_id=asset.id,
                face_index=index,
                embedding_model=engine.name,
                embedding=face.embedding,
                bounding_box=face.bounding_box,
                quality=face.quality,
                source=source,
            )
        )
    db.flush()


def test_search_falls_back_through_stages(client):
    from app.security import create_access_token as _token

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    blue, _ = _enroll_photo(client, env["owner_headers"], "blue")
    red, orange = _png("red"), _png("orange")
    with client.app.state.database.session_factory() as db:
        other = db.query(User).filter(User.email == "face-other@test.invalid").one()
        third = User(
            email="face-third@test.invalid",
            display_name="Face Third",
            password_hash=hash_password("password123456"),
        )
        db.add(third)
        db.flush()
        workspace = db.query(Workspace).filter(Workspace.name == "Face Team").one()
        db.add(
            WorkspaceMember(
                workspace_id=workspace.id, user_id=third.id, role=Role.QUERY
            )
        )
        _enroll_direct(db, other.id, workspace.id, red, "facebook-photo")
        _enroll_direct(db, third.id, workspace.id, orange, "facebook-video")
        db.commit()
        third_headers = {
            "Authorization": "Bearer " + _token(third.id, client.app.state.settings)
        }
    _consent(client, third_headers)

    first = _search_probe(
        client, env["owner_headers"], env["workspace_id"], blue
    ).json()
    assert first["stage"] == 1
    assert first["stages_searched"] == [1]
    assert first["matches"][0]["display_name"] == "Admin Demo"
    assert first["matches"][0]["match_type"] == "direct"

    second = _search_probe(
        client, env["owner_headers"], env["workspace_id"], red
    ).json()
    assert second["stage"] == 2
    assert second["stages_searched"] == [1, 2]
    assert second["matches"][0]["display_name"] == "Face Other"
    assert second["matches"][0]["match_type"] == "possible_acquaintance"

    third_result = _search_probe(
        client, env["owner_headers"], env["workspace_id"], orange
    ).json()
    assert third_result["stage"] == 3
    assert third_result["matches"][0]["display_name"] == "Face Third"
    assert third_result["matches"][0]["match_type"] == "possible_acquaintance"

    missing = _search_probe(
        client, env["owner_headers"], env["workspace_id"], _png("green")
    ).json()
    assert missing["found"] is False
    assert missing["stage"] is None
    assert missing["stages_searched"] == [1, 2, 3]


def test_best_identity_score_unit():
    from app.faces import MockFaceEngine, _best_identity_score

    engine = MockFaceEngine()
    same = engine.detect_faces(_png("teal"))[0].embedding
    other = engine.detect_faces(_png("maroon"))[0].embedding
    assert _best_identity_score([same], [same]) == 1.0
    assert _best_identity_score([same], [other]) < 0.6


def test_verify_identity_simulated_pass(client):
    from datetime import UTC, datetime

    from app.faces import FaceVerification
    from app.social import FacebookProfile

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _, _ = _enroll_photo(client, env["owner_headers"], "blue")
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        db.add(
            FacebookProfile(
                user_id=owner.id, import_status="done", synced_at=datetime.now(UTC)
            )
        )
        db.commit()
    response = client.post("/v1/faces/verify-identity", headers=env["owner_headers"])
    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {
        "verified": True,
        "status": "verified",
        "simulated": True,
        "attempts_remaining": None,
        "retry_after_seconds": None,
    }
    with client.app.state.database.session_factory() as db:
        row = db.query(FaceVerification).one()
        assert row.result == "verified"
        assert row.simulated is True
    assert (
        client.get("/v1/faces/consent", headers=env["owner_headers"]).json()[
            "identity_verified"
        ]
        is True
    )


def test_verify_identity_pending_while_importing(client):
    from datetime import UTC, datetime

    from app.social import FacebookProfile

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _, _ = _enroll_photo(client, env["owner_headers"], "blue")
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        db.add(
            FacebookProfile(
                user_id=owner.id, import_status="running", synced_at=datetime.now(UTC)
            )
        )
        db.commit()
    response = client.post("/v1/faces/verify-identity", headers=env["owner_headers"])
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["verified"] is False


def test_verify_triggers_pending_import_inline(client, monkeypatch):
    from datetime import UTC, datetime

    import httpx
    from app.social import FacebookMedia, FacebookProfile

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _, _ = _enroll_photo(client, env["owner_headers"], "blue")
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        db.add(
            FacebookProfile(
                user_id=owner.id, import_status="pending", synced_at=datetime.now(UTC)
            )
        )
        db.add(
            FacebookMedia(
                fb_id="pending-1",
                user_id=owner.id,
                kind="photo",
                source_url="https://cdn.invalid/pending.jpg",
            )
        )
        db.commit()

    def provider_download(self, url, **kwargs):
        return httpx.Response(
            200, content=_png("teal"), request=httpx.Request("GET", url)
        )

    monkeypatch.setattr(httpx.Client, "get", provider_download)
    response = client.post("/v1/faces/verify-identity", headers=env["owner_headers"])
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "verified"
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        profile = db.get(FacebookProfile, owner.id)
        assert profile.import_status == "done"
        assert profile.imported_photos == 1


def test_verify_identity_requires_capture(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    assert (
        client.post(
            "/v1/faces/verify-identity", headers=env["owner_headers"]
        ).status_code
        == 409
    )


def test_verify_identity_pending_and_keeps_session_without_profile(client):
    from app.faces import FaceVerification
    from app.models import RefreshToken
    from app.security import create_refresh_token

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _, _ = _enroll_photo(client, env["owner_headers"], "blue")
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        _, jti, expires = create_refresh_token(owner.id, client.app.state.settings)
        db.add(RefreshToken(user_id=owner.id, jti=jti, expires_at=expires))
        db.commit()
    # Password accounts without Facebook stay pending, never failed: they use
    # capture + biometric consent, and repeated calls must not lock them.
    for _ in range(3):
        response = client.post(
            "/v1/faces/verify-identity", headers=env["owner_headers"]
        )
        assert response.status_code == 200
        body = response.json()
        assert body["verified"] is False
        assert body["status"] == "pending"
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        assert (
            db.query(RefreshToken)
            .filter(RefreshToken.user_id == owner.id, RefreshToken.revoked_at.is_(None))
            .count()
            == 1
        )
        assert db.query(FaceVerification).count() == 0


def test_verify_identity_mismatch_wipes_selfie(client, monkeypatch):
    import struct
    import uuid as uuidlib
    from datetime import datetime

    from app.faces import MOCK_EMBEDDING_DIM, MOCK_ENGINE_NAME
    from app.social import FacebookProfile

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _enroll_photo(client, env["owner_headers"], "blue")
    zeros = struct.pack(f"<{MOCK_EMBEDDING_DIM}f", *([0.0] * MOCK_EMBEDDING_DIM))
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        db.add(
            FacebookProfile(
                user_id=owner.id, import_status="done", synced_at=datetime.now()
            )
        )
        asset = MediaAsset(
            workspace_id=uuidlib.UUID(env["workspace_id"]),
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=b"fb",
            sha256="fb-reference",
            byte_size=2,
        )
        db.add(asset)
        db.flush()
        db.add(
            FaceEnrollment(
                user_id=owner.id,
                media_asset_id=asset.id,
                face_index=0,
                embedding_model=MOCK_ENGINE_NAME,
                embedding=zeros,
                bounding_box={},
                quality=0.9,
                source="facebook-photo",
            )
        )
        db.commit()

    class LiveStub:
        name = MOCK_ENGINE_NAME
        simulated = False

        def detect_faces(self, image):
            raise AssertionError("verify must not run detection")

    monkeypatch.setattr("app.faces._face_engine_or_503", lambda settings: LiveStub())
    response = client.post("/v1/faces/verify-identity", headers=env["owner_headers"])
    assert response.status_code == 200
    body = response.json()
    assert body["verified"] is False
    assert body["status"] == "failed"
    assert body["attempts_remaining"] == 4
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        remaining = {
            row.source: row
            for row in db.query(FaceEnrollment)
            .filter(FaceEnrollment.user_id == owner.id)
            .all()
        }
        assert "profile" not in remaining
        assert "facebook-photo" in remaining
    status = client.get("/v1/faces/consent", headers=env["owner_headers"]).json()
    assert status["face_capture_done"] is False


def test_verify_identity_accepts_genuine_cross_condition_match(client, monkeypatch):
    import math
    import struct
    import uuid as uuidlib
    from datetime import datetime

    from app.faces import MOCK_EMBEDDING_DIM, MOCK_ENGINE_NAME
    from app.social import FacebookProfile

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    similar = 0.55
    rest = math.sqrt(1.0 - similar**2)
    reference = struct.pack(
        f"<{MOCK_EMBEDDING_DIM}f", 1.0, *([0.0] * (MOCK_EMBEDDING_DIM - 1))
    )
    probe = struct.pack(
        f"<{MOCK_EMBEDDING_DIM}f", similar, rest, *([0.0] * (MOCK_EMBEDDING_DIM - 2))
    )
    synced_at = datetime.now()
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        db.add(
            FacebookProfile(user_id=owner.id, import_status="done", synced_at=synced_at)
        )
        for index, (blob, source) in enumerate(
            [(probe, "profile"), (reference, "facebook-photo")]
        ):
            asset = MediaAsset(
                workspace_id=uuidlib.UUID(env["workspace_id"]),
                kind=MediaKind.IMAGE,
                mime_type="image/png",
                original_bytes=f"genuine-{index}".encode(),
                sha256=f"genuine-{index}",
                byte_size=9,
            )
            db.add(asset)
            db.flush()
            db.add(
                FaceEnrollment(
                    user_id=owner.id,
                    media_asset_id=asset.id,
                    face_index=0,
                    embedding_model=MOCK_ENGINE_NAME,
                    embedding=blob,
                    bounding_box={},
                    quality=0.9,
                    source=source,
                )
            )
        db.commit()

    class LiveStub:
        name = MOCK_ENGINE_NAME
        simulated = False

        def detect_faces(self, image):
            raise AssertionError("verify must not run detection")

    monkeypatch.setattr("app.faces._face_engine_or_503", lambda settings: LiveStub())
    response = client.post("/v1/faces/verify-identity", headers=env["owner_headers"])
    assert response.status_code == 200
    assert response.json()["verified"] is True
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        assert (
            db.query(FaceEnrollment)
            .filter(
                FaceEnrollment.user_id == owner.id,
                FaceEnrollment.source == "profile",
            )
            .count()
            == 1
        )
    status = client.get("/v1/faces/consent", headers=env["owner_headers"]).json()
    assert status["face_capture_done"] is True
    assert status["identity_verified"] is True


def test_fresh_login_clears_selfie_for_new_capture(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _enroll_photo(client, env["owner_headers"], "blue")
    status = client.get("/v1/faces/consent", headers=env["owner_headers"]).json()
    assert status["face_capture_done"] is True
    response = client.post("/v1/me/capture-profile", headers=env["owner_headers"])
    assert response.status_code == 200, response.text
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        assert (
            db.query(FaceEnrollment)
            .filter(
                FaceEnrollment.user_id == owner.id,
                FaceEnrollment.source == "profile",
            )
            .count()
            == 0
        )
    status = client.get("/v1/faces/consent", headers=env["owner_headers"]).json()
    assert status["face_capture_done"] is False


def _live_verify_post(client, monkeypatch, headers):
    from app.faces import MOCK_ENGINE_NAME

    class LiveStub:
        name = MOCK_ENGINE_NAME
        simulated = False

        def detect_faces(self, image):
            raise AssertionError("verify must not run detection")

    with monkeypatch.context() as scoped:
        scoped.setattr("app.faces._face_engine_or_503", lambda settings: LiveStub())
        return client.post("/v1/faces/verify-identity", headers=headers)


def _facebook_reference(client, env, embedding, tag="lockout"):
    import uuid as uuidlib
    from datetime import datetime

    from app.faces import MOCK_ENGINE_NAME
    from app.social import FacebookProfile

    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        if db.get(FacebookProfile, owner.id) is None:
            db.add(
                FacebookProfile(
                    user_id=owner.id, import_status="done", synced_at=datetime.now()
                )
            )
        asset = MediaAsset(
            workspace_id=uuidlib.UUID(env["workspace_id"]),
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=tag.encode(),
            sha256=f"fb-{tag}",
            byte_size=len(tag),
        )
        db.add(asset)
        db.flush()
        enrollment = FaceEnrollment(
            user_id=owner.id,
            media_asset_id=asset.id,
            face_index=0,
            embedding_model=MOCK_ENGINE_NAME,
            embedding=embedding,
            bounding_box={},
            quality=0.9,
            source="facebook-photo",
        )
        db.add(enrollment)
        db.commit()
        return enrollment.id


def _set_reference_embedding(client, enrollment_id, embedding):
    with client.app.state.database.session_factory() as db:
        db.get(FaceEnrollment, enrollment_id).embedding = embedding
        db.commit()


def _zero_embedding():
    import struct

    from app.faces import MOCK_EMBEDDING_DIM

    return struct.pack(f"<{MOCK_EMBEDDING_DIM}f", *([0.0] * MOCK_EMBEDDING_DIM))


def test_verify_identity_locks_after_five_failures(client, monkeypatch):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _facebook_reference(client, env, _zero_embedding())
    for attempt in range(5):
        _enroll_photo(client, env["owner_headers"], "blue")
        body = _live_verify_post(client, monkeypatch, env["owner_headers"]).json()
        if attempt < 4:
            assert body["status"] == "failed"
            assert body["attempts_remaining"] == 4 - attempt
        else:
            assert body["status"] == "locked"
            assert body["attempts_remaining"] == 0
            assert 0 < body["retry_after_seconds"] <= 30 * 60
    locked = _live_verify_post(client, monkeypatch, env["owner_headers"]).json()
    assert locked["status"] == "locked"
    assert locked["retry_after_seconds"] is not None


def test_verify_identity_success_resets_failure_chain(client, monkeypatch):
    from datetime import UTC, datetime, timedelta

    from app.faces import FaceVerification, _mock_embedding

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    reference_id = _facebook_reference(client, env, _zero_embedding(), tag="reset")
    for _ in range(4):
        _enroll_photo(client, env["owner_headers"], "blue")
        body = _live_verify_post(client, monkeypatch, env["owner_headers"]).json()
        assert body["status"] == "failed"
    # Keep the old failures inside the lockout window but before the success,
    # so only the reset logic can exclude them (deterministic on any DB clock).
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        old = datetime.now(UTC) - timedelta(minutes=25)
        for row in (
            db.query(FaceVerification)
            .filter(
                FaceVerification.user_id == owner.id,
                FaceVerification.result == "failed",
            )
            .all()
        ):
            row.created_at = old
        db.commit()
    blue, _ = _enroll_photo(client, env["owner_headers"], "blue")
    _set_reference_embedding(client, reference_id, _mock_embedding(blue, 0))
    assert (
        _live_verify_post(client, monkeypatch, env["owner_headers"]).json()["verified"]
        is True
    )
    _set_reference_embedding(client, reference_id, _zero_embedding())
    body = _live_verify_post(client, monkeypatch, env["owner_headers"]).json()
    assert body["status"] == "failed"
    assert body["attempts_remaining"] == 4


def _spoof_png(array) -> bytes:
    import numpy as np
    from PIL import Image

    output = io.BytesIO()
    Image.fromarray(np.asarray(array, dtype="uint8")).save(output, format="PNG")
    return output.getvalue()


def test_spoof_uniform_image_is_blurry():
    import numpy as np
    from app.faces import assess_spoof_risk

    data = _spoof_png(np.full((128, 128, 3), 128))
    result = assess_spoof_risk(data, {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0})
    assert result.risk == 0.5
    assert result.reasons == ["blurry"]


def test_spoof_natural_noise_passes():
    import numpy as np
    from app.faces import assess_spoof_risk

    rng = np.random.default_rng(7)
    data = _spoof_png(rng.integers(0, 256, (128, 128, 3)))
    result = assess_spoof_risk(data, {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0})
    assert result.risk == 0.0
    assert result.reasons == []


def test_spoof_screen_pattern_is_flagged():
    import numpy as np
    from app.faces import assess_spoof_risk

    columns = np.tile([100, 156], (128, 64))
    data = _spoof_png(np.stack([columns] * 3, axis=-1))
    result = assess_spoof_risk(data, {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0})
    assert result.risk == 0.4
    assert result.reasons == ["screen_moire"]


def test_spoof_glare_is_flagged():
    import numpy as np
    from app.faces import assess_spoof_risk

    frame = np.full((128, 128, 3), 128)
    frame[48:80, 48:80] = 255
    data = _spoof_png(frame)
    result = assess_spoof_risk(data, {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0})
    assert "glare" in result.reasons
    assert result.risk >= 0.3


def test_spoof_respects_exif_orientation():
    import numpy as np
    from app.faces import assess_spoof_risk
    from PIL import Image

    rows = np.tile([[100], [156]], (32, 64))
    picture = Image.fromarray(np.asarray(np.stack([rows] * 3, axis=-1), dtype="uint8"))
    box = {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}

    plain = io.BytesIO()
    picture.save(plain, format="JPEG", quality=95)
    assert assess_spoof_risk(plain.getvalue(), box).reasons == []

    exif = Image.Exif()
    exif[274] = 6
    rotated = io.BytesIO()
    picture.save(rotated, format="JPEG", quality=95, exif=exif)
    assert assess_spoof_risk(rotated.getvalue(), box).reasons == ["screen_moire"]


def test_spoof_tiny_face_is_rejected():
    import numpy as np
    from app.faces import assess_spoof_risk

    data = _spoof_png(np.full((128, 128, 3), 128))
    result = assess_spoof_risk(
        data, {"x": 0.0, "y": 0.0, "width": 0.05, "height": 0.05}
    )
    assert result.risk == 1.0
    assert result.reasons == ["face_too_small"]


def test_live_engine_pipeline_when_available():
    import os

    import pytest

    try:
        from app.faces import FaceEngineError, InsightFaceEngine
    except ImportError:
        pytest.skip("insightface is not installed")
    if not os.path.isdir(os.path.expanduser("~/.insightface/models/buffalo_l")):
        pytest.skip("buffalo_l models are not downloaded")
    engine = InsightFaceEngine()
    assert engine.simulated is False
    assert engine.detect_faces(_png("gray")) == []
    with pytest.raises(FaceEngineError):
        engine.detect_faces(b"junk-bytes")


def test_face_capture_flag_follows_profile_enrollment(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    assert (
        client.get("/v1/faces/consent", headers=env["owner_headers"]).json()[
            "face_capture_done"
        ]
        is False
    )
    _, _ = _enroll_photo(client, env["owner_headers"], "blue")
    assert (
        client.get("/v1/faces/consent", headers=env["owner_headers"]).json()[
            "face_capture_done"
        ]
        is True
    )


def test_profile_photo_replaces_previous_selfie(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _, first = _enroll_photo(client, env["owner_headers"], "blue")
    _, second = _enroll_photo(client, env["owner_headers"], "black")
    assert first["media_id"] != second["media_id"]
    with client.app.state.database.session_factory() as db:
        selfies = [
            asset
            for asset in db.query(MediaAsset).all()
            if (asset.extra_metadata or {}).get("face_profile")
        ]
        assert len(selfies) == 1
        assert str(selfies[0].id) == second["media_id"]


def test_search_is_read_only(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    blue, _ = _enroll_photo(client, env["owner_headers"], "blue")

    def counts():
        with client.app.state.database.session_factory() as db:
            return (
                db.query(MediaAsset).count(),
                db.query(CaptureSession).count(),
                db.query(FaceEnrollment).count(),
            )

    before = counts()
    response = _search_probe(client, env["owner_headers"], env["workspace_id"], blue)
    assert response.status_code == 200
    assert counts() == before


def test_workspace_isolation(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    with client.app.state.database.session_factory() as db:
        outsider = User(
            email="face-outsider@test.invalid",
            display_name="Outsider",
            password_hash=hash_password("password123456"),
        )
        db.add(outsider)
        db.commit()
        outsider_headers = {
            "Authorization": "Bearer "
            + create_access_token(outsider.id, client.app.state.settings)
        }
    _consent(client, outsider_headers)
    outsider_png, _ = _enroll_photo(client, outsider_headers, "purple")

    result = _search_probe(
        client, env["owner_headers"], env["workspace_id"], outsider_png
    ).json()
    assert all(match["display_name"] != "Outsider" for match in result["matches"])
    assert (
        _search_probe(
            client, outsider_headers, env["workspace_id"], outsider_png
        ).status_code
        == 403
    )


def test_revoke_removes_enrollments_and_matches(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    _, _ = _enroll_photo(client, env["owner_headers"], "blue")
    red, _ = _enroll_photo(client, env["other_headers"], "black")

    revoked = client.request(
        "DELETE", "/v1/faces/consent", headers=env["other_headers"]
    )
    assert revoked.status_code == 200
    assert revoked.json()["revoked"] is True
    assert revoked.json()["enrollments_deleted"] >= 1

    result = _search_probe(
        client, env["owner_headers"], env["workspace_id"], red
    ).json()
    assert all(match["display_name"] != "Face Other" for match in result["matches"])
    assert (
        client.get("/v1/faces/enrollments", headers=env["other_headers"]).json() == []
    )


def test_enroll_capture_is_idempotent_and_owner_only(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    raw = _png("blue")
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        workspace = db.query(Workspace).filter(Workspace.name == "Face Team").one()
        session = CaptureSession(workspace_id=workspace.id, created_by_id=owner.id)
        db.add(session)
        db.flush()
        asset = MediaAsset(
            workspace_id=workspace.id,
            capture_session_id=session.id,
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=raw,
            sha256="b" * 64,
            byte_size=len(raw),
        )
        db.add(asset)
        db.commit()
        media_id = str(asset.id)

    first = client.post(
        "/v1/faces/enroll", headers=env["owner_headers"], json={"media_id": media_id}
    )
    second = client.post(
        "/v1/faces/enroll", headers=env["owner_headers"], json={"media_id": media_id}
    )
    assert first.status_code == second.status_code == 201
    assert first.json()["enrollment_ids"] == second.json()["enrollment_ids"]
    assert (
        client.post(
            "/v1/faces/enroll",
            headers=env["other_headers"],
            json={"media_id": media_id},
        ).status_code
        == 403
    )


def test_video_enroll_uses_extracted_frames(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    raw = _png("orange")
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        workspace = db.query(Workspace).filter(Workspace.name == "Face Team").one()
        session = CaptureSession(workspace_id=workspace.id, created_by_id=owner.id)
        db.add(session)
        db.flush()
        video = MediaAsset(
            workspace_id=workspace.id,
            capture_session_id=session.id,
            kind=MediaKind.VIDEO,
            mime_type="video/mp4",
            original_bytes=b"fake-video-bytes",
            sha256="c" * 64,
            byte_size=16,
        )
        db.add(video)
        db.flush()
        video_id = str(video.id)
        frame = MediaAsset(
            workspace_id=workspace.id,
            capture_session_id=session.id,
            parent_asset_id=video.id,
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=raw,
            sha256="d" * 64,
            byte_size=len(raw),
        )
        db.add(frame)
        db.commit()
    assert (
        client.post(
            "/v1/faces/enroll",
            headers=env["owner_headers"],
            json={"media_id": video_id},
        ).status_code
        == 201
    )
    owned = client.get("/v1/faces/enrollments", headers=env["owner_headers"]).json()
    assert owned and all(item["source"] == "frame" for item in owned)

    via_media = client.request(
        "POST",
        "/v1/faces/search",
        headers=env["owner_headers"],
        data={"workspace_id": env["workspace_id"], "media_id": video_id},
    )
    assert via_media.status_code == 200
    assert via_media.json()["found"] is True


def test_video_without_frames_conflicts(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    with client.app.state.database.session_factory() as db:
        owner = db.query(User).filter(User.email == "admin@example.test").one()
        workspace = db.query(Workspace).filter(Workspace.name == "Face Team").one()
        session = CaptureSession(workspace_id=workspace.id, created_by_id=owner.id)
        db.add(session)
        db.flush()
        video = MediaAsset(
            workspace_id=workspace.id,
            capture_session_id=session.id,
            kind=MediaKind.VIDEO,
            mime_type="video/mp4",
            original_bytes=b"fake-video-bytes",
            sha256="e" * 64,
            byte_size=16,
        )
        db.add(video)
        db.commit()
        video_id = str(video.id)
    assert (
        client.post(
            "/v1/faces/enroll",
            headers=env["owner_headers"],
            json={"media_id": video_id},
        ).status_code
        == 409
    )


def test_thumbnail_and_own_list(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    _, enrolled = _enroll_photo(client, env["owner_headers"], "blue")
    owned = client.get("/v1/faces/enrollments", headers=env["owner_headers"]).json()
    assert len(owned) == len(enrolled["enrollment_ids"]) >= 1

    assert owned[0]["thumbnail_url"] is None
    path = f"/v1/faces/enrollments/{owned[0]['id']}/thumbnail"
    for headers in (env["owner_headers"], env["other_headers"]):
        assert client.get(path, headers=headers).status_code == 404

    with client.app.state.database.session_factory() as db:
        outsider = User(
            email="face-thumb-outsider@test.invalid",
            display_name="Thumb Outsider",
            password_hash=hash_password("password123456"),
        )
        db.add(outsider)
        db.commit()
        outsider_headers = {
            "Authorization": "Bearer "
            + create_access_token(outsider.id, client.app.state.settings)
        }
    _consent(client, outsider_headers)
    assert client.get(path, headers=outsider_headers).status_code == 404


def test_guest_users_cannot_use_face_search(client):
    env = _setup_pair(client)
    guest = client.post("/v1/auth/guest", json={"device_id": "face-guest-device"})
    assert guest.status_code == 200, guest.text
    headers = {"Authorization": "Bearer " + guest.json()["access_token"]}
    _consent(client, headers)
    data = _png("green")
    enroll = client.request(
        "POST",
        "/v1/faces/profile-photo",
        headers=headers,
        files={"file": ("face.png", data, "image/png")},
    )
    assert enroll.status_code == 403, enroll.text
    assert "Guest users" in enroll.text
    search = _search_probe(client, headers, env["workspace_id"], data)
    assert search.status_code == 403, search.text
    assert "Guest users" in search.text


def _search_video_probe(client, headers, workspace_id: str, data: bytes):
    return client.request(
        "POST",
        "/v1/faces/search",
        headers=headers,
        data={"workspace_id": workspace_id},
        files={"probe": ("probe.mp4", data, "video/mp4")},
    )


def test_search_ephemeral_video_probe(client, monkeypatch):
    """A video probe samples bounded frames and never persists probe bytes."""

    from app import faces

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    blue, _ = _enroll_photo(client, env["owner_headers"], "blue")
    _enroll_photo(client, env["other_headers"], "black")
    monkeypatch.setattr(
        faces, "_extract_video_probe_frames", lambda raw, limit: [blue, blue]
    )
    with client.app.state.database.session_factory() as db:
        assets_before = db.query(MediaAsset).count()
    response = _search_video_probe(
        client, env["owner_headers"], env["workspace_id"], b"fake-video"
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["found"] is True
    assert result["probe_frames"] == 2
    assert result["probe_faces"] >= 1
    assert result["matches"][0]["display_name"] == "Admin Demo"
    with client.app.state.database.session_factory() as db:
        assert db.query(MediaAsset).count() == assets_before


def test_search_rejects_invalid_video_probe(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    response = _search_video_probe(
        client, env["owner_headers"], env["workspace_id"], b"not-a-video"
    )
    assert response.status_code == 422


def test_search_rejects_unsupported_probe_mime(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    response = client.request(
        "POST",
        "/v1/faces/search",
        headers=env["owner_headers"],
        data={"workspace_id": env["workspace_id"]},
        files={"probe": ("probe.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 415


def test_search_skips_low_quality_probe_and_foreign_enrollments(client, monkeypatch):
    import struct as structlib

    from app.faces import MOCK_EMBEDDING_DIM, DetectedFace, MockFaceEngine

    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    blue, _ = _enroll_photo(client, env["owner_headers"], "blue")
    with client.app.state.database.session_factory() as db:
        other = db.query(User).filter(User.email == "face-other@test.invalid").one()
        asset = db.query(MediaAsset).first()
        zeros = structlib.pack(f"<{MOCK_EMBEDDING_DIM}f", *([0.0] * MOCK_EMBEDDING_DIM))
        db.add(
            FaceEnrollment(
                user_id=other.id,
                media_asset_id=asset.id,
                face_index=99,
                embedding_model="other-engine",
                embedding=zeros,
                bounding_box={"x": 0.1, "y": 0.1, "width": 0.5, "height": 0.5},
                quality=0.95,
                source="profile",
            )
        )
        db.add(
            FaceEnrollment(
                user_id=other.id,
                media_asset_id=asset.id,
                face_index=100,
                embedding_model=MockFaceEngine.name,
                embedding=zeros,
                bounding_box={},
                quality=0.0,
                source="profile",
            )
        )
        db.commit()
    junk = DetectedFace(
        bounding_box={"x": 0.0, "y": 0.0, "width": 0.0, "height": 0.0},
        embedding=b"",
        quality=0.0,
    )
    real_detect = MockFaceEngine.detect_faces
    monkeypatch.setattr(
        MockFaceEngine,
        "detect_faces",
        lambda self, image: [junk, *real_detect(self, image)],
    )
    result = _search_probe(
        client, env["owner_headers"], env["workspace_id"], blue
    ).json()
    assert result["found"] is True
    assert result["matches"][0]["display_name"] == "Admin Demo"
    assert result["probe_faces"] >= 1
    assert result["probe_frames"] == 1
    assert result["probe_faces_skipped"] >= 1
    assert result["enrollments_skipped"] >= 2


def test_thumbnail_full_size_param(client):
    env = _setup_pair(client)
    _consent(client, env["owner_headers"])
    _consent(client, env["other_headers"])
    output = io.BytesIO()
    Image.new("RGB", (800, 600), "blue").save(output, format="PNG")
    response = client.request(
        "POST",
        "/v1/faces/profile-photo",
        headers=env["owner_headers"],
        files={"file": ("big.png", output.getvalue(), "image/png")},
    )
    assert response.status_code == 201, response.text
    owned = client.get("/v1/faces/enrollments", headers=env["owner_headers"]).json()
    assert owned[0]["thumbnail_url"] is None
    path = f"/v1/faces/enrollments/{owned[0]['id']}/thumbnail"
    for query in ("", "?full_size=false", "?full_size=true"):
        assert client.get(path + query, headers=env["owner_headers"]).status_code == 404
