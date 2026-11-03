"""Pull the documented ingestion contract from explicitly allowlisted HTTPS sources."""

import base64
import hashlib
import ipaddress
import socket
import uuid
from urllib.parse import urlsplit

import httpx
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, workspace_member
from app.models import Role, User
from app.workspaces.models import Connection
from app.workspaces.routes import router
from app.workspaces.schemas import ImportBatch
from app.workspaces.service import import_batch


def cipher(settings):
    key = settings.integration_encryption_key.get_secret_value()
    if not key:
        raise HTTPException(503, "Integration secret encryption is not configured.")
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest()))


def encrypt_secret(value, settings):
    return cipher(settings).encrypt(value.encode()).decode()


def validate_source(url, settings):
    parsed = urlsplit(url)
    allowed = {
        h.strip().casefold() for h in settings.integration_source_hosts.split(",") if h.strip()
    }
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.hostname.casefold() not in allowed
        or parsed.username
        or parsed.password
        or parsed.fragment
        or parsed.port not in {None, 443}
    ):
        raise HTTPException(422, "Source must be HTTPS on a server-approved host, port 443.")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise HTTPException(422, "Source hostname cannot be resolved.") from exc
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise HTTPException(422, "Source must resolve to public addresses.")


@router.post("/workspaces/{workspace_id}/connections/{connection_id}/sync")
async def sync(
    workspace_id: uuid.UUID,
    connection_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db, {Role.ADMIN})
    row = db.get(Connection, connection_id)
    if row is None or row.workspace_id != workspace_id or not row.active:
        raise HTTPException(404)
    if not row.source_url:
        raise HTTPException(409, "This connection accepts uploads; no pull source configured.")
    settings = request.app.state.settings
    validate_source(row.source_url, settings)
    headers = {}
    if row.secret_encrypted:
        headers["Authorization"] = (
            "Bearer " + cipher(settings).decrypt(row.secret_encrypted.encode()).decode()
        )
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=False, trust_env=False) as client:
            async with client.stream("GET", row.source_url, headers=headers) as response:
                if response.status_code != 200:
                    raise HTTPException(502, "External source rejected the request.")
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > 2 * 1024 * 1024:
                        raise HTTPException(413, "External batch exceeds 2 MiB.")
        payload = ImportBatch.model_validate_json(bytes(data))
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            502, "Source unavailable or does not implement the import contract."
        ) from exc
    db.refresh(row, with_for_update=True)
    return import_batch(db, row, payload)
