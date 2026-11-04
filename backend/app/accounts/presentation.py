"""Android-aligned account mail and browser actions; no external assets."""

import json
import secrets
from html import escape

from fastapi.responses import HTMLResponse

from app.languages import request_language

COPY = {
    "es": {
        "verify": "Confirmar correo",
        "reset": "Restablecer contraseña",
        "intro": "Continúa con tu cuenta de RealityOS.",
        "expiry": "El enlace vence en 30 minutos y solo se puede usar una vez.",
        "ignore": "Si no solicitaste esta operación, ignora este correo.",
        "alternative": "Si el botón no funciona, abre este enlace:",
        "password": "Nueva contraseña",
        "confirm": "Confirmar contraseña",
        "hint": "Al menos 12 caracteres",
        "busy": "Procesando…",
        "success": "Listo. Vuelve a la aplicación Android para iniciar sesión.",
        "invalid": "Enlace inválido o vencido. Solicita uno nuevo desde la aplicación.",
        "offline": "No se pudo conectar. Intenta de nuevo.",
        "mismatch": "Las contraseñas no coinciden.",
        "rejected": "No se pudo completar la solicitud. Revisa los datos e inténtalo de nuevo.",
        "limited": "Demasiados intentos. Espera unos minutos e inténtalo de nuevo.",
    },
    "en": {
        "verify": "Confirm email",
        "reset": "Reset password",
        "intro": "Continue with your RealityOS account.",
        "expiry": "This link expires in 30 minutes and can only be used once.",
        "ignore": "If you did not request this, ignore this email.",
        "alternative": "If the button does not work, open this link:",
        "password": "New password",
        "confirm": "Confirm password",
        "hint": "At least 12 characters",
        "busy": "Processing…",
        "success": "Done. Return to the Android app to sign in.",
        "invalid": "Invalid or expired link. Request a new one from the app.",
        "offline": "Could not connect. Try again.",
        "mismatch": "Passwords do not match.",
        "rejected": "The request could not be completed. Check the details and try again.",
        "limited": "Too many attempts. Wait a few minutes and try again.",
    },
}


def language(header: str | None, fallback: str | None = None) -> str:
    return request_language(header, fallback if fallback in COPY else "es")


BODY_STYLE = "margin:0;background:#262729;color:#F4F7F5;font-family:Arial,sans-serif;font-size:16px;line-height:1.5"
CARD_STYLE = (
    "max-width:560px;margin:32px auto;padding:24px;border:1px solid #363D45;border-radius:12px"
)
BUTTON_STYLE = "display:inline-block;background:#62A9F8;color:#17211f;padding:16px 24px;border-radius:12px;font-weight:bold;text-decoration:none"


def mail_content(purpose: str, url: str, lang: str) -> tuple[str, str, str]:
    copy = COPY[lang]
    title = copy[purpose]
    text = f"{title}\n\n{copy['intro']}\n\n{url}\n\n{copy['expiry']}\n{copy['ignore']}"
    link = escape(url, quote=True)
    html = f'''<!doctype html><html lang="{lang}"><body style="{BODY_STYLE}">
<div style="{CARD_STYLE}"><p style="font-weight:bold">RealityOS</p>
<h1 style="font-size:27px;line-height:33px">{title}</h1><p>{copy["intro"]}</p>
<p><a href="{link}" style="{BUTTON_STYLE}">{title}</a></p>
<p>{copy["expiry"]}</p><p>{copy["alternative"]}</p>
<a href="{link}" style="color:#62A9F8;word-break:break-all">{link}</a>
<p style="color:#AAB4AF">{copy["ignore"]}</p></div></body></html>'''
    return "RealityOS — " + title, text, html


def action_page(action: str, lang: str) -> HTMLResponse:
    copy = COPY[lang]
    reset = action == "reset"
    endpoint = "reset-password" if reset else "confirm-email"
    nonce = secrets.token_urlsafe(20)
    fields = (
        "".join(
            f'<label for="{key}">{copy[label]}</label><input id="{key}" type="password" minlength="12" maxlength="512" autocomplete="new-password" required>'
            for key, label in (("password", "password"), ("confirmation", "confirm"))
        )
        if reset
        else ""
    )
    if reset:
        fields += f"<p>{copy['hint']}</p>"
    return HTMLResponse(
        f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>RealityOS — {copy[action]}</title>
<style nonce="{nonce}">body{{{BODY_STYLE}}}main{{{CARD_STYLE}}}h1{{font-size:27px;line-height:33px}}
*{{box-sizing:border-box}}label,input,button{{display:block;width:100%}}label{{margin:16px 0 8px}}
input{{background:#262729;color:#F4F7F5;border:1px solid #AAB4AF;border-radius:12px;padding:16px;font:inherit}}
button{{{BUTTON_STYLE};border:0;font:inherit;font-weight:bold;cursor:pointer;margin-top:24px}}
:focus-visible{{outline:2px solid #62A9F8;outline-offset:4px}}button:disabled{{opacity:.6;cursor:wait}}
@media(max-width:600px){{main{{margin:16px}}}}</style></head><body><main>
<p><strong>RealityOS</strong></p><h1>{copy[action]}</h1><form>{fields}<button>{copy[action]}</button></form>
<p role="status" aria-live="polite" id="status"></p></main>
<script nonce="{nonce}">
const words={json.dumps(copy, ensure_ascii=True)};
const token=new URLSearchParams(location.hash.slice(1)).get('token');
history.replaceState(null,'',location.pathname+location.search);
const form=document.querySelector('form'), status=document.querySelector('#status'), button=form.querySelector('button');
let busy=false;
if(!token){{form.remove();status.textContent=words.invalid;}}
form.onsubmit=async e=>{{e.preventDefault();if(busy)return;
const password=document.querySelector('#password'), confirmation=document.querySelector('#confirmation');
if(password&&password.value!==confirmation.value){{status.textContent=words.mismatch;confirmation.focus();return;}}
busy=true;button.disabled=true;status.textContent=words.busy;
let body={{token}};if(password)body.password=password.value;
try{{const r=await fetch('/v1/auth/{endpoint}',{{method:'POST',headers:{{'Content-Type':'application/json','Accept-Language':'{lang}'}},body:JSON.stringify(body)}});
status.textContent=r.ok?words.success:r.status>=500?words.offline:r.status===429?words.limited:r.status===400?words.invalid:words.rejected;
if(r.ok)form.remove();}}catch{{status.textContent=words.offline;}}
finally{{busy=false;button.disabled=false;}}}};
</script></body></html>''',
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "Content-Language": lang,
            "Vary": "Accept-Language",
            "Content-Security-Policy": f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
        },
    )
