"""Normalize visible scenario copy, preserving provenance, permissions and media.

Dry run by default. Apply requires a private JSON journal; --rollback restores
only fields still equal to this operation's output. Record versions and biometric
authorization are untouched: these are presentation corrections, not new evidence.
"""

import argparse
import json
import re
import uuid
from collections import Counter
from pathlib import Path

from app.accounts.models import PasswordAccount
from app.config import get_settings
from app.db import Database
from app.models import User, Workspace
from app.social_features.evidence_models import PublicationTranslation
from app.social_features.localizations import text_hash
from app.social_features.models import Publication
from app.storage.models import StorageConnection
from app.workspaces.models import Connection, Record, RecordNote
from sqlalchemy import inspect, select

GROUPS = {
    "Pacific Ridge Police Department": "Casos, observaciones y evidencias del equipo policial.",
    "California Valley Medical Center": "Expedientes, atención y seguimiento del equipo de enfermería.",
    "Sonoran Neurological Institute": "Expedientes, recordatorios y seguimiento del equipo de atención.",
}
REPLACEMENTS = {
    "Caso de prueba": "Caso",
    "Expediente ficticio para evaluación del software.": "Expediente de seguimiento con observaciones y registros relacionados.",
    "Persona ficticia, no cuenta de acceso.": "Información personal y registros de atención relacionados.",
    "Sesión de prueba de revisión contextual y seguimiento, sin decisiones clínicas reales.": "Sesión de revisión contextual y seguimiento.",
    "envase de prueba": "envase de medicación",
    "Prescripción ficticia": "Prescripción",
    "Alerta ficticia de alergia": "Alerta de alergia",
    "Administración ficticia previamente registrada": "Administración previamente registrada",
    "DEMO MEDICINE": "Medicamento registrado",
    "TEST-HOSPITAL-": "HOSPITAL-",
    "TEST-MEMORY-": "MEMORY-",
    " para la evaluación.": ".",
    "Acceptance workspace desk": "Workspace desk",
    "Synthetic acceptance fixture. Private QA profile publication.": "Workspace desk with organized tools and supplies.",
    "Accesorio de aceptación sintético. Publicación de perfil privado de control de calidad.": "Escritorio con herramientas y materiales organizados.",
    "Elemento de aceptación sintético. Publicación de perfil privado de control de calidad.": "Escritorio con herramientas y materiales organizados.",
    "Elemento de aceptación sintético. Publicación privada de perfil de control de calidad.": "Escritorio con herramientas y materiales organizados.",
    "Modelo de aceptación sintético. Publicación privada de perfil de QA.": "Escritorio con herramientas y materiales organizados.",
    "Escritorio del espacio de trabajo de aceptación": "Escritorio del espacio de trabajo",
    "Escritorio de espacio de trabajo de aceptación": "Escritorio del espacio de trabajo",
    "RealityOS Demo Admin": "RealityOS Admin",
    "Postman Demo (public test account)": "Postman",
    "Postman Demo - public test workspace": "Postman",
    "Public Postman demo. Empty test workspace; no private data or media.": "Espacio de trabajo de Postman.",
    "QA Hackathon — disposable tests": "Equipo de revisión",
    "QA Admin — Synthetic Alex": "Alex · Administración",
    "QA Member — Synthetic Maya": "Maya · Colaboración",
    "QA Reader — Synthetic Daniel": "Daniel · Consulta",
    "QA Outsider — Synthetic Sarah": "Sarah",
    "Demo police": "Archivo policial",
    "Demo nursing": "Archivo de enfermería",
    "Demo memory": "Archivo de seguimiento",
    "Demo qa": "Archivo del equipo",
    "QA conexión concurrente descartable": "Archivo de revisión",
    "QA revisión R2 2026-11-03": "Archivo R2",
    "Directorio social y taller (QA)": "Directorio social",
    "Jury source — real REST ingestion": "Registros del equipo",
}
MARKER = re.compile(
    r"\[(?:demo|simulated(?: qa)?|(?:qa |control de calidad )?simulado|demostración)\]\s*",
    re.IGNORECASE,
)
MODELS = {
    m.__tablename__: m
    for m in (
        User,
        Workspace,
        Publication,
        PublicationTranslation,
        StorageConnection,
        Connection,
        Record,
        RecordNote,
    )
}


def clean(value):
    if isinstance(value, dict):
        return {
            k: clean(v)
            for k, v in value.items()
            if not (k == "warning" and v == "NO ES UNA PRESCRIPCIÓN REAL")
        }
    if isinstance(value, list):
        return [clean(v) for v in value]
    if not isinstance(value, str):
        return value
    value = MARKER.sub("", value)
    for old, new in REPLACEMENTS.items():
        value = value.replace(old, new)
    return value


