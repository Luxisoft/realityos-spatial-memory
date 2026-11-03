"""Explicit comparison of imported medication fields; never a treatment decision."""

import uuid
from datetime import UTC, datetime

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, workspace_member
from app.models import User
from app.workspaces.models import Record
from app.workspaces.routes import router, scoped_record
from app.workspaces.schemas import MedicationCheck


def source_date(value):
    if not isinstance(value, str):
        raise ValueError("Date must be an ISO timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Date needs a timezone")
    return parsed


@router.post("/workspaces/{workspace_id}/records/{person_id}/medication-check")
async def medication_check(
    workspace_id: uuid.UUID,
    person_id: uuid.UUID,
    payload: MedicationCheck,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db)
    person = scoped_record(db, workspace_id, person_id)
    if person.kind != "person":
        raise HTTPException(422, "Select a person record.")
    try:
        prescription = scoped_record(db, workspace_id, uuid.UUID(payload.prescription_id))
    except ValueError:
        raise HTTPException(422, "Invalid prescription identifier.")
    if (
        prescription.kind != "prescription"
        or prescription.connection_id != person.connection_id
        or person.external_id not in prescription.related_ids
    ):
        raise HTTPException(422, "Prescription does not belong to this person.")
    issues, missing = [], []
    if not payload.patient_confirmed:
        missing.append("patient_confirmation")
    for observed, field in (
        (payload.observed_ingredient, "ingredient"),
        (payload.observed_concentration, "concentration"),
    ):
        expected = prescription.data.get(field)
        if not isinstance(expected, str) or not expected.strip():
            missing.append(field)
        elif expected.strip().casefold() != observed.strip().casefold():
            issues.append(field + "_mismatch")
    now = payload.checked_at
    if now.tzinfo is None:
        raise HTTPException(422, "checked_at requires a timezone.")
    for key, is_start in (("valid_from", True), ("valid_until", False)):
        try:
            value = source_date(prescription.data[key])
            if (is_start and now < value) or (not is_start and now > value):
                issues.append("prescription_outside_validity")
        except (KeyError, ValueError, TypeError):
            missing.append(key)
    if prescription.data.get("state") != "active":
        issues.append("prescription_not_active")
    try:
        if source_date(person.data.get("allergies_reviewed_at")) > now:
            raise ValueError("Review occurs after this comparison")
    except ValueError:
        missing.append("allergy_review")
    related = list(
        db.scalars(
            select(Record).where(
                Record.connection_id == person.connection_id,
                Record.status == "active",
                Record.kind.in_(["allergy", "administration"]),
            )
        )
    )
    sources = [str(person.id), str(prescription.id)]
    for row in related:
        if person.external_id not in row.related_ids:
            continue
        sources.append(str(row.id))
        if (
            row.kind == "allergy"
            and str(row.data.get("substance", "")).strip().casefold()
            == payload.observed_ingredient.strip().casefold()
        ):
            issues.append("recorded_allergy")
        if row.kind == "administration" and prescription.external_id in row.related_ids:
            issues.append("administration_history_requires_review")
    return {
        "status": "discrepancy" if issues else "insufficient_data" if missing else "fields_match",
        "issues": sorted(set(issues)),
        "missing": missing,
        "source_record_ids": sources,
        "requires_professional_review": True,
        "administration_recorded": False,
        "checked_at": now.astimezone(UTC).isoformat(),
    }
