from __future__ import annotations

import hashlib
import io
import uuid
import zipfile
from datetime import UTC, datetime
from xml.etree import ElementTree

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import (
    or_,
    select,
)
from sqlalchemy.orm import Session

from app.accounts.models import PasswordAccount
from app.dependencies import get_current_user, get_db
from app.models import (
    MediaAsset,
    User,
    WorkspaceMember,
)
from app.social_features.models import (
    FacebookFriend,
    FacebookIdentity,
    FacebookProfile,
    Publication,
    UserProfile,
)
from app.social_features.publication_visibility import publication_content
from app.social_features.schemas import ProfileSearchRequest, ProfileUpdate

"""Facebook identities and explicitly shared audiovisual publications."""


router = APIRouter()


def _user_profile(db: Session, user_id: uuid.UUID) -> UserProfile:

    profile = db.get(UserProfile, user_id)
    if profile is None:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    return profile


def _safe_web_url(value: str) -> str:
    normalized = value.strip()
    if normalized and not normalized.casefold().startswith(("https://", "http://")):
        raise HTTPException(422, "Profile links must use HTTP or HTTPS.")
    return normalized


def _public_profile_payload(target: User, db: Session) -> dict:

    facebook_account = bool(
        db.scalar(select(FacebookIdentity.subject).where(FacebookIdentity.user_id == target.id))
    )
    facebook = db.get(FacebookProfile, target.id)
    custom = db.get(UserProfile, target.id)
    friends = list(
        db.scalars(
            select(FacebookFriend)
            .where(FacebookFriend.owner_user_id == target.id)
            .order_by(FacebookFriend.name)
            .limit(100)
        )
    )
    local_avatar = custom.avatar_media_id if custom else None
    birthday = custom.birthday if custom and not facebook else None
    today = datetime.now(UTC).date()
    age = (
        today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        if birthday
        else None
    )
    return {
        "user_id": str(target.id),
        "profile_source": (
            "facebook"
            if facebook_account
            else "email"
            if db.get(PasswordAccount, target.id)
            else "other"
        ),
        "display_name": target.display_name,
        "is_guest": target.is_guest,
        "email": facebook.email if facebook else target.email,
        "birthday": facebook.birthday if facebook else birthday.isoformat() if birthday else None,
        "age_min": facebook.age_min if facebook else age,
        "age_max": facebook.age_max if facebook else age,
        "gender": facebook.gender if facebook else custom.gender if custom else None,
        "hometown": facebook.hometown if facebook else custom.hometown if custom else None,
        "location": facebook.location if facebook else custom.location if custom else None,
        "facebook_link": facebook.profile_link if facebook else None,
        "picture_url": (
            f"/v1/profiles/{target.id}/avatar"
            if local_avatar
            else facebook.picture_url
            if facebook
            else None
        ),
        "headline": custom.headline if custom else "",
        "biography": custom.biography if custom else "",
        "phone": custom.phone if custom else "",
        "website": custom.website if custom else "",
        "social_links": custom.social_links if custom else [],
        "counts": {
            "friends": facebook.friends_count if facebook else None,
            "likes": facebook.likes_count if facebook else None,
            "photos": facebook.photos_count if facebook else None,
            "videos": facebook.videos_count if facebook else None,
        },
        "friends": [
            {
                "facebook_id": item.facebook_id,
                "name": item.name,
                "picture_url": item.picture_url,
                "profile_link": item.profile_link,
            }
            for item in friends
        ],
    }


def _own_profile_payload(user: User, db: Session) -> dict:
    payload = _public_profile_payload(user, db)
    custom = _user_profile(db, user.id)
    facebook_account = payload["profile_source"] == "facebook"
    password_account = db.get(PasswordAccount, user.id)
    payload["personal_details_editable"] = bool(
        password_account and not facebook_account and not user.is_guest
    )
    payload["cv"] = {
        "present": custom.cv_bytes is not None,
        "filename": custom.cv_filename,
        "mime_type": custom.cv_mime_type,
        "sha256": custom.cv_sha256,
        "status": custom.cv_status,
        "error": custom.cv_error,
        "simulated": custom.cv_simulated,
        "analysis": custom.cv_context,
        "updated_at": custom.cv_updated_at.isoformat() if custom.cv_updated_at else None,
    }
    return payload


@router.get("/me/profile")
def own_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _own_profile_payload(user, db)


