from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.dependencies import bearer_scheme, get_current_device, get_current_user, get_db
from app.http.common import _active_assignment
from app.providers.tts import SpeechUnavailable, synthesize
from app.tts_contracts import SpeechRequest

router = APIRouter()


@router.post(
    "/tts",
    response_class=Response,
    responses={200: {"content": {"audio/wav": {"schema": {"type": "string", "format": "binary"}}}}},
    tags=["speech"],
)
async def speech_audio(
    payload: SpeechRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    """Speak caller-supplied response text; never look up evidence or capture media."""
    if request.headers.get("Authorization"):
        await get_current_user(request, credentials, db)
    else:
        device = await get_current_device(request, db)
        if _active_assignment(db, device) is None:
            raise HTTPException(403, "Device has no active workspace assignment.")
    try:
        raw = await synthesize(
            payload,
            request.app.state.settings,
            transport=getattr(request.app.state, "tts_transport", None),
        )
    except SpeechUnavailable as error:
        raise HTTPException(503, str(error)) from error
    return Response(raw, media_type="audio/wav", headers={"Cache-Control": "no-store"})
