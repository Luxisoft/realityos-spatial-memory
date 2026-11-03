<p align="center"><a href="../../en/api/API_REFERENCE.md"><img src="../../assets/readme/language-en.svg" alt="English" height="32"></a> <a href="../../es/api/API_REFERENCE.md"><img src="../../assets/readme/language-es-active.svg" alt="Español" height="32"></a></p>

# Referencia de operaciones

[← API](API.md) · [Postman](../../postman/RealityOS.reference.postman_collection.json)

Generada del contrato. Los nombres de operaciones y campos conservan los identificadores del API. ✓ = obligatorio. Los ejemplos requieren tus identificadores y archivos; no son respuestas capturadas de producción.

Los ejemplos de referencia usan variables sin prefijo. La colección descargable incluye las carpetas Server requests y Localhost requests y añade respectivamente `server_` o `localhost_` a cada variable, con cuenta y espacio demo preconfigurados.

Bearer = sesión de usuario; device = credenciales de dispositivo; integration = clave de integración; signed = enlace temporal; none = sin credenciales de transporte.

## Acceso

| Operación | Identificador descriptivo | Acceso | Campos obligatorios | Manual |
| --- | --- | --- | --- | --- |
| `POST /v1/auth/login` | Iniciar sesión | none | `email`, `password` | — |
| `POST /v1/auth/refresh` | Renovar sesión | none | `refresh_token` | — |
| `GET /v1/auth/me` | Consultar mi usuario | bearer | — | — |
| `POST /v1/auth/register` | Registrar cuenta | none | `username`, `email`, `display_name`, `password` | ✓ |
| `POST /v1/auth/resend-confirmation` | Reenviar confirmación | none | `email` | ✓ |
| `POST /v1/auth/change-pending-email` | Cambiar correo de cuenta pendiente | none | `username`, `email`, `password` | ✓ |
| `POST /v1/auth/confirm-email` | Confirmar correo | none | `token` | ✓ |
| `POST /v1/auth/forgot-password` | Solicitar recuperación | none | `email` | ✓ |
| `POST /v1/auth/reset-password` | Restablecer contraseña | none | `token`, `password` | ✓ |
| `GET /v1/auth/account-session` | Consultar estado de cuenta | bearer | — | — |
| `POST /v1/auth/account-capture-profile` | Obtener credencial de captura | bearer | — | ✓ |
| `POST /v1/auth/logout` | Cerrar sesión | bearer | — | ✓ |
| `POST /v1/auth/facebook` | Acceder mediante Facebook | none | `access_token` | ✓ |
| `POST /v1/auth/guest` | Acceder como invitado | none | `device_id` | ✓ |

<details>

<summary>POST /v1/auth/login</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 3}` |
| `password` | body | ✓ | `string` | `{"maxLength": 512, "minLength": 1}` |

```json

{
  "email": "{{email}}",
  "password": "{{password}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/auth/refresh</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `refresh_token` | body | ✓ | `string` | `{"minLength": 20}` |

```json

{
  "refresh_token": "{{refresh_token}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/auth/me</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/auth/register</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `username` | body | ✓ | `string` | `{"pattern": "^[a-zA-Z][a-zA-Z0-9_.-]{2,63}$"}` |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 5}` |
| `display_name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 1}` |
| `password` | body | ✓ | `string` | `{"maxLength": 512, "minLength": 12}` |

```json

{
  "username": "{{username}}",
  "email": "{{email}}",
  "display_name": "{{display_name}}",
  "password": "{{password}}"
}

```

Respuestas declaradas: `202`, `422`.

</details>

<details>

<summary>POST /v1/auth/resend-confirmation</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 3}` |

```json

{
  "email": "{{email}}"
}

```

Respuestas declaradas: `202`, `422`.

</details>

<details>

<summary>POST /v1/auth/change-pending-email</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `username` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 3}` |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 5}` |
| `password` | body | ✓ | `string` | `{"maxLength": 512, "minLength": 1}` |

```json

{
  "username": "{{username}}",
  "email": "{{new_email}}",
  "password": "{{password}}"
}

```

Respuestas declaradas: `202`, `422`.

</details>

<details>

<summary>POST /v1/auth/confirm-email</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `token` | body | ✓ | `string` | `{"maxLength": 128, "minLength": 32}` |

```json