@router.patch("/me/profile")
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    personal_fields = {"display_name", "birthday", "gender", "hometown", "location"}
    supplied = payload.model_fields_set
    if supplied & personal_fields:
        facebook_account = db.scalar(
            select(FacebookIdentity.subject).where(FacebookIdentity.user_id == user.id)
        )
        if facebook_account or user.is_guest or not db.get(PasswordAccount, user.id):
            raise HTTPException(
                403, "Personal details are editable only for email accounts without Facebook."
            )
    profile = _user_profile(db, user.id)
    if "display_name" in supplied:
        user.display_name = payload.display_name
    if "birthday" in supplied:
        profile.birthday = payload.birthday
    for field in ("gender", "hometown", "location"):
        if field in supplied:
            setattr(profile, field, (getattr(payload, field) or "").strip() or None)
    for field in ("headline", "biography", "phone"):
        if field in supplied:
            setattr(profile, field, getattr(payload, field).strip())
    if "website" in supplied:
        profile.website = _safe_web_url(payload.website)
    if "social_links" in supplied:
        profile.social_links = [
            {"label": item.label.strip(), "url": _safe_web_url(item.url)}
            for item in payload.social_links
        ]
    db.flush()
    return _own_profile_payload(user, db)


def _guest_may_view_profile(viewer: User, target: User) -> bool:
    """Guests see only themselves and fellow guests."""
    return not viewer.is_guest or target.id == viewer.id or target.is_guest


