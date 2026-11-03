> Historical source / Fuente histórica — preserved 2026-11-03. [Current guide](../ARCHITECTURE.md) · [Guía actual](../ARCHITECTURE.es.md). Earlier deployment instructions may be retired.

# Architecture

RealityOS is a modular monorepo: FastAPI owns authorization and business rules;
Celery runs long-running processing against the same SQLAlchemy domain model;
React clients consume only the REST contract.

    Register client -> API -> PostgreSQL BYTEA -> Redis/Celery -> Meta provider
    Query client    -> API -> verified observation + authorized media URL

The query path does not create capture-domain resources. Audit and eventual
query analytics are isolated from observations so they cannot become evidence.

The current API uses synchronous SQLAlchemy inside async endpoints to avoid a
runtime thread-pool limitation in the supported Python 3.13 environment.
Production scaling should move to an async driver or process replicas before
high concurrency.


## Reorganización modular (2026-10-30)

La primera etapa separa el backend conservando las interfaces existentes:

- `app.http`: adaptadores de identidad/dispositivos, capturas, objetos,
  consultas y medios. `app.routes` conserva el ensamblaje y la precedencia
  original de rutas.
- `app.providers`: contratos Meta compartidos, cliente Live y cliente Mock.
  `app.meta` conserva sus exportaciones y la fábrica de clientes.
- `app.processing`: operaciones de procesamiento, búsqueda y almacenamiento
  BYTEA. `app.services` conserva las importaciones utilizadas por worker,
  scripts y pruebas.
- `app.social_features`: modelos, contratos, grupos, perfiles, galería, chat,
  asistente e importación Facebook. `app.social` conserva las exportaciones
  utilizadas por migraciones históricas y el módulo biométrico.
- `tests/social`: regresiones separadas por funcionalidad. La instantánea
  generada `tests/contracts/openapi.json` comprueba que la reorganización no
  cambia el contrato público, incluidos identificadores de operación.

Los modelos tienen una única definición. Los puntos de compatibilidad no
registran tablas adicionales. Las dependencias entre operaciones sociales que
se invocan mutuamente se resuelven dentro de esas operaciones; modelos y
contratos se importan normalmente al cargar los módulos.

`make architecture-check` limita a 999 líneas físicas los archivos Python de
backend, gateway y pruebas, y el código TypeScript/CSS de las aplicaciones web. Las excepciones explícitas son `app/faces.py` y
`tests/test_faces.py`, protegidos por decisión del propietario. El código
biométrico y sus pruebas no se reorganizan.

El panel web separa autenticación, inicio, capturas y consultas bajo `features/`.
Ambas aplicaciones web usan Prettier y CI comprueba su formato. El control
de tamaño también cubre TypeScript y CSS. Android separa navegación, barras
y drawer en `host`, y las operaciones de dispositivos, captura, consultas y
procesamiento en `host/operations`. El ViewModel conserva su API callable
y coordina estado y recursos compartidos; sus operaciones son extensiones
internas con receptor explícito. El estado mutable permanece dentro del
módulo Android; las interfaces observables públicas no cambian.

El chat separa modelos/decodificación e historial de la presentación en
`chat/ChatScreen`. La pantalla recibe estado y callbacks; la coordinación y
el ciclo de vida de audio permanecen en el host Compose para preservar
su comportamiento. `chat/ChatAudioPlayback` posee los reproductores y su estado observable;
el host conserva la grabación y libera los recursos al salir de composición. Ktlint
comprueba los archivos reorganizados y sus nuevas pruebas, excluyendo la
UI biométrica. El control de tamaño incluye Kotlin, scripts y pruebas. No se modificaron
esquemas, tareas Celery ni el comportamiento del gateway.

La validación inicial encontró esperas del pool de AnyIO en el sandbox.
La separación de pruebas también expuso contactos al Redis real desde el
indexador de galería. El fixture de API ahora aísla exclusivamente el envío
Celery de ese indexador; sus pruebas ejecutan la indexación directamente.
El cliente ASGI original y los endpoints biométricos se conservan. La suite
completa pasó con este aislamiento, sin depender de un broker externo.


### Despliegue de esta etapa

API y worker usan `realityos-backend:architecture-20261030`, con los overlays
anteriores de entorno y gateway conservados. `/health/ready` devuelve `ready`,
OpenAPI coincide con la instantánea anterior y Alembic está en
`20261030_0025 (head)`. No se añadió ninguna migración ni dump de base de datos.

Overlay de imagen: `.runtime/architecture-20261030-release.json`.
Rollback: `.runtime/architecture-20261030-rollback.json` (imagen anterior
`realityos-backend:tts-natural-20261030`). Para revertir, usar la misma cadena
de archivos Compose del despliegue sustituyendo el último overlay de release
por el de rollback y recrear únicamente `api worker` con `--no-deps --no-build`.
Los cambios web se entregan mediante CI; no se recrearon sus contenedores.


### Desarrollo y verificación

- `make architecture-check`: máximo 999 líneas físicas por archivo propio
  de backend, gateway, Android, web, scripts y pruebas; excluye dependencias,
  artefactos y las dos excepciones biométricas nombradas anteriormente.
