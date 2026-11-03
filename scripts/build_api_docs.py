"""Generate public API reference and Postman examples from the checked-in contract.

No requests, credentials, database connections or runtime configuration are used.
"""

import argparse
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}
READ_POSTS = {
    "/v1/queries",
    "/v1/queries/image",
    "/v1/queries/audio",
    "/v1/device/queries",
    "/v1/search/classify",
    "/v1/search/route",
    "/v1/faces/search",
    "/v1/profiles/search",
    "/v1/gallery/evidence/information",
}
AUTH_POSTS = {"/v1/auth/login", "/v1/auth/refresh", "/v1/auth/local-login"}
TARGETS = [
    ("public", "server", "Consultas servidor", "https://realityos.luxisoft.com"),
    ("local", "localhost", "Consultas localhost", "http://localhost:8080"),
]
DEFAULT_VARIABLES = {
    "base_url": "https://realityos.luxisoft.com",
    "email": "",
    "username": "",
    "display_name": "",
    "password": "",
    "new_email": "",
    "new_password": "",
    "access_token": "",
    "refresh_token": "",
    "workspace_id": "",
    "language": "en",
    "query": "Where were the documents last seen?",
    "enable_write_requests": "false",
    "device_id": "",
    "device_key": "",
    "integration_key": "",
    "token": "",
}
VARIABLE_DESCRIPTIONS = {
    "base_url": "API origin, without /v1. / URL del API, sin /v1.",
    "email": "Public demo email prefilled. Replace locally to use your own account. / Correo demo incluido. Cámbialo localmente para usar tu cuenta.",
    "username": "Demo username prefilled; use an existing username or email for correction. / Usuario demo incluido; usa tu usuario o correo actual para corregir una cuenta propia.",
    "display_name": "Demo display name prefilled. / Nombre visible demo incluido.",
    "password": "Public demo password prefilled. Replace locally to use your own account. / Contraseña pública demo incluida. Cámbiala localmente para usar tu cuenta.",
    "new_email": "Replacement email for a pending account. / Correo nuevo que reemplaza al pendiente.",
    "new_password": "New password for recovery, at least 12 characters. / Nueva contraseña de recuperación, mínimo 12 caracteres.",
    "access_token": "Saved automatically after login/refresh. / Se guarda automáticamente al iniciar o renovar sesión.",
    "refresh_token": "Saved and rotated automatically after login/refresh. / Se guarda y rota automáticamente al iniciar o renovar sesión.",
    "workspace_id": "Demo workspace preselected. For your own account, copy an ID from GET /v1/workspaces. / Espacio demo preseleccionado. Para tu cuenta, copia un ID de GET /v1/workspaces.",
    "user_id": "Demo user ID prefilled. For your own account, copy id from GET /v1/auth/me. / ID del usuario demo incluido. Para tu cuenta, copia id de GET /v1/auth/me.",
    "language": "Response language: en or es. / Idioma de respuesta: en o es.",
    "query": "Question for evidence/record searches. / Pregunta para consultar evidencia o expedientes.",
    "enable_write_requests": "Set true to enable explicit write operations for this target. / Activa true para habilitar escrituras en este destino.",
    "facebook_access_token": "Your Facebook user token; never a RealityOS session token. / Token de usuario Facebook; no es el token de RealityOS.",
    "device_key": "Key issued when provisioning this target's device. / Clave entregada al provisionar el dispositivo de este destino.",
    "integration_key": "Key issued for this target's integration. / Clave de integración emitida en este destino.",
    "token": "Temporary email action or signed resource token. / Token temporal del correo o recurso firmado.",
}
GROUPS = [
    ("auth", "Access / Acceso"),
    ("workspaces", "Workspaces and records / Espacios y expedientes"),
    ("faces", "Facial recognition / Reconocimiento facial"),
    ("capture", "Capture and processing / Captura y procesamiento"),
    ("query", "Queries and evidence / Consultas y evidencia"),
    ("social", "Profiles and social / Perfiles y social"),
    ("device", "Devices and Display / Dispositivos y Display"),
    ("admin", "Administration / Administración"),
    ("system", "Health / Salud"),
    ("local", "Local installation only / Solo instalación local"),
]


