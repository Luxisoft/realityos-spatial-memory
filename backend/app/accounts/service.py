"""Account challenges and SMTP transport. No credentials or tokens are logged."""

import asyncio
import hashlib
import secrets
import smtplib
import ssl
import time
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

from fastapi import HTTPException
from sqlalchemy import update

from app.accounts.models import AccountAttempt, AccountChallenge
from app.accounts.presentation import language, mail_content


def utc(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def throttle(db, request, identity, action):
    # Independent client and identity buckets prevent trivial username rotation.
    for value, limit in (
        (request.client.host if request.client else "unknown", 30),
        (identity.casefold(), 8),
    ):
        key = hashlib.sha256(f"{action}:{value}".encode()).hexdigest()
        window = int(time.time()) // 900
        from sqlalchemy import case

        if db.get_bind().dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import insert
        else:
            from sqlalchemy.dialects.sqlite import insert
        statement = insert(AccountAttempt).values(key=key, window=window, count=1)
        statement = statement.on_conflict_do_update(
            index_elements=[AccountAttempt.key],
            set_={
                "window": window,
                "count": case((AccountAttempt.window == window, AccountAttempt.count + 1), else_=1),
            },
        ).returning(AccountAttempt.count)
        count = db.scalar(statement)
        blocked = count > limit
        db.commit()  # Failed requests must also count.
        if blocked:
            raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")


def send_mail(settings, recipient, purpose, lang, token):
    if not settings.smtp_host or not settings.smtp_from:
        raise HTTPException(503, "Email delivery is not configured.")
    path = "verify" if purpose == "verify" else "reset"
    url = f"{str(settings.auth_public_url).rstrip('/')}/v1/auth/{path}?lang={lang}#token={token}"
    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = recipient
    subject, text, html = mail_content(purpose, url, lang)
    message["Subject"] = subject
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    try:
        context = ssl.create_default_context()
        if settings.smtp_port == 465:
            client = smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=15, context=context
            )
        else:
            client = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
            client.ehlo()
            client.starttls(context=context)
            client.ehlo()
        with client:
            if settings.smtp_username:
                client.login(settings.smtp_username, settings.smtp_password.get_secret_value())
            client.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise HTTPException(503, "Email delivery failed. Please retry.") from exc


async def challenge(db, settings, user, purpose, accept_language=None):
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    db.execute(
        update(AccountChallenge)
        .where(
            AccountChallenge.user_id == user.id,
            AccountChallenge.purpose == purpose,
            AccountChallenge.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    row = AccountChallenge(
        digest=hashlib.sha256(token.encode()).hexdigest(),
        user_id=user.id,
        purpose=purpose,
        expires_at=now + timedelta(minutes=30),
    )
    db.add(row)
    db.flush()
    await asyncio.to_thread(
        send_mail,
        settings,
        user.email,
        purpose,
        language(accept_language, user.preferred_language),
        token,
    )


def consume(db, token, purpose):
    row = db.get(AccountChallenge, hashlib.sha256(token.encode()).hexdigest(), with_for_update=True)
    if (
        row is None
        or row.purpose != purpose
        or row.consumed_at
        or utc(row.expires_at) <= datetime.now(UTC)
    ):
        raise HTTPException(400, "Invalid or expired link.")
    row.consumed_at = datetime.now(UTC)
    return row.user_id
