# Cuentas e integración de espacios de trabajo

La API, almacenamiento BYTEA, indexación y proveedores son reales. El conjunto
`simulator/workspaces/` contiene exclusivamente material ficticio. No debe
utilizarse para decisiones clínicas ni como registros de personas reales.

## Cuentas

`POST /v1/auth/register` recibe `username`, `email`, `display_name` y `password`
(mínimo 12 caracteres). El correo se confirma antes del primer acceso.
`/auth/login` conserva el campo `email` por compatibilidad; admite correo o usuario.
`/auth/resend-confirmation`, `/auth/forgot-password`, `/auth/confirm-email` y
`/auth/reset-password` completan la recuperación. Los enlaces vencen en 30 minutos,
son de un solo uso y el cambio de contraseña revoca sesiones anteriores.

SMTP requiere `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`,
`SMTP_FROM` y `AUTH_PUBLIC_URL` privados. Se exige TLS; puerto 465 usa TLS directo,
los demás STARTTLS. Nunca incluir estas variables en aplicaciones cliente o Git.

Las cuentas del jurado son provisionadas por administración: pueden entrar por
usuario y contraseña, pero sus direcciones ficticias no se marcan verificadas.
La provisión HTTP está deshabilitada salvo `TEST_WORKER_PROVISIONING_ENABLED=true`.
No cambia la excepción del Debug local de Windows ni los permisos biométricos.

## Contrato REST

Un administrador crea una conexión con
`POST /v1/workspaces/{workspace_id}/connections`, cuerpo `{"name":"Origen"}`.
La respuesta muestra `integration_key` una sola vez. Enviar esa credencial como
`X-RealityOS-Integration-Key` en las rutas de integración. No es un token de usuario.
Revocar la conexión impide nuevas importaciones. Perder la pertenencia administrativa
del creador también bloquea esa credencial.

`POST /v1/integrations/imports` acepta un lote atómico de hasta 100 registros y
2 MiB. Ejemplo mínimo:

```json
{
  "request_key": "source-batch-001",
  "records": [{
    "external_id": "patient-001",
    "kind": "person",
    "title": "Persona autorizada",
    "version": 1,
    "status": "active",
    "authorized": true,
    "occurred_at": "2026-11-02T09:00:00-05:00",
    "data": {"identifier": "P001"},
    "related_ids": [],
    "simulated": false
  }]
}
```

Tipos: `person`, `case`, `encounter`, `event`, `object`, `prescription`, `allergy`,
`administration`. Las relaciones usan identificadores externos de la misma fuente;
pueden referir registros del mismo lote. Las versiones deben aumentar. Repetir
exactamente un lote con la misma clave devuelve el resultado original. Cambiar su
contenido con la misma clave devuelve 409. Un error invalida el lote completo;
la respuesta identifica el registro que debe corregirse. Estados `draft` y `deleted`
no aparecen en consultas de registros; una baja oculta publicaciones asociadas.
Las notas locales y revisiones se conservan.

Consultar un lote: `GET /v1/integrations/imports/{id}`.
Adjuntar originales: `POST /v1/integrations/records/{record_id}/media`, multipart
`external_id`, `publish`, `author_id` opcional y `file`. Acepta JPEG, PNG, WebP y MP4,
hasta 64 MiB; MP4 hasta 120 segundos o el límite menor del servidor. Con `publish=true`
crea una publicación de trabajo y solicita indexación al worker existente.
El autor debe ser miembro activo del mismo espacio. Una nueva revisión de archivo
requiere otro identificador externo; nunca se sobrescribe silenciosamente el original.
`POST /v1/integrations/records/{id}/index` permite reintentar indexación.

Para sincronización de entrada HTTP, la conexión puede incluir `source_url` y
`source_token`. El origen debe servir el mismo JSON de lote. El servidor autoriza
sus dominios mediante `INTEGRATION_SOURCE_HOSTS`; solo HTTPS/443, sin redirecciones
ni direcciones privadas. `INTEGRATION_ENCRYPTION_KEY` cifra las credenciales guardadas.
`POST /v1/workspaces/{id}/connections/{connection_id}/sync` realiza una sincronización
explícita. Los archivos se cargan mediante multipart, no se descargan URLs arbitrarias.
No se afirma compatibilidad universal con cualquier EHR ni conformidad FHIR.

## Consultas y trazabilidad

Las rutas `/v1/workspaces/{id}/records` permiten listar, consultar detalle y añadir
notas. Cada respuesta incluye fuente, identificador externo, versión y fechas.
Los adjuntos incluyen tipo MIME y tamaño; web y Android abren fotos y videos
con autenticación. La lectura de originales admite rangos HTTP y medios por chunks.
`POST .../records/search` recibe `question`, `language` y `record_id` opcional;
recupera únicamente registros activos del espacio autorizado antes de consultar IA.
La búsqueda actual selecciona hasta ocho registros de los 500 más recientes;
los listados paginan de 50 en 50 mediante `offset`. No hay búsqueda global de Facebook.
La consulta del propio perfil/CV se conserva separada.

`POST .../records/{id}/publications` relaciona una publicación existente del mismo
espacio mediante `publication_id`. `POST .../records/{id}/notes` agrega una nota
con `text` y `occurred_at`; no modifica datos importados. Las revisiones son de
lectura administrativa y las notas son anexos, no reemplazos del historial externo.

La comparación clínica recibe prescripción, ingrediente y concentración observados,
confirmación profesional de identidad y fecha. Compara campos exactos, vigencia,
alergias y antecedentes de administración. No convierte unidades ni calcula dosis,
no prescribe y no registra administraciones automáticamente. Los formularios no
sustituyen una verificación clínica. La extracción automática del envase completo
no forma parte de este comparador de campos.

El módulo biométrico permanece intacto. Los registros `person` importados no son
usuarios ni se enrolan automáticamente. No se conecta este nuevo registro al
buscador facial existente ni se modifica su contrato.

## Conjunto del jurado

Los manifiestos definen 47 registros y 27 adjuntos: quince fotos de escenas de trabajo,
seis retratos ficticios y seis MP4 de cinco segundos. Los MP4 son escenas estáticas
rotuladas como simuladas, no grabaciones reales ni prueba de seguimiento temporal.
Los nueve trabajadores tienen avatares diferentes. Cada uno pertenece a un solo
espacio de trabajo, además de su espacio personal de captura.

```bash
.venv/bin/python simulator/workspaces/build_fixture.py
.venv/bin/python simulator/workspaces/load.py simulator/workspaces/hospital.json \
  --credentials .runtime/jury-hospital-integration.json
```

El cargador utiliza HTTP real; no inserta personas ni historiales directamente en SQL.
Las fotos originales generadas se guardan en `simulator/workspaces/assets/`. Los
retratos representan personas ficticias creadas para pruebas; las escenas muestran
mesa de evidencias, carro de preparación y escritorio doméstico. No contienen
logotipos institucionales ni información de pacientes reales.

## Limpieza y despliegue

`scripts/purge_workspaces.py ID ...` calcula las dependencias y revierte su transacción
por defecto. `--apply` requiere revisión del inventario y respaldo técnico reversible.
La herramienta protege las tablas de identidad y biometría y conserva medios usados
por publicaciones de espacios ajenos a la selección. No admite espacios personales.
La migración de cuentas y registros es `20261102_0031`.

La publicación web aislada usa el workflow manual `Publish workspace web`: valida y
construye el frontend en CI, publica solo su imagen y conserva el checkout y backend.