def group(path):
    if "/auth/local-" in path:
        return "local"
    if path.startswith("/health/"):
        return "system"
    if "/admin/" in path or "/moderation" in path:
        return "admin"
    if "/device/" in path or "/display/" in path or "/virtual-devices" in path:
        return "device"
    if "/auth/" in path:
        return "auth"
    if "/faces/" in path:
        return "faces"
    if "/workspaces" in path or "/integrations/" in path:
        return "workspaces"
    if any("/" + x in path for x in ["captures", "sessions", "jobs"]):
        return "capture"
    if any(
        "/" + x in path
        for x in [
            "queries",
            "objects",
            "observations",
            "media",
            "search/",
            "tracks",
            "facts",
        ]
    ):
        return "query"
    return "social"


def auth(path, op):
    if path == "/v1/tts":
        return "bearer"
    if "/integrations/" in path:
        return "integration"
    if path.startswith("/v1/device/") and "/device/display/" not in path:
        return "device"
    if "/device/display/" in path or path in {
        "/v1/display/media",
        "/v1/display/face-group",
    }:
        return "signed"
    return "bearer" if op.get("security") else "none"


def resolve(schema, spec):
    while "$ref" in schema:
        schema = spec["components"]["schemas"][schema["$ref"].split("/")[-1]]
    return schema


def example(schema, spec, key="", depth=0):
    schema = resolve(schema, spec)
    if depth > 8:
        return None
    if key == "access_token" and schema.get("title") == "Access Token":
        return "{{access_token}}"
    if key in {"language", "username", "display_name"}:
        return "{{" + key + "}}"
    if "default" in schema and schema["default"] is not None:
        return schema["default"]
    if "enum" in schema:
        return schema["enum"][0]
    if "const" in schema:
        return schema["const"]
    for union in ("anyOf", "oneOf", "allOf"):
        if union in schema:
            return example(
                next((s for s in schema[union] if s.get("type") != "null"), {}),
                spec,
                key,
                depth + 1,
            )
    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        return {
            k: example(v, spec, k, depth + 1)
            for k, v in schema.get("properties", {}).items()
            if k in schema.get("required", []) or k in {"language"}
        }
    if kind == "array":
        return [example(schema.get("items", {}), spec, key, depth + 1)]
    if kind in {"number", "integer"}:
        return max(schema.get("minimum", 1), 1)
    if kind == "boolean":
        return False
    if schema.get("format") == "date-time":
        return "2026-11-03T12:00:00Z"
    if schema.get("format") == "date":
        return "2026-11-03"
    if (
        key in {"password", "email", "refresh_token", "access_token", "workspace_id"}
        or key.endswith("_id")
        or key in {"token", "integration_key", "device_key"}
    ):
        return "{{" + key + "}}"
    if schema.get("format") == "uuid":
        return "00000000-0000-4000-8000-000000000001"
    if key in {"query", "question"}:
        return "{{query}}"
    if key == "text":
        return "Where were the documents last seen?"
    return "example-" + (key or "value")


def write(path, content, check):
    file = ROOT / path
    if check:
        if not file.exists() or file.read_text() != content:
            raise SystemExit(
                f"Out of date: {path}; run python scripts/build_api_docs.py"
            )
    else:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)


def target_item(value, prefix, variables):
    """Namespace references and script storage, including saved response examples."""
    if isinstance(value, dict):
        return {k: target_item(v, prefix, variables) for k, v in value.items()}
    if isinstance(value, list):
        return [target_item(v, prefix, variables) for v in value]
    if not isinstance(value, str):
        return value
    value = re.sub(r"{{([^}]+)}}", lambda m: "{{" + prefix + "_" + m[1] + "}}", value)
    value = re.sub(
        r'(pm\.(?:variables|environment|collectionVariables)\.(?:get|set|has)\(")([^"\n]+)(")',
        lambda m: m[1] + prefix + "_" + m[2] + m[3],
        value,
    )
    for key in variables:
        value = value.replace(f"`{key}", f"`{prefix}_{key}")
    return value


def variable_description(key):
    return VARIABLE_DESCRIPTIONS.get(
        key,
        "Copy this identifier from an authorized response for this target. / "
        "Copia este identificador de una respuesta autorizada de este destino.",
    )


