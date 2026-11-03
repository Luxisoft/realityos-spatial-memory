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
El nombre visible del remitente es siempre `RealityOS`; de `SMTP_FROM` se toma
solo la dirección del buzón. Un nombre heredado de otra aplicación no cambia
la identidad de los correos de confirmación o recuperación.

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
del creador o desactivar su cuenta también bloquea esa credencial. La revocación
se vuelve a comprobar antes de escribir, incluso si una descarga estaba en curso.

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
requiere otro identificador externo; nunca se sobrescribe silenciosamente el original
ni se cambia su autor mediante un reintento. Se comprueba el formato real de las imágenes.
`POST /v1/integrations/records/{id}/index` permite reintentar indexación.

Para sincronización de entrada HTTP, la conexión puede incluir `source_url` y
`source_token`. El origen debe servir el mismo JSON de lote. El servidor autoriza
sus dominios mediante `INTEGRATION_SOURCE_HOSTS`; solo HTTPS/443, sin redirecciones
ni direcciones privadas. La descarga fija la IP pública validada y conserva la
verificación TLS del dominio para evitar cambios de DNS entre validación y conexión.
`INTEGRATION_ENCRYPTION_KEY` cifra las credenciales guardadas.
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
La búsqueda filtra y ordena en SQL por título, identificador, datos y notas locales
antes de limitar resultados; un registro antiguo no queda excluido por tener 500
registros más recientes. Selecciona hasta cuatro coincidencias principales y sus
relaciones activas de la misma fuente, con un máximo de ocho registros y veinte
notas por registro. `context_truncated` indica resultados o contexto recortados,
y la respuesta de IA debe señalar que la información recuperada es parcial.
Web y Android permiten paginar los listados de 50 en 50 mediante `offset`.
No hay búsqueda global de Facebook.
La consulta del propio perfil/CV se conserva separada.

`POST .../records/{id}/publications` relaciona una publicación existente del mismo
espacio mediante `publication_id`. `POST .../records/{id}/notes` agrega una nota
con `text` y `occurred_at`; no modifica datos importados. Las revisiones son de
lectura administrativa y las notas son anexos, no reemplazos del historial externo.

Cada prescripción, alergia o administración activa importada debe relacionarse
con exactamente una persona activa de la misma fuente. Esta condición se comprueba
sobre el estado final completo de la fuente, incluyendo registros que no vienen
en el lote. Para retirar una persona, hay que retirar o reasignar en el mismo lote
sus registros clínicos activos; si no, toda la importación devuelve 422 sin cambios.
La comparación clínica recibe prescripción, ingrediente y concentración observados,
confirmación profesional de identidad y fecha. Compara campos exactos, vigencia,
alergias y antecedentes de administración. No convierte unidades ni calcula dosis,
no prescribe y no registra administraciones automáticamente. Los campos observados
no admiten texto vacío o espacios; los campos importados vacíos o que no sean texto
se informan como datos insuficientes. Una alergia registrada sin sustancia válida
también se informa como evidencia incompleta, conservando su referencia. Editar el formulario invalida la comparación
anterior y los campos quedan bloqueados mientras llega la respuesta. Los formularios no
sustituyen una verificación clínica. La extracción automática del envase completo
no forma parte de este comparador de campos.

El brazo biométrico conserva su aislamiento y ahora enlaza expedientes
autorizados: los registros `person` importados no son usuarios ni se enrolan
automáticamente. La importación puede marcar `biometric_authorized` con
`biometric_basis` trazable; el enrolamiento es un paso explícito posterior por
retrato (`POST /v1/faces/record-enroll`, una sola cara, ADMIN/REGISTER) y la
búsqueda `POST /v1/faces/search` devuelve `matches_records` del mismo espacio
(solo `active` + `person` + autorización vigente) como candidatas que el
profesional debe confirmar. Bajas y revocaciones excluyen sin borrar notas.

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

El panel y la web Display están retirados. Los formularios de cuentas y expedientes
se utilizan desde Android; las verificaciones web históricas no describen una app vigente.

## Alcance de la revisión del 2 de noviembre de 2026

La regresión cubre registro y recuperación de cuenta, renovación de sesión Android,
autorización por espacio, claves revocadas, importación atómica, medios, notas,
relaciones, búsqueda de registros antiguos y límites del contexto de IA. Las pruebas
de correo verifican enlaces, tokens, TLS y recuperación ante fallos usando transporte
controlado; no equivalen a recepción de un correo real.

La prueba de navegador usa 51 registros sintéticos para comprobar paginación,
permisos del editor de notas y que una foto recibida tarde no aparezca en el perfil
de otro paciente, ni que guardar una nota anterior borre el borrador de otro
expediente. También comprueba la vista móvil de 390 píxeles. El conjunto
instalado conserva 47 registros; los 51 de esa prueba no se cargan en producción.

Pendientes de validación externa: recepción de confirmación y recuperación en un
correo autorizado, conexión a una fuente institucional que implemente el contrato
y pruebas físicas con teléfono y Ray-Ban. La importación HTTP del conjunto del jurado
sí se ejecutó contra la API real. La lectura automática de envases no está
implementada. El enlace de personas al reconocimiento facial se implementó en
`20261103_0032` con autorización explícita y enrolamiento por retrato; falta
enrolar los retratos del jurado por API y verificar la búsqueda viva.

| Parte del plan | Verificación y límite |
| --- | --- |
| Perfil global, correo visible, detalles plegables y gafas bajo Facebook | Componente compartido conservado; pruebas Compose del encabezado incluidas en la suite Android. Falta QA física. |
| Referencias Facebook internas y publicaciones de trabajo | Suite de permisos y visibilidad aprobada; motor biométrico sin cambios. |
| Registro, acceso, confirmación y recuperación | Pruebas de API, transporte SMTP y renovación de sesión aprobadas; recepción real aún pendiente. |
| Jurado y limpieza anterior | Tres grupos ficticios con tres trabajadores cada uno; nueve avatares distintos, 47 registros, 27 adjuntos y 21 publicaciones indexadas. |
| API y aislamiento | Importación real por HTTP; pruebas de revisiones, reintentos, revocación, archivos, paginación y accesos entre grupos. |
| Historial de personas y casos | Registros relacionados y notas disponibles en los expedientes y en la búsqueda contextual; respuestas con Meta real verificadas. |
| Medicación | Comparación manual de campos y validación de relaciones/fechas; sin OCR de envases ni autorización automática. |
| Memoria | Búsqueda de observaciones autorizadas y referencia a última ubicación observada; dataset sintético, sin prueba de captura física continua. |


La tercera revisión añadió regresiones de baja de personas con historial clínico
activo y comparación de campos mal tipados. En Android se verificó volver atrás
durante la carga o el guardado de un expediente: las respuestas obsoletas no
reabren el paciente anterior ni modifican el borrador del siguiente. Salir de la
pantalla no revierte una nota que el servidor ya haya recibido. Estas pruebas
usan respuestas controladas y no sustituyen QA física de captura con las gafas.


Las solicitudes de registro, reenvío y recuperación aceptan `Accept-Language`
ES/EN; el respaldo es la preferencia de cuenta y después español. Los correos
son multipart HTML/texto y conservan enlaces de un uso con token en fragmento.
Las páginas mínimas `/v1/auth/verify` y `/v1/auth/reset` permanecen con el mismo
tema Android; `?lang=es|en` selecciona su idioma. Sin cambio del cuerpo REST.