def change(row, fields, changes):
    before = {
        key: getattr(row, key)
        for key, value in fields.items()
        if getattr(row, key) != value
    }
    if before:
        changes.append(
            {
                "table": row.__tablename__,
                "key": {
                    c.key: str(getattr(row, c.key))
                    for c in inspect(type(row)).primary_key
                },
                "before": before,
                "after": {key: fields[key] for key in before},
            }
        )


def plan(db):
    changes = []
    groups = list(db.scalars(select(Workspace).where(Workspace.name.in_(GROUPS))))
    for row in groups:
        if (
            row.description
            == "Synthetic test dataset imported through the real RealityOS API."
        ):
            change(row, {"description": GROUPS[row.name]}, changes)
    for model, fields in (
        (Workspace, ("name", "description")),
        (User, ("display_name",)),
        (StorageConnection, ("name",)),
    ):
        for row in db.scalars(select(model)):
            # Exact fixture values only; free-form user copy is not rewritten.
            change(
                row,
                {f: REPLACEMENTS.get(getattr(row, f), getattr(row, f)) for f in fields},
                changes,
            )
    group_ids = [row.id for row in groups]
    record_ids = []
    for row in db.scalars(
        select(Record).where(
            Record.workspace_id.in_(group_ids), Record.simulated.is_(True)
        )
    ):
        record_ids.append(row.id)
        change(row, {"title": clean(row.title), "data": clean(row.data)}, changes)
    for row in db.scalars(
        select(RecordNote).where(RecordNote.record_id.in_(record_ids))
    ):
        if MARKER.match(row.text):
            change(row, {"text": clean(row.text)}, changes)
    for row in db.scalars(
        select(Connection).where(Connection.workspace_id.in_(group_ids))
    ):
        change(row, {"name": REPLACEMENTS.get(row.name, row.name)}, changes)
    qa_owners = set(
        db.scalars(
            select(PasswordAccount.user_id).where(
                PasswordAccount.username.in_(
                    [
                        "qa-hackathon-admin",
                        "qa-hackathon-member",
                        "qa-hackathon-reader",
                        "qa-hackathon-outsider",
                    ]
                )
            )
        )
    )
    for row in db.scalars(select(Publication)):
        if (
            not (
                row.workspace_id in group_ids
                and row.source
                in {"simulator-licensed", "simulator-work", "workspace-import"}
            )
            and row.owner_id not in qa_owners
        ):
            continue
        fields = {
            key: clean(getattr(row, key))
            for key in ("caption", "note_text", "search_text", "ai_caption")
        }
        change(row, fields, changes)
        hashes = {
            text_hash(getattr(row, key)): text_hash(fields[key])
            for key in ("caption", "note_text")
            if getattr(row, key) and getattr(row, key) != fields[key]
        }
        for translation in db.scalars(
            select(PublicationTranslation).where(
                PublicationTranslation.post_id == row.id
            )
        ):
            translated = {"translated_text": clean(translation.translated_text)}
            digest = hashes.get(translation.text_hash)
            if (
                digest
                and db.get(
                    PublicationTranslation, (row.id, translation.language, digest)
                )
                is None
            ):
                translated["text_hash"] = digest
            change(translation, translated, changes)
    return changes


def apply_changes(db, changes, rollback=False):
    targets = []
    for item in changes:
        model = MODELS[item["table"]]
        key = dict(item["key"])
        if rollback:
            key.update({k: item["after"][k] for k in key if k in item["after"]})
        identity = tuple(
            uuid.UUID(key[c.key]) if c.type.python_type is uuid.UUID else key[c.key]
            for c in inspect(model).primary_key
        )
        row = db.get(model, identity, with_for_update=True)
        expected = item["after" if rollback else "before"]
        if row is None or any(getattr(row, k) != v for k, v in expected.items()):
            raise ValueError(f"Concurrent change in {item['table']}; nothing committed")
        targets.append((row, item["before" if rollback else "after"]))
    for row, fields in targets:
        for key, value in fields.items():
            setattr(row, key, value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    parser.add_argument("--journal", type=Path)
    args = parser.parse_args()
    if (args.apply or args.rollback) and not args.journal:
        parser.error("A private --journal is required")
    with Database(get_settings().database_url).session_factory() as db:
        changes = json.loads(args.journal.read_text()) if args.rollback else plan(db)
        if args.apply or args.rollback:
            apply_changes(db, changes, args.rollback)
            if not args.rollback:
                args.journal.parent.mkdir(parents=True, exist_ok=True)
                with args.journal.open("x") as stream:
                    args.journal.chmod(0o600)
                    json.dump(changes, stream, ensure_ascii=False, indent=2)
                    stream.write("\n")
            db.commit()
        print(
            json.dumps(
                {
                    "applied": args.apply or args.rollback,
                    "rows": dict(Counter(c["table"] for c in changes)),
                }
            )
        )


if __name__ == "__main__":
    main()