@router.get("/profiles/{user_id}")
def public_profile(
    user_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if target is None or not target.is_active:
        raise HTTPException(404, "Profile unavailable.")
    if not _guest_may_view_profile(user, target):
        raise HTTPException(404, "Profile unavailable.")
    return _public_profile_payload(target, db)


@router.get("/profiles/{user_id}/avatar")
def profile_avatar(
    user_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from fastapi.responses import Response

    target = db.get(User, user_id)
    if target is None or not _guest_may_view_profile(user, target):
        raise HTTPException(404, "Profile picture unavailable.")
    profile = db.get(UserProfile, user_id)
    asset = (
        db.get(MediaAsset, profile.avatar_media_id) if profile and profile.avatar_media_id else None
    )
    if asset is None:
        from app.models import CaptureSession

        asset = db.scalar(
            select(MediaAsset)
            .join(CaptureSession, MediaAsset.capture_session_id == CaptureSession.id)
            .where(
                CaptureSession.created_by_id == user_id,
                MediaAsset.extra_metadata["face_profile"].as_boolean().is_(True),
            )
            .order_by(MediaAsset.created_at.desc())
            .limit(1)
        )
    if asset is None or not asset.mime_type.startswith("image/"):
        raise HTTPException(404, "Profile picture unavailable.")
    from PIL import Image, ImageOps

    with Image.open(io.BytesIO(asset.original_bytes)) as original:
        portrait = ImageOps.exif_transpose(original).convert("RGB")
        portrait.thumbnail((512, 512))
        buffer = io.BytesIO()
        portrait.save(buffer, "JPEG", quality=90)
    return Response(
        buffer.getvalue(),
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=3600"},
    )


def _extract_cv_text(raw: bytes, mime_type: str) -> str:
    if mime_type == "application/pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        if len(reader.pages) > 100:
            raise ValueError("The CV has too many pages.")
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > 5 * 1024 * 1024:
                raise ValueError("The CV document is too complex.")
            root = ElementTree.fromstring(archive.read(info))
        text = " ".join(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
    else:
        raise ValueError("Only PDF and DOCX files are accepted.")
    normalized = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(normalized) < 20:
        raise ValueError("The CV does not contain readable text.")
    return normalized[:100_000]


def _process_current_cv(profile: UserProfile, request: Request) -> None:

    from app.meta import MetaProviderError, build_meta_client

    if profile.cv_bytes is None or profile.cv_mime_type is None:
        raise HTTPException(409, "There is no CV to process.")
    profile.cv_status = "processing"
    profile.cv_error = None
    profile.cv_text = None
    profile.cv_context = None
    profile.cv_simulated = False
    try:
        extracted = _extract_cv_text(profile.cv_bytes, profile.cv_mime_type)
        context = build_meta_client(request.app.state.settings).extract_profile_context(extracted)
        profile.cv_text = extracted
        profile.cv_context = context.text
        profile.cv_simulated = context.simulated
        profile.cv_status = "ready"
    except (MetaProviderError, OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        profile.cv_status = "failed"
        profile.cv_error = str(exc)[:500]


@router.post("/me/profile/cv")
async def upload_cv(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    if file.content_type not in allowed:
        raise HTTPException(415, "Only PDF and DOCX files are accepted.")
    raw = await file.read()
    if not raw or len(raw) > 10 * 1024 * 1024:
        raise HTTPException(413, "The CV must be between 1 byte and 10 MB.")
    profile = _user_profile(db, user.id)
    # A new upload is the only current CV. Old derived data is cleared before
    # processing so questions can never use stale professional information.
    profile.cv_bytes = raw
    profile.cv_filename = (file.filename or "cv")[:255]
    profile.cv_mime_type = file.content_type
    profile.cv_sha256 = hashlib.sha256(raw).hexdigest()
    profile.cv_text = None
    profile.cv_context = None
    profile.cv_status = "pending"
    profile.cv_error = None
    profile.cv_simulated = False
    profile.cv_updated_at = datetime.now(UTC)
    _process_current_cv(profile, request)
    db.flush()
    return _own_profile_payload(user, db)


def _note_audio_to_wav(raw: bytes, mime_type: str) -> bytes:
    import subprocess

    if mime_type in {"audio/wav", "audio/x-wav"}:
        return raw
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                "pipe:0",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-f",
                "wav",
                "pipe:1",
            ],
            input=raw,
            capture_output=True,
            check=True,
            timeout=30,
        )
    except FileNotFoundError as error:
        raise HTTPException(503, "Audio conversion is unavailable.") from error
    except (subprocess.SubprocessError, OSError) as error:
        raise HTTPException(422, "The audio cannot be decoded.") from error
    return result.stdout


@router.post("/notes/transcribe")
async def transcribe_note(
    request: Request,
    audio: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Transcribe a mobile voice note to text. Audio bytes are never stored."""

    from app.meta import MetaProviderError, build_meta_client

    allowed = {
        "audio/wav",
        "audio/x-wav",
        "audio/mp4",
        "audio/x-m4a",
        "audio/3gpp",
        "audio/3gpp2",
        "audio/webm",
        "audio/mpeg",
    }
    if audio.content_type not in allowed:
        raise HTTPException(415, "Only WAV, M4A, MP4, 3GP, WebM or MP3 audio is accepted.")
    raw = await audio.read()
    if not raw or len(raw) > 10 * 1024 * 1024:
        raise HTTPException(413, "The audio exceeds the permitted size.")
    wav = _note_audio_to_wav(raw, audio.content_type or "")
    try:
        transcription = build_meta_client(request.app.state.settings).transcribe_wav(wav)
    except MetaProviderError as exc:
        if "no transcript" in str(exc):
            raise HTTPException(422, "No recognizable speech in the recording.") from exc
        raise HTTPException(503, str(exc)) from exc
    return {"text": transcription.text, "simulated": transcription.simulated}


def _checked_note(note_text: str, note_source: str) -> tuple[str, str]:
    if note_source not in ("", "voice", "text"):
        raise HTTPException(422, "note_source must be voice or text.")
    note = note_text.strip()
    return note, note_source if note else ""


@router.post("/me/profile/cv/retry")
def retry_cv(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _user_profile(db, user.id)
    _process_current_cv(profile, request)
    profile.cv_updated_at = datetime.now(UTC)
    db.flush()
    return _own_profile_payload(user, db)


@router.delete("/me/profile/cv")
def delete_cv(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = _user_profile(db, user.id)
    profile.cv_bytes = None
    profile.cv_filename = None
    profile.cv_mime_type = None
    profile.cv_sha256 = None
    profile.cv_text = None
    profile.cv_context = None
    profile.cv_status = "empty"
    profile.cv_error = None
    profile.cv_simulated = False
    profile.cv_updated_at = datetime.now(UTC)
    db.flush()
    return _own_profile_payload(user, db)


def _profile_search_text(
    target: User, viewer: User, db: Session
) -> tuple[str, str, list[Publication]]:

    public = _public_profile_payload(target, db)
    custom = db.get(UserProfile, target.id)
    public_text = " ".join(
        str(value)
        for value in (
            public["display_name"],
            public["headline"],
            public["biography"],
            public["hometown"],
            public["location"],
        )
        if value
    )
    from app.social_features.publication_visibility import authorized_publications

    visible_media = list(
        db.scalars(
            select(Publication)
            .where(
                Publication.owner_id == target.id,
                Publication.hidden.is_(False),
                publication_content(),
                authorized_publications(viewer.id),
            )
            .order_by(Publication.published_at.desc())
            .limit(60)
        )
    )
    media_text = " ".join(
        f"{publication.caption} {publication.search_text}" for publication in visible_media
    )
    context = custom.cv_context if custom and custom.cv_status == "ready" else ""
    return f"{public_text} {media_text}".strip(), context or "", visible_media


@router.post("/profiles/search")
def search_profiles(
    payload: ProfileSearchRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.meta import MetaProviderError, build_meta_client
    from app.social_features.gallery import _publication_payload

    if not user.is_guest:
        if payload.user_id is None:
            payload = payload.model_copy(update={"user_id": user.id})
        elif payload.user_id != user.id:
            raise HTTPException(
                410, "Use the workspace records search with an authorized workspace."
            )
    if user.is_guest:
        teammate_ids = select(WorkspaceMember.user_id).where(
            WorkspaceMember.workspace_id.in_(
                select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user.id)
            )
        )
        if payload.user_id is not None:
            selected = db.get(User, payload.user_id)
            shares_team = (
                selected is not None
                and db.scalar(
                    select(WorkspaceMember.workspace_id)
                    .where(
                        WorkspaceMember.user_id == selected.id,
                        WorkspaceMember.workspace_id.in_(
                            select(WorkspaceMember.workspace_id).where(
                                WorkspaceMember.user_id == user.id
                            )
                        ),
                    )
                    .limit(1)
                )
                is not None
            )
            targets = (
                [selected]
                if selected is not None
                and selected.is_active
                and (selected.id == user.id or (selected.is_guest and shares_team))
                else []
            )
        else:
            targets = list(
                db.scalars(
                    select(User).where(
                        User.is_active.is_(True),
                        User.is_guest.is_(True),
                        or_(User.id == user.id, User.id.in_(teammate_ids)),
                    )
                )
            )
    elif payload.user_id is not None:
        selected = db.get(User, payload.user_id)
        targets = [selected] if selected is not None and selected.is_active else []
    else:
        targets = list(db.scalars(select(User).where(User.is_active.is_(True))))
    if not targets:
        raise HTTPException(404, "Profile unavailable.")
    terms = {
        word.casefold().strip(".,:?¿¡!()")
        for word in payload.question.split()
        if len(word.strip(".,:?¿¡!()")) > 3
    }
    ranked: list[tuple[int, User, str, str, list[Publication]]] = []
    for target in targets:
        public_text, context, media = _profile_search_text(target, user, db)
        haystack = f"{public_text} {context}".casefold()
        score = sum(term in haystack for term in terms)
        ranked.append((score, target, public_text, context, media))
    ranked.sort(key=lambda item: (item[0], item[1].display_name.casefold()), reverse=True)
    if payload.user_id is None and any(item[0] > 0 for item in ranked):
        ranked = [item for item in ranked if item[0] > 0]
    candidates = [
        {
            "user_id": str(target.id),
            "name": target.display_name,
            "public_profile": public_text,
            "context": context,
        }
        for _, target, public_text, context, _ in ranked[:8]
    ]
    try:
        model = build_meta_client(request.app.state.settings)
        from app.social_features.language_preferences import language_diagnostic

        language = language_diagnostic(request, user, payload.language)
        answer = model.answer_profile_question(payload.question, candidates, language=language)
    except MetaProviderError as exc:
        raise HTTPException(503, str(exc)) from exc
    matched = set(answer.matched_user_ids)
    profiles = [
        _public_profile_payload(target, db)
        for _, target, _, _, _ in ranked[:8]
        if not matched or str(target.id) in matched
    ]
    from app.gallery_index import expand_terms

    known_media_tags: list[str] = []
    for _, target, _, _, media in ranked[:8]:
        if matched and str(target.id) not in matched:
            continue
        for publication in media:
            for label in publication.ai_labels or []:
                if label not in known_media_tags:
                    known_media_tags.append(label)
    expanded = expand_terms(payload.question, known_media_tags[:1000], model)
    wanted = [term.casefold() for term in expanded if term] or [term for term in terms if term]
    media_matches = []
    for _, target, _, _, media in ranked[:8]:
        if matched and str(target.id) not in matched:
            continue
        for publication in media:
            haystack = f"{publication.caption} {publication.search_text}".casefold()
            if wanted and not any(term in haystack for term in wanted):
                continue
            media_matches.append(_publication_payload(publication, user, db))
            if len(media_matches) >= 12:
                break
        if len(media_matches) >= 12:
            break
    return {
        "answer": answer.text,
        "response_language": language,
        "profiles": profiles,
        "media_matches": media_matches,
        "simulated": answer.simulated,
    }