- `make format-check`: Ruff en los módulos Python reorganizados, Prettier en
  ambos clientes web y ktlint en los archivos Kotlin reorganizados.
- `make android-check`: formato, pruebas unitarias, lint y APK Debug/Release.
  Requiere SDK Android configurado. La validación física de cámara, gafas y
  audio es independiente de estas comprobaciones automatizadas.

Los namespaces Android existentes conservan compatibilidad con la aplicación;
los módulos nuevos usan subpaquetes `host`, `host.operations` y `chat`. No se
actualizaron versiones de SDK ni contratos Meta. Las dependencias nuevas de
Prettier y ktlint solo se usan para desarrollo y CI.

### Carga de contenido en Android

`LoadingSkeleton.kt` reúne placeholders de perfil, listas, cuadrículas y texto.
`DatabaseImage` mantiene un placeholder hasta que Coil carga el medio y muestra
un estado de error si falla. Perfil, galería, historial de chat, espacios,
invitaciones, comentarios y administración usan estados de carga independientes;
los datos vacíos solo se anuncian al terminar la consulta. La paginación conserva
el contenido recibido y agrega placeholders al final. Las acciones de escritura
y grabación conservan sus indicadores de progreso. La UI biométrica protegida
permanece fuera de este cambio.


### Resultado final verificado

- 119 pruebas Python aprobadas; Ruff y contrato OpenAPI aprobados.
- 62 pruebas unitarias Android aprobadas; ktlint, lint, APK Debug y Release
  aprobados; fuentes de pruebas instrumentadas compiladas. No se ejecutó
  validación en dispositivo físico ni emulador durante esta reorganización.
- Release no contiene referencias al Mock Device Kit.
- Ambas aplicaciones web compilan y pasan Prettier; su publicación sigue CI.
- Todos los archivos propios cubiertos por `make architecture-check` tienen
  menos de 1.000 líneas, excepto los dos archivos biométricos protegidos.
- Se retiraron el contenedor y la imagen temporal de pruebas; se conservan
  únicamente la nueva imagen backend y la anterior necesaria para rollback.


### Visor señalizado a resolución original — 2026-10-30

El endpoint de galería `boxed` admite `full_size=true`: conserva las dimensiones
originales, aplica los mismos filtros de etiquetas y controles de acceso, y no
modifica el BYTEA. Android usa esa variante al abrir una miniatura señalizada,
incluido el historial de chat ya guardado. La miniatura sigue siendo pequeña.

API y worker usan `realityos-backend:boxed-full-20261030`, conservando el runtime
anterior del gateway. Se verificaron `/health/ready`, igualdad del contrato
OpenAPI y Alembic `20261030_0025 (head)`, sin cambios de esquema ni dumps.
Una petición autenticada productiva devolvió 1920 × 1280 para el visor y
360 × 240 para la miniatura del mismo original. Pasaron 22 pruebas backend y
69 pruebas Android, formato, lint y APK Debug; queda pendiente QA en teléfono.
Release: `.runtime/boxed-full-20261030-release.json`.
Rollback: `.runtime/boxed-full-20261030-rollback.json` (imagen anterior
`realityos-backend:architecture-20261030`). La cadena de Compose está registrada
en `.runtime/boxed-full-20261030-deploy.json`: sustituir su último overlay de
release por rollback y recrear `api worker` con `--no-deps --no-build`.
No quedaron contenedores temporales de este despliegue.


### Búsqueda visual y revisión de publicaciones — 2026-10-30

`social_features.visual` normaliza orientación, filtra geometría y combina Muse
con localización SAM en una llamada por imagen con múltiples objetos. El índice
serial de galería guarda evidencia inmutable en BYTEA con PTS real para video;
la consulta solo selecciona evidencia ya procesada y autorizada. No inicia
captura ni segmentación. `Publication.evidence_version` pertenece a cada
publicación, incluso cuando varias comparten el mismo medio original.

`uploads` y `upload_service` mantienen subidas privadas hasta la revisión Meta,
con claves idempotentes y bloqueo por dueño/destino. Un duplicado requiere
confirmación para reemplazar el medio; conserva identidad, permisos y actividad.
El mantenimiento retira copias redundantes mediante aliases y un mapa reversible,
sin eliminar originales. Reanudarlo con `scripts/rebuild_search_evidence.py --apply`.

Android conserva el conjunto y la selección del carrusel en `UnifiedSearch`;
`SearchEvidenceCarousel` coordina páginas, miniaturas, zoom y reproducción desde
PTS menos tres segundos. `PublicationUploader` gestiona estados y confirmación.
El proveedor Live usa las rutas existentes del gateway, sin cambios de allowlist.
API/worker: `realityos-backend:search-evidence-20261030`; Alembic `20261030_0026`.
Release/rollback: `.runtime/search-evidence-20261030-{release,rollback}.json`.
El rollback omite el arranque Alembic de la imagen anterior, que desconoce la
revisión nueva, y conserva las tablas aditivas. Tras recrear API, recargar Nginx
Compose para resolver su dirección nueva antes de comprobar la salud pública.
Se verificaron salud, contrato OpenAPI y hashes de todo el entorno API/worker.