def generate(spec, check=False):
    spanish = json.loads((ROOT / "docs/postman/operation-labels.es.json").read_text())
    demo = json.loads((ROOT / "simulator/postman/demo.json").read_text())
    # Local routes are intentionally absent from the production contract.
    local = copy.deepcopy(spec)
    login = copy.deepcopy(spec["paths"]["/v1/auth/login"]["post"])
    login["summary"] = "Local login (local realm only)"
    local["paths"]["/v1/auth/local-login"] = {"post": login}
    local["paths"]["/v1/auth/local-session"] = {
        "get": {
            "summary": "Check local realm",
            "security": [{"HTTPBearer": []}],
            "responses": {"200": {"description": "Local realm confirmed"}},
        }
    }
    local["paths"]["/v1/auth/local-capture-profile"] = {
        "post": {
            "summary": "Local capture profile",
            "security": [{"HTTPBearer": []}],
            "responses": {"200": {"description": "Device capture profile"}},
        }
    }
    # Only include local operations that actually exist in the isolated router.
    source = (ROOT / "backend/app/http/local_access.py").read_text()
    for path in list(local["paths"]):
        if (
            "/auth/local-" in path
            and '"' + path.removeprefix("/v1") + '"' not in source
        ):
            del local["paths"][path]
    folders = {key: [] for key, _ in GROUPS}
    rows = {key: [] for key, _ in GROUPS}
    details = {key: [] for key, _ in GROUPS}
    all_vars = dict(DEFAULT_VARIABLES)
    for path, methods in local["paths"].items():
        for method, op in methods.items():
            if method not in METHODS:
                continue
            mode = auth(path, op)
            mutable = (
                method not in {"get", "head", "options"}
                and path not in READ_POSTS | AUTH_POSTS
                and not path.endswith("/records/search")
            )
            name = f"{method.upper()} {path}"
            summary = op.get("summary", name)
            translated = spanish.get(summary, summary)
            description = f"{summary} / {translated}\n\n" + (
                "Explicit action / Acción explícita (escritura o proveedor). Set `enable_write_requests=true` to send. / Activa esa variable para enviar."
                if mutable
                else "Read or session access / Consulta o acceso de sesión."
            )
            description += "\n\nUse your authorized workspace and role. Provider calls may incur costs. / Usa tu espacio y rol autorizados. Las llamadas a proveedores pueden tener coste."
            request = {
                "method": method.upper(),
                "header": [],
                "description": description,
                "url": {
                    "raw": "{{base_url}}" + re.sub(r"{([^}]+)}", r"{{\1}}", path),
                    "host": ["{{base_url}}"],
                    "path": [
                        re.sub(r"{([^}]+)}", r"{{\1}}", s)
                        for s in path.strip("/").split("/")
                    ],
                },
            }
            if mode == "bearer":
                request["auth"] = {
                    "type": "bearer",
                    "bearer": [
                        {"key": "token", "value": "{{access_token}}", "type": "string"}
                    ],
                }
            else:
                request["auth"] = {"type": "noauth"}
            if mode == "device":
                request["header"] = [
                    {"key": "X-RealityOS-Device-ID", "value": "{{device_id}}"},
                    {"key": "X-RealityOS-Device-Key", "value": "{{device_key}}"},
                ]
            if mode == "integration":
                request["header"] = [
                    {
                        "key": "X-RealityOS-Integration-Key",
                        "value": "{{integration_key}}",
                    }
                ]
            params = []
            for p in methods.get("parameters", []) + op.get("parameters", []):
                val = example(p.get("schema", {}), local, p["name"])
                params.append(
                    (p["name"], p["in"], bool(p.get("required")), p.get("schema", {}))
                )
                if p["in"] == "query":
                    request["url"].setdefault("query", []).append(
                        {
                            "key": p["name"],
                            "value": str(val).lower()
                            if isinstance(val, bool)
                            else str(val),
                            "disabled": not p.get("required", False),
                        }
                    )
                elif p["in"] == "header":
                    request["header"].append(
                        {
                            "key": p["name"],
                            "value": str(val),
                            "disabled": not p.get("required", False),
                        }
                    )
            content = op.get("requestBody", {}).get("content", {})
            body_schema = {}
            if content:
                mime = next(iter(content))
                body_schema = resolve(content[mime].get("schema", {}), local)
                if mime == "application/json":
                    request["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(
                            example(body_schema, local), indent=2, ensure_ascii=False
                        ),
                        "options": {"raw": {"language": "json"}},
                    }
                    if path == "/v1/auth/facebook":
                        request["body"]["raw"] = request["body"]["raw"].replace(
                            "{{access_token}}", "{{facebook_access_token}}"
                        )
                    if path == "/v1/auth/change-pending-email":
                        request["body"]["raw"] = request["body"]["raw"].replace(
                            "{{email}}", "{{new_email}}"
                        )
                    if path == "/v1/auth/reset-password":
                        request["body"]["raw"] = request["body"]["raw"].replace(
                            "{{password}}", "{{new_password}}"
                        )
                    request["header"].append(
                        {"key": "Content-Type", "value": "application/json"}
                    )
                elif mime in {
                    "multipart/form-data",
                    "application/x-www-form-urlencoded",
                }:
                    fields = []
                    for key, schema in body_schema.get("properties", {}).items():
                        resolved = resolve(schema, local)
                        variants = resolved.get("anyOf", [resolved])
                        binary = any(v.get("format") == "binary" for v in variants)
                        field = {
                            "key": key,
                            "type": "file" if binary else "text",
                            "disabled": key not in body_schema.get("required", []),
                        }
                        field["src" if binary else "value"] = (
                            "" if binary else str(example(schema, local, key))
                        )
                        fields.append(field)
                    kind = "formdata" if mime == "multipart/form-data" else "urlencoded"
                    request["body"] = {"mode": kind, kind: fields}
            for p, s in body_schema.get("properties", {}).items():
                params.append((p, "body", p in body_schema.get("required", []), s))
            enabled_query = [
                q for q in request["url"].get("query", []) if not q.get("disabled")
            ]
            if enabled_query:
                request["url"]["raw"] += "?" + "&".join(
                    q["key"] + "=" + q["value"] for q in enabled_query
                )
            tests = [
                'pm.test("Successful response / Respuesta correcta", () => pm.expect(pm.response.code).to.be.below(400));'
            ]
            if path in AUTH_POSTS | {"/v1/auth/facebook", "/v1/auth/guest"}:
                tests += [
                    'pm.test("Login succeeds / Acceso correcto", () => pm.expect(pm.response.code).to.eql(200));',
                    "if (pm.response.code === 200) {",
                    "  const b = pm.response.json();",
                    '  if (typeof b.access_token === "string" && b.access_token && typeof b.refresh_token === "string" && b.refresh_token) {',
                    '    pm.collectionVariables.set("access_token", b.access_token);',
                    '    pm.collectionVariables.set("refresh_token", b.refresh_token);',
                    '    if (pm.environment.has("access_token")) pm.environment.set("access_token", b.access_token);',
                    '    if (pm.environment.has("refresh_token")) pm.environment.set("refresh_token", b.refresh_token);',
                    "  }",
                    "}",
                ]
            events = [
                {"listen": "test", "script": {"type": "text/javascript", "exec": tests}}
            ]
            if mutable:
                events.insert(
                    0,
                    {
                        "listen": "prerequest",
                        "script": {
                            "type": "text/javascript",
                            "exec": [
                                'if (pm.variables.get("enable_write_requests") !== "true") { console.warn("Skipped write. / Escritura omitida: activa la variable enable_write_requests de este destino."); pm.execution.skipRequest(); }'
                            ],
                        },
                    },
                )
            saved = []
            for code, response in op.get("responses", {}).items():
                if not code.startswith("2"):
                    continue
                schema = (
                    response.get("content", {})
                    .get("application/json", {})
                    .get("schema")
                )
                if schema:
                    saved.append(
                        {
                            "name": "Synthetic example / Ejemplo sintético",
                            "originalRequest": copy.deepcopy(request),
                            "status": "Example",
                            "code": int(code),
                            "header": [
                                {"key": "Content-Type", "value": "application/json"}
                            ],
                            "body": json.dumps(
                                example(schema, local), indent=2, ensure_ascii=False
                            ),
                        }
                    )
                    break
            item = {
                "name": name,
                "request": request,
                "event": events,
                "response": saved,
            }
            folders[group(path)].append(item)
            required = (
                ", ".join("`" + p + "`" for p, where, req, s in params if req) or "—"
            )
            rows[group(path)].append((name, summary, mode, required, mutable))
            fieldrows = []
            for p, where, req, s in params:
                s = resolve(s, local)
                typ = s.get(
                    "type",
                    s.get(
                        "format",
                        " / ".join(
                            x.get("type", x.get("$ref", "").split("/")[-1])
                            for x in s.get("anyOf", [])
                        )
                        or "object",
                    ),
                )
                constraints = {
                    k: v
                    for k, v in s.items()
                    if k
                    in {
                        "enum",
                        "minimum",
                        "maximum",
                        "minLength",
                        "maxLength",
                        "pattern",
                        "default",
                    }
                }
                fieldrows.append(
                    f"| `{p}` | {where} | {'✓' if req else '—'} | `{typ}` | `{json.dumps(constraints, ensure_ascii=False).replace(chr(124), chr(92) + chr(124))}` |"
                )
            details[group(path)].append(
                (name, fieldrows, request.get("body"), op.get("responses", {}))
            )
            for var in re.findall(r"{{([^}]+)}}", json.dumps(item)):
                all_vars.setdefault(var, "")
    quick = []
    for name in [
        "GET /health/live",
        "POST /v1/auth/login",
        "GET /v1/auth/me",
        "GET /v1/workspaces",
        "POST /v1/queries",
    ]:
        quick.append(
            copy.deepcopy(
                next(i for f in folders.values() for i in f if i["name"] == name)
            )
        )
    quick[-1]["event"].insert(
        0,
        {
            "listen": "prerequest",
            "script": {
                "type": "text/javascript",
                "exec": [
                    'if (!pm.variables.get("workspace_id")) { throw new Error("Choose workspace_id from your authorized workspaces. / Selecciona workspace_id de este destino explícitamente."); }'
                ],
            },
        },
    )
    collection = {
        "info": {
            "name": "RealityOS API · EN / ES",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": "Two independent folders: Consultas servidor (https://realityos.luxisoft.com) and Consultas localhost (http://localhost:8080). All variables, public demo credentials and demo workspace IDs are included; environments are optional. Run 00 Quick start inside the chosen folder to log in, save tokens and query. The demo role is query-only in an empty test workspace; use your own authorized account for writes and real data. Enable the local demo once with scripts/local/Enable-PostmanDemo.ps1. / Dos carpetas independientes con variables, cuenta pública de prueba y espacio demo preconfigurados. Ejecuta 00 Quick start dentro del destino elegido para autenticar, guardar tokens y consultar. La cuenta demo tiene rol de consulta en un espacio vacío; para escrituras y datos propios usa tu cuenta autorizada. En localhost activa primero la demo con scripts/local/Enable-PostmanDemo.ps1. Los tokens de sesión nunca se incluyen en el archivo publicado.",
        },
        "item": [],
        "variable": [],
    }
    for realm, prefix, title, url in TARGETS:
        target_quick = copy.deepcopy(quick)
        target_folders = [
            {
                "name": "00 Quick start / Inicio rápido",
                "description": "Run this subfolder: health, login, current user, workspaces and query. Demo credentials and workspace are already configured; session tokens are saved automatically. / Ejecuta esta subcarpeta: salud, login, usuario, espacios y consulta. Credenciales y espacio demo ya configurados; los tokens se guardan automáticamente.",
                "item": target_quick,
            }
        ]
        target_folders += [
            {"name": f"{n:02} {label}", "item": folders[key]}
            for n, (key, label) in enumerate(GROUPS, 1)
            if folders[key] and (realm == "local" or key != "local")
        ]
        collection["item"].append(
            {
                "name": title,
                "description": f"{url} · Variables: {prefix}_* · "
                "Independent credentials, session and resource IDs. / Credenciales, sesión e IDs independientes.",
                "item": target_item(target_folders, prefix, all_vars),
            }
        )
        variables = dict(all_vars, base_url=url)
        for key in (
            "email",
            "username",
            "password",
            "display_name",
            "user_id",
            "workspace_id",
        ):
            variables[key] = demo[prefix][key]
        collection["variable"].extend(
            {
                "key": f"{prefix}_{k}",
                "value": v,
                "type": "string",
                "description": variable_description(k),
            }
            for k, v in sorted(variables.items())
        )
        env = {
            "name": f"RealityOS · {title}",
            "values": [
                {
                    "key": f"{prefix}_{k}",
                    "value": v,
                    "enabled": True,
                    "description": variable_description(k),
                    "type": "secret"
                    if any(s in k for s in ["password", "token", "key"])
                    and k != "enable_write_requests"
                    else "default",
                }
                for k, v in sorted(variables.items())
            ],
            "_postman_variable_scope": "environment",
        }
        write(
            f"docs/postman/RealityOS.{realm}.postman_environment.json",
            json.dumps(env, indent=2, ensure_ascii=False) + "\n",
            check,
        )
    write(
        "docs/postman/RealityOS.postman_collection.json",
        json.dumps(collection, indent=2, ensure_ascii=False) + "\n",
        check,
    )
    for lang in ["en", "es"]:
        es = lang == "es"
        suffix = ".es" if es else ""
        lines = [
            nav("API_REFERENCE", es),
            "# " + ("Referencia de operaciones" if es else "Operation reference"),
            f"[← API](API{suffix}.md) · [Postman](postman/RealityOS.postman_collection.json)",
            (
                "Generada del contrato. Los nombres de operaciones y campos conservan los identificadores del API. ✓ = obligatorio. Los ejemplos requieren tus identificadores y archivos; no son respuestas capturadas de producción."
                if es
                else "Generated from the contract. Operation and field names preserve API identifiers. ✓ = required. Examples need your own identifiers and files; they are not captured production responses."
            ),
            (
                "Los ejemplos de referencia usan variables sin prefijo. La colección descargable incluye las carpetas Consultas servidor y Consultas localhost y añade respectivamente `server_` o `localhost_` a cada variable, con cuenta y espacio demo preconfigurados."
                if es
                else "Reference examples use unprefixed variables. The downloadable collection includes Consultas servidor and Consultas localhost folders and prefixes each variable with `server_` or `localhost_`, with demo credentials and workspace IDs preconfigured."
            ),
            "Bearer = "
            + (
                "sesión de usuario; device = credenciales de dispositivo; integration = clave de integración; signed = enlace temporal; none = sin credenciales de transporte."
                if es
                else "user session; device = device credentials; integration = integration key; signed = temporary link; none = no transport credentials."
            ),
        ]
        for key, title in GROUPS:
            if not rows[key]:
                continue
            lines += [
                "## " + title.split(" / ")[int(es)],
                "| "
                + (
                    "Operación | Identificador descriptivo | Acceso | Campos obligatorios | Manual"
                    if es
                    else "Operation | Summary | Access | Required fields | Manual"
                )
                + " |",
                "| --- | --- | --- | --- | --- |",
            ]
            for name, summary, mode, required, mutable in rows[key]:
                lines.append(
                    f"| `{name}` | {spanish.get(summary, summary) if es else summary} | {mode} | {required} | {'✓' if mutable else '—'} |"
                )
            for name, fields, body, responses in details[key]:
                lines += [
                    "<details>",
                    f"<summary>{name}</summary>",
                    "",
                    "| "
                    + (
                        "Campo | Ubicación | Obligatorio | Tipo | Restricciones"
                        if es
                        else "Field | Location | Required | Type | Constraints"
                    )
                    + " |",
                    "| --- | --- | --- | --- | --- |",
                    *fields,
                ]
                if not fields:
                    lines.append("| — | — | — | — | — |")
                if body and body["mode"] == "raw":
                    lines += ["", "```json", body["raw"], "```"]
                lines += [
                    "",
                    ("Respuestas declaradas" if es else "Declared responses")
                    + ": "
                    + ", ".join("`" + r + "`" for r in responses)
                    + ".",
                    "",
                    "</details>",
                    "",
                ]
        write(
            f"docs/API_REFERENCE{suffix}.md",
            re.sub(
                r"(?<=\|)\n\n(?=\|)",
                "\n",
                re.sub(r"\n{3,}", "\n\n", "\n\n".join(lines)),
            )
            + "\n",
            check,
        )
    return collection


def nav(stem, es):
    return f'<p align="center"><a href="{stem}.md"><img src="assets/readme/language-en{"" if es else "-active"}.svg" alt="English" height="32"></a> <a href="{stem}.es.md"><img src="assets/readme/language-es{"-active" if es else ""}.svg" alt="Español" height="32"></a></p>'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--contract", type=Path, default=ROOT / "tests/contracts/openapi.json"
    )
    args = parser.parse_args()
    generate(json.loads(args.contract.read_text()), args.check)