{
  "token": "{{token}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/auth/forgot-password</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 3}` |

```json

{
  "email": "{{email}}"
}

```

Respuestas declaradas: `202`, `422`.

</details>

<details>

<summary>POST /v1/auth/reset-password</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `token` | body | ✓ | `string` | `{"maxLength": 128, "minLength": 32}` |
| `password` | body | ✓ | `string` | `{"maxLength": 512, "minLength": 12}` |

```json

{
  "token": "{{token}}",
  "password": "{{new_password}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/auth/account-session</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/auth/account-capture-profile</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/auth/logout</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/auth/facebook</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `access_token` | body | ✓ | `string` | `{"maxLength": 4096, "minLength": 1}` |
| `device_id` | body | — | `string / null` | `{}` |

```json

{
  "access_token": "{{facebook_access_token}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/auth/guest</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `device_id` | body | ✓ | `string` | `{"maxLength": 128, "minLength": 1}` |

```json

{
  "device_id": "{{device_id}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

## Espacios y expedientes

| Operación | Identificador descriptivo | Acceso | Campos obligatorios | Manual |
| --- | --- | --- | --- | --- |
| `GET /v1/workspaces` | Listar mis espacios | bearer | — | — |
| `POST /v1/workspaces` | Crear espacio | bearer | `name` | ✓ |
| `GET /v1/workspaces/{workspace_id}/zones` | Listar zonas | bearer | `workspace_id` | — |
| `POST /v1/workspaces/{workspace_id}/zones` | Crear zona | bearer | `workspace_id`, `name` | ✓ |
| `POST /v1/workspaces/{workspace_id}/connections` | Crear conexión de datos | bearer | `workspace_id`, `name` | ✓ |
| `GET /v1/workspaces/{workspace_id}/connections` | Listar conexiones | bearer | `workspace_id` | — |
| `DELETE /v1/workspaces/{workspace_id}/connections/{connection_id}` | Revocar conexión | bearer | `workspace_id`, `connection_id` | ✓ |
| `POST /v1/integrations/imports` | Importar lote versionado | integration | `request_key`, `records` | ✓ |
| `GET /v1/integrations/imports/{run_id}` | Consultar estado de importación | integration | `run_id` | — |
| `GET /v1/workspaces/{workspace_id}/records` | Listar expedientes | bearer | `workspace_id` | — |
| `GET /v1/workspaces/{workspace_id}/records/{record_id}` | Abrir expediente | bearer | `workspace_id`, `record_id` | — |
| `POST /v1/workspaces/{workspace_id}/records/{record_id}/notes` | Añadir nota | bearer | `workspace_id`, `record_id`, `text`, `occurred_at` | ✓ |
| `GET /v1/workspaces/{workspace_id}/records/{record_id}/revisions` | Consultar revisiones | bearer | `workspace_id`, `record_id` | — |
| `POST /v1/workspaces/{workspace_id}/records/{record_id}/publications` | Vincular publicación | bearer | `workspace_id`, `record_id`, `publication_id` | ✓ |
| `POST /v1/workspaces/{workspace_id}/records/{person_id}/medication-check` | Comparar campos de medicación | bearer | `workspace_id`, `person_id`, `prescription_id`, `observed_ingredient`, `observed_concentration`, `checked_at` | ✓ |
| `POST /v1/integrations/records/{record_id}/media` | Subir adjunto | integration | `record_id`, `external_id`, `file` | ✓ |
| `POST /v1/integrations/records/{record_id}/index` | Reintentar indexación | integration | `record_id` | ✓ |
| `GET /v1/workspaces/{workspace_id}/record-media/{link_id}` | Obtener medio autorizado | bearer | `workspace_id`, `link_id` | — |
| `POST /v1/workspaces/{workspace_id}/test-workers` | Provisionar cuentas de prueba | bearer | `workspace_id`, `username`, `display_name` | ✓ |
| `POST /v1/workspaces/{workspace_id}/records/search` | Consultar contexto de expedientes | bearer | `workspace_id`, `question` | — |
| `POST /v1/workspaces/{workspace_id}/connections/{connection_id}/sync` | Sincronizar conexión | bearer | `workspace_id`, `connection_id` | ✓ |

<details>

<summary>GET /v1/workspaces</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/workspaces</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `description` | body | — | `string / null` | `{}` |

```json

{
  "name": "example-name"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/zones</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/zones</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 1}` |
| `parent_id` | body | — | `string / null` | `{}` |
| `kind` | body | — | `string` | `{"maxLength": 32, "minLength": 1, "default": "zone"}` |
| `sort_order` | body | — | `integer` | `{"maximum": 9999.0, "minimum": 0.0, "default": 0}` |

```json

{
  "name": "example-name"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/connections</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `source_url` | body | — | `string / null` | `{}` |
| `source_token` | body | — | `string / null` | `{}` |

```json

{
  "name": "example-name"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/connections</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/workspaces/{workspace_id}/connections/{connection_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `connection_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/integrations/imports</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `request_key` | body | ✓ | `string` | `{"maxLength": 128, "minLength": 1}` |
| `records` | body | ✓ | `array` | `{}` |

```json

{
  "request_key": "example-request_key",
  "records": [
    {
      "external_id": "{{external_id}}",
      "kind": "person",
      "title": "example-title",
      "version": 1.0,
      "occurred_at": "2026-11-03T12:00:00Z"
    }
  ]
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/integrations/imports/{run_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `run_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/records</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `q` | query | — | `string` | `{"maxLength": 200, "default": ""}` |
| `kind` | query | — | `string / null` | `{}` |
| `offset` | query | — | `integer` | `{"minimum": 0, "default": 0}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/records/{record_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `record_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/records/{record_id}/notes</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `record_id` | path | ✓ | `string` | `{}` |
| `text` | body | ✓ | `string` | `{"maxLength": 10000, "minLength": 1}` |
| `occurred_at` | body | ✓ | `string` | `{}` |

```json

{
  "text": "Where were the documents last seen?",
  "occurred_at": "2026-11-03T12:00:00Z"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/records/{record_id}/revisions</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `record_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/records/{record_id}/publications</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `record_id` | path | ✓ | `string` | `{}` |
| `publication_id` | body | ✓ | `string` | `{}` |

```json

{
  "publication_id": "{{publication_id}}"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/records/{person_id}/medication-check</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `person_id` | path | ✓ | `string` | `{}` |
| `prescription_id` | body | ✓ | `string` | `{}` |
| `observed_ingredient` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 1}` |
| `observed_concentration` | body | ✓ | `string` | `{"maxLength": 80, "minLength": 1}` |
| `patient_confirmed` | body | — | `boolean` | `{"default": false}` |
| `checked_at` | body | ✓ | `string` | `{}` |

```json

{
  "prescription_id": "{{prescription_id}}",
  "observed_ingredient": "example-observed_ingredient",
  "observed_concentration": "example-observed_concentration",
  "checked_at": "2026-11-03T12:00:00Z"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/integrations/records/{record_id}/media</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `record_id` | path | ✓ | `string` | `{}` |
| `external_id` | body | ✓ | `string` | `{"maxLength": 160}` |
| `publish` | body | — | `boolean` | `{"default": false}` |
| `author_id` | body | — | `string / null` | `{}` |
| `file` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>POST /v1/integrations/records/{record_id}/index</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `record_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/workspaces/{workspace_id}/record-media/{link_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `link_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/test-workers</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `username` | body | ✓ | `string` | `{"pattern": "^[a-z][a-z0-9_.-]{2,63}$"}` |
| `display_name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `role` | body | — | `string` | `{"enum": ["admin", "register", "query"]}` |

```json

{
  "username": "{{username}}",
  "display_name": "{{display_name}}"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/records/search</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `question` | body | ✓ | `string` | `{"maxLength": 1000, "minLength": 2}` |
| `language` | body | — | `string` | `{"pattern": "^(es\|en)$", "default": "es"}` |
| `record_id` | body | — | `string / null` | `{}` |

```json

{
  "question": "{{query}}",
  "language": "{{language}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/workspaces/{workspace_id}/connections/{connection_id}/sync</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `connection_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

## Reconocimiento facial

| Operación | Identificador descriptivo | Acceso | Campos obligatorios | Manual |
| --- | --- | --- | --- | --- |
| `GET /v1/faces/consent` | Consultar consentimiento biométrico | bearer | — | — |
| `POST /v1/faces/consent` | Otorgar consentimiento biométrico | bearer | `confirm` | ✓ |
| `DELETE /v1/faces/consent` | Revocar consentimiento biométrico | bearer | — | ✓ |
| `POST /v1/faces/verify-identity` | Verificar identidad de la cuenta | bearer | — | ✓ |
| `POST /v1/faces/profile-photo` | Enrolar foto de perfil | bearer | `file` | ✓ |
| `POST /v1/faces/enroll` | Enrolar medio propio | bearer | `media_id` | ✓ |
| `GET /v1/faces/enrollments` | Consultar mis enrolamientos | bearer | — | — |
| `POST /v1/faces/record-enroll` | Enrolar retrato de expediente | bearer | `record_id` | ✓ |
| `GET /v1/faces/record-enrollments` | Consultar enrolamientos de expedientes | bearer | `workspace_id` | — |
| `DELETE /v1/faces/record-enrollments/{enrollment_id}` | Eliminar enrolamiento de expediente | bearer | `enrollment_id` | ✓ |
| `POST /v1/faces/search` | Buscar candidatos faciales | bearer | `workspace_id` | — |
| `GET /v1/faces/enrollments/{enrollment_id}/thumbnail` | Ver evidencia del enrolamiento | bearer | `enrollment_id` | — |
| `GET /v1/faces/record-enrollments/{enrollment_id}/thumbnail` | Ver evidencia del expediente enrolado | bearer | `enrollment_id` | — |
| `POST /v1/faces/reference-photos` | Add Reference | bearer | `file` | ✓ |
| `DELETE /v1/faces/reference-photos/{enrollment_id}` | Remove Reference | bearer | `enrollment_id` | ✓ |
| `GET /v1/faces/setup` | Status | bearer | — | — |
| `POST /v1/faces/setup/complete` | Complete | bearer | — | ✓ |

<details>

<summary>GET /v1/faces/consent</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/faces/consent</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `confirm` | body | ✓ | `boolean` | `{}` |

```json

{
  "confirm": false
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/faces/consent</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/faces/verify-identity</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/faces/profile-photo</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>POST /v1/faces/enroll</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `media_id` | body | ✓ | `string` | `{}` |

```json

{
  "media_id": "{{media_id}}"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>GET /v1/faces/enrollments</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/faces/record-enroll</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `record_id` | body | ✓ | `string` | `{}` |
| `media_id` | body | — | `string / null` | `{}` |
| `record_media_id` | body | — | `string / null` | `{}` |
| `biometric_basis` | body | — | `string / null` | `{}` |

```json

{
  "record_id": "{{record_id}}"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>GET /v1/faces/record-enrollments</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | query | ✓ | `string` | `{}` |
| `record_id` | query | — | `string / null` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/faces/record-enrollments/{enrollment_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `enrollment_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/faces/search</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `media_id` | body | — | `string / null` | `{}` |
| `probe` | body | — | `string / null` | `{}` |
| `include_records` | body | — | `boolean` | `{"default": true}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/faces/enrollments/{enrollment_id}/thumbnail</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `enrollment_id` | path | ✓ | `string` | `{}` |
| `full_size` | query | — | `boolean` | `{"default": true}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/faces/record-enrollments/{enrollment_id}/thumbnail</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `enrollment_id` | path | ✓ | `string` | `{}` |
| `full_size` | query | — | `boolean` | `{"default": true}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/faces/reference-photos</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>DELETE /v1/faces/reference-photos/{enrollment_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `enrollment_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/faces/setup</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/faces/setup/complete</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

## Captura y procesamiento

| Operación | Identificador descriptivo | Acceso | Campos obligatorios | Manual |
| --- | --- | --- | --- | --- |
| `POST /v1/sessions` | Abrir sesión de captura | bearer | `workspace_id`, `consent_confirmed` | ✓ |
| `GET /v1/sessions/{session_id}` | Consultar sesión de captura | bearer | `session_id` | — |
| `POST /v1/sessions/{session_id}/close` | Cerrar sesión de captura | bearer | `session_id` | ✓ |
| `POST /v1/captures` | Subir captura | bearer | `session_id`, `file` | ✓ |
| `GET /v1/captures/{capture_id}` | Consultar captura | bearer | `capture_id` | — |
| `POST /v1/captures/{capture_id}/process` | Procesar captura | bearer | `capture_id` | ✓ |
| `GET /v1/jobs/{job_id}` | Consultar trabajo | bearer | `job_id` | — |

<details>

<summary>POST /v1/sessions</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `zone_id` | body | — | `string / null` | `{}` |
| `consent_confirmed` | body | ✓ | `boolean` | `{}` |

```json

{
  "workspace_id": "{{workspace_id}}",
  "consent_confirmed": false
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>GET /v1/sessions/{session_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `session_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/sessions/{session_id}/close</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `session_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/captures</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `session_id` | body | ✓ | `string` | `{}` |
| `captured_at` | body | — | `string / null` | `{}` |
| `file` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>GET /v1/captures/{capture_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `capture_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/captures/{capture_id}/process</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `capture_id` | path | ✓ | `string` | `{}` |

```json

{}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/jobs/{job_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `job_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

## Consultas y evidencia

| Operación | Identificador descriptivo | Acceso | Campos obligatorios | Manual |
| --- | --- | --- | --- | --- |
| `GET /v1/objects` | Listar objetos | bearer | `workspace_id` | — |
| `GET /v1/objects/{object_id}` | Consultar objeto | bearer | `object_id` | — |
| `POST /v1/objects/{object_id}/aliases` | Añadir alias de objeto | bearer | `object_id`, `alias` | ✓ |
| `GET /v1/objects/{object_id}/history` | Consultar historial del objeto | bearer | `object_id` | — |
| `GET /v1/objects/{object_id}/facts` | Consultar hechos del objeto | bearer | `object_id` | — |
| `PATCH /v1/facts/{fact_id}` | Revisar un hecho | bearer | `fact_id`, `verification_status` | ✓ |
| `GET /v1/objects/{object_id}/tracks` | Consultar seguimiento del objeto | bearer | `object_id` | — |
| `GET /v1/tracks/{track_id}/frames` | Consultar fotogramas del seguimiento | bearer | `track_id` | — |
| `PATCH /v1/observations/{observation_id}` | Revisar observación | bearer | `observation_id`, `verification_status` | ✓ |
| `POST /v1/observations/{observation_id}/segment` | Solicitar refinamiento SAM | bearer | `observation_id` | ✓ |
| `POST /v1/queries` | Consultar evidencia de objetos | bearer | `workspace_id`, `question` | — |
| `POST /v1/queries/image` | Consultar por imagen | bearer | `workspace_id`, `image` | — |
| `POST /v1/search/classify` | Clasificar imagen de consulta | bearer | `workspace_id`, `image` | — |
| `POST /v1/search/route` | Clasificar intención del texto | bearer | `text` | — |
| `POST /v1/queries/audio` | Consultar por audio | bearer | `workspace_id`, `audio` | — |
| `GET /v1/media/{media_id}` | Obtener medio autorizado | bearer | `media_id` | — |
| `GET /v1/observations/{observation_id}/highlighted` | Ver observación señalada | bearer | `observation_id` | — |
| `GET /v1/media/{media_id}/highlighted` | Obtener medio señalado | bearer | `media_id` | — |
| `GET /v1/me/storage-connections/{connection_id}/objects` | Objects | bearer | `connection_id` | — |
| `GET /v1/profiles/{user_id}/media` | Paginar medios del perfil | bearer | `user_id` | — |
| `GET /v1/gallery/{post_id}/media` | Obtener medio autorizado | bearer | `post_id` | — |

<details>

<summary>GET /v1/objects</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | query | ✓ | `string` | `{}` |
| `q` | query | — | `string / null` | `{}` |
| `category` | query | — | `string / null` | `{}` |
| `zone_id` | query | — | `string / null` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/objects/{object_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `object_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/objects/{object_id}/aliases</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `object_id` | path | ✓ | `string` | `{}` |
| `alias` | body | ✓ | `string` | `{"maxLength": 240, "minLength": 2}` |

```json

{
  "alias": "example-alias"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>GET /v1/objects/{object_id}/history</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `object_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/objects/{object_id}/facts</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `object_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>PATCH /v1/facts/{fact_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `fact_id` | path | ✓ | `string` | `{}` |
| `verification_status` | body | ✓ | `string` | `{"enum": ["verified", "rejected"]}` |
| `value_text` | body | — | `string / null` | `{}` |
| `normalized_value` | body | — | `string / null` | `{}` |

```json

{
  "verification_status": "verified"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/objects/{object_id}/tracks</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `object_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/tracks/{track_id}/frames</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `track_id` | path | ✓ | `string` | `{}` |
| `offset` | query | — | `integer` | `{"default": 0}` |
| `limit` | query | — | `integer` | `{"default": 240}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>PATCH /v1/observations/{observation_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `observation_id` | path | ✓ | `string` | `{}` |
| `verification_status` | body | ✓ | `string` | `{"enum": ["verified", "rejected"]}` |
| `spatial_description` | body | — | `string / null` | `{}` |

```json

{
  "verification_status": "verified"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/observations/{observation_id}/segment</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `observation_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `202`, `422`.

</details>

<details>

<summary>POST /v1/queries</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `question` | body | ✓ | `string` | `{"maxLength": 500, "minLength": 2}` |
| `language` | body | — | `string` | `{"maxLength": 16, "default": "en"}` |
| `search_scope` | body | — | `string` | `{"enum": ["auto", "gallery", "registry"], "default": "auto"}` |

```json

{
  "workspace_id": "{{workspace_id}}",
  "question": "{{query}}",
  "language": "{{language}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/queries/image</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `image` | body | ✓ | `string` | `{}` |
| `question` | body | — | `string` | `{"default": ""}` |
| `language` | body | — | `string` | `{"default": "en"}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/search/classify</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `image` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/search/route</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `text` | body | ✓ | `string` | `{"maxLength": 2000, "minLength": 2}` |

```json

{
  "text": "Where were the documents last seen?"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/queries/audio</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `audio` | body | ✓ | `string` | `{}` |
| `language` | body | — | `string` | `{"default": "en"}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/media/{media_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `media_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/observations/{observation_id}/highlighted</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `observation_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/media/{media_id}/highlighted</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `media_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/storage-connections/{connection_id}/objects</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `prefix` | query | — | `string` | `{"default": ""}` |
| `cursor` | query | — | `string / null` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/profiles/{user_id}/media</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `user_id` | path | ✓ | `string` | `{}` |
| `limit` | query | — | `integer` | `{"default": 12}` |
| `cursor` | query | — | `string / null` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery/{post_id}/media</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

## Perfiles y social

| Operación | Identificador descriptivo | Acceso | Campos obligatorios | Manual |
| --- | --- | --- | --- | --- |
| `POST /v1/tts` | Generar respuesta hablada | bearer | `text`, `language` | ✓ |
| `GET /v1/me/storage-connections` | Listar conexiones | bearer | — | — |
| `POST /v1/me/storage-connections` | Create | bearer | `name`, `endpoint`, `bucket` | ✓ |
| `PUT /v1/me/storage-connections/{connection_id}` | Update | bearer | `connection_id`, `name`, `endpoint`, `bucket` | ✓ |
| `DELETE /v1/me/storage-connections/{connection_id}` | Disconnect | bearer | `connection_id` | ✓ |
| `POST /v1/me/storage-connections/{connection_id}/test` | Test | bearer | `connection_id` | ✓ |
| `GET /v1/me/storage-connections/{connection_id}/content` | Content | bearer | `connection_id`, `key` | — |
| `POST /v1/me/storage-connections/{connection_id}/cv` | Cv | bearer | `connection_id`, `key` | ✓ |
| `POST /v1/me/storage-connections/{connection_id}/imports` | Start Import | bearer | `connection_id`, `request_key`, `keys` | ✓ |
| `GET /v1/me/storage-connections/{connection_id}/imports` | Imports | bearer | `connection_id` | — |
| `POST /v1/me/storage-connections/{connection_id}/imports/{run_id}/retry` | Retry | bearer | `connection_id`, `run_id` | ✓ |
| `GET /v1/me/storage-connections/{connection_id}/syncs` | Syncs | bearer | `connection_id` | — |
| `POST /v1/me/storage-connections/{connection_id}/syncs` | Create Sync | bearer | `connection_id` | ✓ |
| `POST /v1/me/storage-connections/{connection_id}/syncs/{rule_id}/run` | Run Sync | bearer | `connection_id`, `rule_id` | ✓ |
| `DELETE /v1/me/storage-connections/{connection_id}/syncs/{rule_id}` | Stop Sync | bearer | `connection_id`, `rule_id` | ✓ |
| `POST /v1/me/profile/avatar` | Cambiar avatar | bearer | `file` | ✓ |
| `GET /v1/me/social-capabilities` | Consultar capacidades sociales | bearer | — | — |
| `GET /v1/groups/{workspace_id}/members` | Listar miembros | bearer | `workspace_id` | — |
| `POST /v1/groups/{workspace_id}/members/{member_id}/invite-permission` | Cambiar permiso para invitar | bearer | `workspace_id`, `member_id` | ✓ |
| `POST /v1/groups/{workspace_id}/members/{member_id}/remove` | Retirar miembro | bearer | `workspace_id`, `member_id` | ✓ |
| `POST /v1/groups` | Crear grupo | bearer | — | ✓ |
| `GET /v1/groups/{workspace_id}/pin` | Consultar PIN del grupo | bearer | `workspace_id` | — |
| `POST /v1/groups/{workspace_id}/pin/rotate` | Renovar PIN del grupo | bearer | `workspace_id` | ✓ |
| `DELETE /v1/groups/{workspace_id}` | Eliminar grupo | bearer | `workspace_id` | ✓ |
| `POST /v1/groups/join-by-pin` | Unirse mediante PIN | bearer | `pin` | ✓ |
| `POST /v1/chat/append` | Guardar turno de conversación | bearer | `text` | ✓ |
| `GET /v1/chat/history` | Consultar historial de chat | bearer | — | — |
| `POST /v1/chat/audio` | Guardar audio de chat | bearer | `message_id`, `audio` | ✓ |
| `GET /v1/chat/audio/{audio_id}` | Descargar audio de chat | bearer | `audio_id` | — |
| `POST /v1/notes/merge` | Combinar notas | bearer | `texts` | ✓ |
| `POST /v1/groups/{workspace_id}/invite` | Crear invitación | bearer | `workspace_id` | ✓ |
| `POST /v1/groups/join` | Aceptar invitación | bearer | — | ✓ |
| `POST /v1/gallery/{post_id}/remove` | Retirar publicación | bearer | `post_id` | ✓ |
| `POST /v1/assistant` | Consultar asistente | bearer | `text` | ✓ |
| `POST /v1/gallery/{post_id}/share` | Compartir publicación | bearer | `post_id`, `audience` | ✓ |
| `GET /v1/groups/{workspace_id}/reports` | Consultar reportes del grupo | bearer | `workspace_id` | — |
| `POST /v1/groups/{workspace_id}/hide/{post_id}` | Ocultar publicación del grupo | bearer | `workspace_id`, `post_id` | ✓ |
| `GET /v1/me/facebook-profile` | Consultar mi perfil sincronizado | bearer | — | — |
| `GET /v1/me/profile` | Consultar mi perfil | bearer | — | — |
| `PATCH /v1/me/profile` | Actualizar mi perfil | bearer | — | ✓ |
| `GET /v1/profiles/{user_id}` | Consultar perfil visible | bearer | `user_id` | — |
| `GET /v1/profiles/{user_id}/avatar` | Obtener avatar de perfil | bearer | `user_id` | — |
| `POST /v1/me/profile/cv` | Reemplazar CV privado | bearer | `file` | ✓ |
| `DELETE /v1/me/profile/cv` | Eliminar CV privado | bearer | — | ✓ |
| `POST /v1/notes/transcribe` | Transcribir nota | bearer | `audio` | ✓ |
| `POST /v1/me/profile/publications` | Publicar en mi perfil | bearer | `file`, `workspace_id` | ✓ |
| `POST /v1/me/work-publications` | Publicar en espacio de trabajo | bearer | `workspace_id`, `file` | ✓ |
| `POST /v1/me/profile/cv/retry` | Reintentar procesamiento de CV | bearer | — | ✓ |
| `POST /v1/profiles/search` | Consultar perfiles autorizados | bearer | `question` | — |
| `GET /v1/gallery/page` | Paginar galería | bearer | — | — |
| `GET /v1/gallery` | Consultar galería | bearer | — | — |
| `POST /v1/gallery` | Crear publicación | bearer | `media_id` | ✓ |
| `POST /v1/me/capture-profile` | Obtener credencial de captura | bearer | — | ✓ |
| `GET /v1/gallery/{post_id}/thumbnail` | Obtener miniatura | bearer | `post_id` | — |
| `GET /v1/gallery/{post_id}/boxed` | Obtener miniatura señalada | bearer | `post_id` | — |
| `POST /v1/gallery/{post_id}/interactions` | Registrar interacción | bearer | `post_id`, `action` | ✓ |
| `GET /v1/gallery/{post_id}/comments` | Consultar comentarios | bearer | `post_id` | — |
| `GET /v1/me/preferences` | Leer preferencias | bearer | — | — |
| `PATCH /v1/me/preferences` | Actualizar preferencias | bearer | `preferred_language` | ✓ |
| `POST /v1/chat/history/prepare` | Preparar traducciones del historial | bearer | `message_ids` | ✓ |
| `GET /v1/chat/history/translations` | Leer traducciones del historial | bearer | `ids` | — |
| `POST /v1/gallery/evidence/information` | Leer información de evidencia | bearer | `items` | — |
| `POST /v1/gallery/evidence/information/prepare` | Preparar información bilingüe | bearer | `items` | ✓ |
| `GET /v1/gallery/evidence/{evidence_id}` | Obtener imagen de evidencia | bearer | `evidence_id` | — |
| `POST /v1/me/publication-uploads` | Preparar publicación para revisión | bearer | `file`, `request_key` | ✓ |
| `GET /v1/me/publication-uploads/{upload_id}` | Consultar estado de publicación | bearer | `upload_id` | — |
| `GET /v1/me/publication-uploads/{upload_id}/preview` | Ver publicación pendiente | bearer | `upload_id` | — |
| `POST /v1/me/publication-uploads/{upload_id}/confirm` | Confirmar publicación | bearer | `upload_id` | ✓ |
| `POST /v1/me/publication-uploads/{upload_id}/cancel` | Cancelar publicación pendiente | bearer | `upload_id` | ✓ |
| `POST /v1/me/publication-uploads/{upload_id}/retry` | Reintentar publicación | bearer | `upload_id` | ✓ |
| `POST /v1/groups/{workspace_id}/publications/import` | Import Group Publications | bearer | `workspace_id`, `publication_ids` | ✓ |

<details>

<summary>POST /v1/tts</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `text` | body | ✓ | `string` | `{"maxLength": 4000, "minLength": 1}` |
| `language` | body | ✓ | `string` | `{"enum": ["es", "en"]}` |

```json

{
  "text": "Where were the documents last seen?",
  "language": "{{language}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/storage-connections</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/me/storage-connections</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `provider` | body | — | `string` | `{"enum": ["r2", "s3"], "default": "r2"}` |
| `endpoint` | body | ✓ | `string` | `{"maxLength": 2048}` |
| `bucket` | body | ✓ | `string` | `{"pattern": "^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$"}` |
| `region` | body | — | `string` | `{"pattern": "^[a-zA-Z0-9-]{1,80}$", "default": "auto"}` |
| `prefix` | body | — | `string` | `{"maxLength": 1024, "default": ""}` |
| `access_key` | body | — | `string / null` | `{}` |
| `secret_key` | body | — | `string / null` | `{}` |
| `workspace_id` | body | — | `string / null` | `{}` |

```json

{
  "name": "example-name",
  "endpoint": "example-endpoint",
  "bucket": "example-bucket"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>PUT /v1/me/storage-connections/{connection_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `name` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `provider` | body | — | `string` | `{"enum": ["r2", "s3"], "default": "r2"}` |
| `endpoint` | body | ✓ | `string` | `{"maxLength": 2048}` |
| `bucket` | body | ✓ | `string` | `{"pattern": "^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$"}` |
| `region` | body | — | `string` | `{"pattern": "^[a-zA-Z0-9-]{1,80}$", "default": "auto"}` |
| `prefix` | body | — | `string` | `{"maxLength": 1024, "default": ""}` |
| `access_key` | body | — | `string / null` | `{}` |
| `secret_key` | body | — | `string / null` | `{}` |
| `workspace_id` | body | — | `string / null` | `{}` |

```json

{
  "name": "example-name",
  "endpoint": "example-endpoint",
  "bucket": "example-bucket"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/me/storage-connections/{connection_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/test</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/storage-connections/{connection_id}/content</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `key` | query | ✓ | `string` | `{"maxLength": 1024}` |
| `preview` | query | — | `boolean` | `{"default": false}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/cv</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `key` | body | ✓ | `string` | `{"maxLength": 1024, "minLength": 1}` |

```json

{
  "key": "example-key"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/imports</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `request_key` | body | ✓ | `string` | `{"maxLength": 128, "minLength": 1}` |
| `keys` | body | ✓ | `array` | `{}` |
| `audience` | body | — | `string` | `{"default": "work"}` |
| `workspace_id` | body | — | `string / null` | `{}` |

```json

{
  "request_key": "example-request_key",
  "keys": [
    "example-keys"
  ]
}

```

Respuestas declaradas: `202`, `422`.

</details>

<details>

<summary>GET /v1/me/storage-connections/{connection_id}/imports</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/imports/{run_id}/retry</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `run_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/storage-connections/{connection_id}/syncs</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/syncs</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `prefix` | body | — | `string` | `{"maxLength": 1024, "default": ""}` |
| `audience` | body | — | `string` | `{"default": "work"}` |
| `workspace_id` | body | — | `string / null` | `{}` |
| `interval_minutes` | body | — | `integer` | `{"enum": [15, 60, 1440], "default": 15}` |
| `enabled` | body | — | `boolean` | `{"default": false}` |

```json

{}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>POST /v1/me/storage-connections/{connection_id}/syncs/{rule_id}/run</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `rule_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `202`, `422`.

</details>

<details>

<summary>DELETE /v1/me/storage-connections/{connection_id}/syncs/{rule_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `connection_id` | path | ✓ | `string` | `{}` |
| `rule_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/profile/avatar</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/social-capabilities</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>GET /v1/groups/{workspace_id}/members</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/members/{member_id}/invite-permission</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `member_id` | path | ✓ | `string` | `{}` |
| `allowed` | body | — | `boolean` | `{"default": false}` |

```json

{
  "allowed": false
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/members/{member_id}/remove</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `member_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `name` | body | — | `string` | `{"maxLength": 160, "default": ""}` |
| `code` | body | — | `string` | `{"maxLength": 128, "default": ""}` |

```json

{
  "name": "New work group"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/groups/{workspace_id}/pin</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/pin/rotate</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/groups/{workspace_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/join-by-pin</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `pin` | body | ✓ | `string` | `{"maxLength": 16, "minLength": 9}` |

```json

{
  "pin": "example-pin"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/chat/append</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `response_language` | body | — | `string / null` | `{}` |
| `role` | body | — | `string` | `{"enum": ["user", "ai"], "default": "user"}` |
| `kind` | body | — | `string` | `{"default": "text"}` |
| `text` | body | ✓ | `string` | `{"maxLength": 4000, "minLength": 1}` |
| `evidence_url` | body | — | `string / null` | `{}` |
| `gallery` | body | — | `array` | `{}` |
| `simulated` | body | — | `boolean` | `{"default": false}` |
| `quick_replies` | body | — | `array` | `{}` |
| `face_action` | body | — | `boolean` | `{"default": false}` |

```json

{
  "text": "Where were the documents last seen?"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/chat/history</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `limit` | query | — | `integer` | `{"default": 10}` |
| `before_id` | query | — | `integer / null` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/chat/audio</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `message_id` | body | ✓ | `integer` | `{}` |
| `duration_ms` | body | — | `integer` | `{"default": 0}` |
| `audio` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/chat/audio/{audio_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `audio_id` | path | ✓ | `integer` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/notes/merge</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `texts` | body | ✓ | `array` | `{}` |

```json

{
  "texts": [
    "example-texts"
  ]
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/invite</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/join</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `name` | body | — | `string` | `{"maxLength": 160, "default": ""}` |
| `code` | body | — | `string` | `{"maxLength": 128, "default": ""}` |

```json

{
  "code": "{{invite_code}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery/{post_id}/remove</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/assistant</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `language` | body | — | `string / null` | `{}` |
| `text` | body | ✓ | `string` | `{"maxLength": 500, "minLength": 2}` |
| `audience` | body | — | `string` | `{"enum": ["home", "public", "work"], "default": "home"}` |
| `workspace_id` | body | — | `string / null` | `{}` |
| `post_id` | body | — | `string / null` | `{}` |

```json

{
  "language": "{{language}}",
  "text": "Where were the documents last seen?"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery/{post_id}/share</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |
| `audience` | body | ✓ | `string` | `{"enum": ["home", "public", "work"]}` |
| `workspace_id` | body | — | `string / null` | `{}` |

```json

{
  "audience": "work",
  "workspace_id": "{{workspace_id}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/groups/{workspace_id}/reports</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/hide/{post_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `post_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/facebook-profile</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>GET /v1/me/profile</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>PATCH /v1/me/profile</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `display_name` | body | — | `string / null` | `{}` |
| `birthday` | body | — | `string / null` | `{}` |
| `gender` | body | — | `string / null` | `{}` |
| `hometown` | body | — | `string / null` | `{}` |
| `location` | body | — | `string / null` | `{}` |
| `headline` | body | — | `string` | `{"maxLength": 240, "default": ""}` |
| `biography` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `phone` | body | — | `string` | `{"maxLength": 64, "default": ""}` |
| `website` | body | — | `string` | `{"maxLength": 1024, "default": ""}` |
| `social_links` | body | — | `array` | `{}` |

```json

{
  "display_name": "{{display_name}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/profiles/{user_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `user_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/profiles/{user_id}/avatar</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `user_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/profile/cv</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>DELETE /v1/me/profile/cv</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/notes/transcribe</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `audio` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/profile/publications</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |
| `caption` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_text` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_source` | body | — | `string` | `{"default": ""}` |
| `workspace_id` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/work-publications</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `caption` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_text` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_source` | body | — | `string` | `{"default": ""}` |
| `file` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/profile/cv/retry</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/profiles/search</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `language` | body | — | `string / null` | `{}` |
| `question` | body | ✓ | `string` | `{"maxLength": 500, "minLength": 2}` |
| `user_id` | body | — | `string / null` | `{}` |

```json

{
  "language": "{{language}}",
  "question": "{{query}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery/page</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `audience` | query | — | `string` | `{"enum": ["home", "work"], "default": "work"}` |
| `workspace_id` | query | — | `string / null` | `{}` |
| `limit` | query | — | `integer` | `{"default": 12}` |
| `cursor` | query | — | `string / null` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `audience` | query | — | `string` | `{"enum": ["home", "public", "work"], "default": "work"}` |
| `offset` | query | — | `integer` | `{"default": 0}` |
| `workspace_id` | query | — | `string / null` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `media_id` | body | ✓ | `string` | `{}` |
| `audience` | body | — | `string` | `{"default": "work"}` |
| `caption` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `workspace_id` | body | — | `string / null` | `{}` |

```json

{
  "media_id": "{{media_id}}",
  "audience": "work",
  "workspace_id": "{{workspace_id}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/capture-profile</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>GET /v1/gallery/{post_id}/thumbnail</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery/{post_id}/boxed</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |
| `labels` | query | — | `string` | `{"default": ""}` |
| `full_size` | query | — | `boolean` | `{"default": false}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery/{post_id}/interactions</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |
| `action` | body | ✓ | `string` | `{"enum": ["like", "unlike", "comment", "report"]}` |
| `text` | body | — | `string` | `{"maxLength": 2000, "default": ""}` |
| `parent_id` | body | — | `string / null` | `{}` |

```json

{
  "action": "like"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery/{post_id}/comments</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/preferences</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>PATCH /v1/me/preferences</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `initialize` | query | — | `boolean` | `{"default": false}` |
| `preferred_language` | body | ✓ | `string` | `{"enum": ["en", "es"]}` |

```json

{
  "preferred_language": "en"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/chat/history/prepare</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `message_ids` | body | ✓ | `array` | `{}` |

```json

{
  "message_ids": [
    1
  ]
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/chat/history/translations</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `ids` | query | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery/evidence/information</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `language` | body | — | `string` | `{"maxLength": 16, "default": "en"}` |
| `items` | body | ✓ | `array` | `{}` |

```json

{
  "language": "{{language}}",
  "items": [
    {
      "evidence_id": "{{evidence_id}}",
      "labels": [
        "example-labels"
      ]
    }
  ]
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/gallery/evidence/information/prepare</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `language` | body | — | `string` | `{"maxLength": 16, "default": "en"}` |
| `items` | body | ✓ | `array` | `{}` |

```json

{
  "language": "{{language}}",
  "items": [
    {
      "evidence_id": "{{evidence_id}}",
      "labels": [
        "example-labels"
      ]
    }
  ]
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/gallery/evidence/{evidence_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `evidence_id` | path | ✓ | `string` | `{}` |
| `labels` | query | — | `string` | `{"default": ""}` |
| `full_size` | query | — | `boolean` | `{"default": false}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/publication-uploads</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `file` | body | ✓ | `string` | `{}` |
| `request_key` | body | ✓ | `string` | `{"maxLength": 64}` |
| `audience` | body | — | `string` | `{"default": "work"}` |
| `workspace_id` | body | — | `string / null` | `{}` |
| `caption` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_text` | body | — | `string` | `{"maxLength": 4000, "default": ""}` |
| `note_source` | body | — | `string` | `{"default": ""}` |

Respuestas declaradas: `202`, `422`.

</details>

<details>

<summary>GET /v1/me/publication-uploads/{upload_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `upload_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/me/publication-uploads/{upload_id}/preview</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `upload_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/publication-uploads/{upload_id}/confirm</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `upload_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/publication-uploads/{upload_id}/cancel</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `upload_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/me/publication-uploads/{upload_id}/retry</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `upload_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/groups/{workspace_id}/publications/import</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | path | ✓ | `string` | `{}` |
| `publication_ids` | body | ✓ | `array` | `{}` |

```json

{
  "publication_ids": [
    "{{post_id}}"
  ]
}

```

Respuestas declaradas: `200`, `422`.

</details>

## Dispositivos y Display

| Operación | Identificador descriptivo | Acceso | Campos obligatorios | Manual |
| --- | --- | --- | --- | --- |
| `POST /v1/virtual-devices/bootstrap` | Preparar dispositivo virtual | none | `X-RealityOS-Installation-ID` | ✓ |
| `GET /v1/device/zones` | Listar zonas del dispositivo | device | — | — |
| `POST /v1/device/sessions` | Abrir sesión del dispositivo | device | — | ✓ |
| `POST /v1/device/sessions/{session_id}/close` | Cerrar sesión del dispositivo | device | `session_id` | ✓ |
| `POST /v1/device/captures` | Subir captura del dispositivo | device | `session_id`, `file` | ✓ |
| `POST /v1/device/captures/{capture_id}/process` | Procesar captura del dispositivo | device | `capture_id` | ✓ |
| `GET /v1/device/jobs/{job_id}` | Consultar trabajo del dispositivo | device | `job_id` | — |
| `POST /v1/device/queries` | Consultar desde dispositivo | device | `workspace_id`, `question` | — |
| `GET /v1/device/observations/{observation_id}/highlighted` | Ver evidencia del dispositivo | device | `observation_id` | — |
| `GET /v1/device/display/observations/{observation_id}/highlighted` | Ver evidencia mediante enlace Display | signed | `observation_id`, `token` | — |
| `POST /v1/display/media-links` | Crear enlace temporal de medio | bearer | `kind`, `resource_id` | ✓ |
| `GET /v1/display/media` | Abrir medio de Display | signed | `token` | — |
| `POST /v1/display/face-group-links` | Crear enlace temporal de rostros | bearer | `marks`, `probe` | ✓ |
| `GET /v1/display/face-group` | Ver imagen de rostros numerados | signed | `token` | — |

<details>

<summary>POST /v1/virtual-devices/bootstrap</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `X-RealityOS-Installation-ID` | header | ✓ | `string` | `{}` |

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>GET /v1/device/zones</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/device/sessions</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `zone_id` | body | — | `string / null` | `{}` |

```json

{}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>POST /v1/device/sessions/{session_id}/close</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `session_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/device/captures</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `session_id` | body | ✓ | `string` | `{}` |
| `captured_at` | body | — | `string / null` | `{}` |
| `file` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>POST /v1/device/captures/{capture_id}/process</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `capture_id` | path | ✓ | `string` | `{}` |

```json

{}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/device/jobs/{job_id}</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `job_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/device/queries</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `question` | body | ✓ | `string` | `{"maxLength": 500, "minLength": 2}` |
| `language` | body | — | `string` | `{"maxLength": 16, "default": "en"}` |
| `search_scope` | body | — | `string` | `{"enum": ["auto", "gallery", "registry"], "default": "auto"}` |

```json

{
  "workspace_id": "{{workspace_id}}",
  "question": "{{query}}",
  "language": "{{language}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/device/observations/{observation_id}/highlighted</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `observation_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/device/display/observations/{observation_id}/highlighted</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `observation_id` | path | ✓ | `string` | `{}` |
| `token` | query | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/display/media-links</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `kind` | body | ✓ | `string` | `{"enum": ["evidence", "upload", "publication", "face_enrollment", "face_record_enrollment", "avatar"]}` |
| `resource_id` | body | ✓ | `string` | `{}` |
| `labels` | body | — | `array` | `{}` |

```json

{
  "kind": "evidence",
  "resource_id": "{{resource_id}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/display/media</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `token` | query | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/display/face-group-links</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `marks` | body | ✓ | `string` | `{}` |
| `probe` | body | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/display/face-group</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `token` | query | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

## Administración

| Operación | Identificador descriptivo | Acceso | Campos obligatorios | Manual |
| --- | --- | --- | --- | --- |
| `GET /v1/admin/devices` | Listar dispositivos | bearer | `workspace_id` | — |
| `POST /v1/admin/devices` | Enrolar dispositivo | bearer | `workspace_id`, `device_identifier`, `label` | ✓ |
| `POST /v1/admin/devices/{device_id}/rotate` | Renovar clave del dispositivo | bearer | `device_id` | ✓ |
| `POST /v1/admin/devices/{device_id}/revoke` | Revocar dispositivo | bearer | `device_id` | ✓ |
| `GET /v1/admin/devices/{device_id}/assignments` | Consultar asignaciones del dispositivo | bearer | `device_id` | — |
| `POST /v1/admin/devices/{device_id}/assignments` | Asignar dispositivo | bearer | `device_id`, `operator_label`, `notice_version` | ✓ |
| `GET /v1/admin/analytics/inventory` | Consultar analítica del inventario | bearer | `workspace_id` | — |
| `GET /v1/moderation/reports` | Consultar reportes de moderación | bearer | — | — |
| `POST /v1/moderation/{post_id}/hide` | Ocultar publicación por moderación | bearer | `post_id` | ✓ |

<details>

<summary>GET /v1/admin/devices</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | query | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/admin/devices</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | body | ✓ | `string` | `{}` |
| `device_identifier` | body | ✓ | `string` | `{"maxLength": 96, "minLength": 3, "pattern": "^[A-Za-z0-9._:-]+$"}` |
| `label` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 2}` |
| `metadata` | body | — | `object` | `{}` |

```json

{
  "workspace_id": "{{workspace_id}}",
  "device_identifier": "example-device_identifier",
  "label": "example-label"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>POST /v1/admin/devices/{device_id}/rotate</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `device_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/admin/devices/{device_id}/revoke</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `device_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/admin/devices/{device_id}/assignments</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `device_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>POST /v1/admin/devices/{device_id}/assignments</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `device_id` | path | ✓ | `string` | `{}` |
| `operator_label` | body | ✓ | `string` | `{"maxLength": 160, "minLength": 1}` |
| `external_reference` | body | — | `string / null` | `{}` |
| `notice_version` | body | ✓ | `string` | `{"maxLength": 80, "minLength": 1}` |

```json

{
  "operator_label": "example-operator_label",
  "notice_version": "example-notice_version"
}

```

Respuestas declaradas: `201`, `422`.

</details>

<details>

<summary>GET /v1/admin/analytics/inventory</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `workspace_id` | query | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/moderation/reports</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>POST /v1/moderation/{post_id}/hide</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `post_id` | path | ✓ | `string` | `{}` |

Respuestas declaradas: `200`, `422`.

</details>

## Salud

| Operación | Identificador descriptivo | Acceso | Campos obligatorios | Manual |
| --- | --- | --- | --- | --- |
| `GET /health/live` | Comprobar proceso activo | none | — | — |
| `GET /health/ready` | Comprobar disponibilidad | none | — | — |

<details>

<summary>GET /health/live</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

<details>

<summary>GET /health/ready</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>

## Solo instalación local

| Operación | Identificador descriptivo | Acceso | Campos obligatorios | Manual |
| --- | --- | --- | --- | --- |
| `POST /v1/auth/local-login` | Acceder a instalación local | none | `email`, `password` | — |
| `GET /v1/auth/local-session` | Comprobar entorno local | bearer | — | — |

<details>

<summary>POST /v1/auth/local-login</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| `email` | body | ✓ | `string` | `{"maxLength": 320, "minLength": 3}` |
| `password` | body | ✓ | `string` | `{"maxLength": 512, "minLength": 1}` |

```json

{
  "email": "{{email}}",
  "password": "{{password}}"
}

```

Respuestas declaradas: `200`, `422`.

</details>

<details>

<summary>GET /v1/auth/local-session</summary>

| Campo | Ubicación | Obligatorio | Tipo | Restricciones |
| --- | --- | --- | --- | --- |
| — | — | — | — | — |

Respuestas declaradas: `200`.

</details>


