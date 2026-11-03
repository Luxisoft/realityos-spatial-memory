"""Presentation maintenance must preserve evidence and workspace boundaries."""

import importlib.util
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.accounts.models import PasswordAccount
from app.models import MediaAsset, MediaKind, User, Workspace
from app.social_features.evidence_models import PublicationTranslation
from app.social_features.localizations import (
    display_information,
    stored_rows,
    text_hash,
)
from app.social_features.models import Publication
from app.workspaces.models import Connection, Record, RecordNote
from sqlalchemy import select


def script():
    path = Path(__file__).resolve().parents[1] / "scripts/normalize_scenario_text.py"
    spec = importlib.util.spec_from_file_location("scenario_text", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scoped_copy_translations_idempotency_and_rollback(client):
    module = script()
    with client.app.state.database.session_factory() as db:
        user = db.scalar(select(User))
        rows = []
        for name in (next(iter(module.GROUPS)), "Another workspace"):
            group = Workspace(name=name, created_by_id=user.id)
            db.add(group)
            db.flush()
            connection = Connection(
                workspace_id=group.id,
                created_by_id=user.id,
                name="Source",
                token_hash=str(group.id),
            )
            asset = MediaAsset(
                workspace_id=group.id,
                kind=MediaKind.IMAGE,
                mime_type="image/png",
                original_bytes=b"unchanged",
                byte_size=9,
                sha256="hash",
            )
            db.add_all([connection, asset])
            db.flush()
            record = Record(
                workspace_id=group.id,
                connection_id=connection.id,
                external_id="case-1",
                kind="case",
                title="Caso de prueba 1",
                data={
                    "description": "Expediente ficticio para evaluación del software."
                },
                simulated=True,
                version=7,
                status="active",
                occurred_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            post = Publication(
                owner_id=user.id,
                workspace_id=group.id,
                media_id=asset.id,
                audience="work",
                source="simulator-licensed",
                source_ref=str(group.id),
                caption="[Demo] Notebook",
                search_text="[Demo] Notebook blue",
            )
            db.add_all([record, post])
            db.flush()
            note = RecordNote(
                record_id=record.id,
                actor_id=user.id,
                text="[Simulado] Revisión del turno.",
                occurred_at=datetime.now(UTC),
            )
            db.add(note)
            for language, text in (
                ("en", "[Demo] Notebook"),
                ("es", "[Demo] Cuaderno"),
            ):
                db.add(
                    PublicationTranslation(
                        post_id=post.id,
                        language=language,
                        text_hash=text_hash(post.caption),
                        translated_text=text,
                    )
                )
            rows.append((record, post, asset, note))
        db.commit()
        changes = module.plan(db)
        module.apply_changes(db, changes)
        db.commit()
        record, post, asset, note = rows[0]
        assert record.title == "Caso 1" and record.version == 7 and record.simulated
        assert post.caption == "Notebook" and post.search_text == "Notebook blue"
        assert asset.original_bytes == b"unchanged" and post.media_id == asset.id
        assert note.text == "Revisión del turno."
        localized = display_information(
            stored_rows(db, [post.id]), post.id, post.id, "es", post.caption, "", []
        )
        assert localized["title"] == "Cuaderno"
        assert rows[1][0].title == "Caso de prueba 1"
        assert rows[1][1].caption == "[Demo] Notebook"
        assert not module.plan(db)
        module.apply_changes(db, changes, rollback=True)
        db.commit()
        assert post.caption == "[Demo] Notebook" and record.title == "Caso de prueba 1"
        assert module.plan(db) == changes


def test_concurrent_change_is_not_overwritten(client):
    module = script()
    with client.app.state.database.session_factory() as db:
        user = db.scalar(select(User))
        user.display_name = "RealityOS Demo Admin"
        db.commit()
        changes = module.plan(db)
        user.display_name = "New name chosen by owner"
        db.commit()
        with pytest.raises(ValueError, match="Concurrent change"):
            module.apply_changes(db, changes)
        assert user.display_name == "New name chosen by owner"


def test_qa_notes_are_cleaned_after_caption_was_already_corrected(client):
    module = script()
    with client.app.state.database.session_factory() as db:
        user = db.scalar(select(User))
        group = Workspace(name="Equipo de revisión", created_by_id=user.id)
        db.add(group)
        db.flush()
        asset = MediaAsset(
            workspace_id=group.id,
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=b"unchanged",
            byte_size=9,
            sha256="hash",
        )
        db.add_all(
            [asset, PasswordAccount(user_id=user.id, username="qa-hackathon-admin")]
        )
        db.flush()
        post = Publication(
            owner_id=user.id,
            workspace_id=group.id,
            media_id=asset.id,
            audience="work",
            source="local",
            caption="Workspace desk",
            note_text="Synthetic acceptance fixture. Private QA profile publication.",
        )
        db.add(post)
        db.flush()
        db.add(
            PublicationTranslation(
                post_id=post.id,
                language="es",
                text_hash=text_hash(post.caption),
                translated_text="[QA simulado] Escritorio del espacio de trabajo de aceptación",
            )
        )
        db.commit()
        module.apply_changes(db, module.plan(db))
        db.commit()
        assert post.note_text == "Workspace desk with organized tools and supplies."
        assert (
            db.scalar(select(PublicationTranslation.translated_text))
            == "Escritorio del espacio de trabajo"
        )
        assert not module.plan(db)
