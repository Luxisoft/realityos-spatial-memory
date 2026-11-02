# RealityOS — contexto del proyecto para agentes

> Puerta de entrada rápida. Los documentos en `docs/` son la fuente autoritativa;
> este archivo es solo un mapa + estado actual. Actualizarlo cuando cambien la
> arquitectura o el estado de despliegue.

## Qué es

RealityOS es una memoria espacial basada en evidencia: registra observaciones
visuales intencionales en un workspace y recupera la **última evidencia
verificada** de un objeto ("visto por última vez", nunca "sigue ahí").
Preparado para Meta AI Developer Hackathon 2026. Licencia Apache-2.0.

Invariantes no negociables (ver `AGENTS.md` y `docs/REALITYOS_MISSION.md`):

- PostgreSQL `BYTEA` es la fuente de verdad de cada medio original.
- Register = escritura explícita con sesión consentida; Query = solo lectura,
  nunca inicia captura ni fabrica evidencia.
- Todo recurso se filtra por pertenencia al workspace autenticado.
- `MODEL_API_KEY`, JWT y credenciales DB solo en servidor; en producción la
  clave Meta vive en archivos privados de RealityOS y del gateway de FRONTEND.
- Mock es determinista y etiquetado `simulated`; Live nunca cae a mock en
  silencio (`uncertain` ante proveedor ambiguo).

## Mapa del monorepo

| Directorio | Contenido | Stack |
| --- | --- | --- |
| `backend/app/` | API y contratos compartidos: `http`, `providers`, `processing`, `social_features`; fachadas compatibles y módulo biométrico aislado | Python, FastAPI, SQLAlchemy, Celery/Redis |
| `backend/alembic/versions/` | Migraciones históricas; head productivo verificado `20261031_0029` | Alembic, PostgreSQL |
| `meta-gateway/` | Servicio de egress restringido a Meta (no proxy general) | FastAPI, ~150 líneas |
| `frontend/src/` | Panel admin React (Home/Register/Query/Objects/Map/Intelligence/Devices) | React 18 + TS + Vite |
| `display-webapp/src/` | Demo de consulta 600×600 para Display | React + TS + Vite |
| `android/` | Host nativo DAT 1.0.1 para Ray-Ban Display + galería social (v0.1.6, code 7) | Kotlin, Compose, CameraX, DAT, Mock Device Kit (solo Debug) |
| `infrastructure/` | Compose (postgres, redis, api, worker, frontend, display, proxy Nginx) + despliegue gateway/Nginx/TLS | Docker Compose, Nginx |
| `tests/` + `gateway-tests/` | Regresiones backend/gateway, social agrupado por funcionalidad y contrato OpenAPI congelado | pytest |
| `scripts/` | `seed_demo.py`, `import_manual_photos.py`, `backup-postgres.sh`, `chunk_large_video_asset.py` | — |
| `.runtime/` | Ignorado por Git: capturas manuales privadas, dumps, release/rollback JSON | — |
| `reports/` | Imágenes de diagnóstico (sin commitear, revisar antes de tocar) | — |

Flujo de datos:

```text
Register: cliente -> API -> PostgreSQL BYTEA -> Redis/Celery -> Mock o Meta API
Query:    cliente -> API -> última observación verificada + URL de medio autorizada
Social:   app Android (login Facebook) -> API -> publicaciones/grupos sobre BYTEA existente
Live Meta: API/worker -> api.meta.ai (MODEL_API_KEY); FRONTEND gateway = fallback
Speech: API -> ElevenLabs; STT -> Meta Muse Voice Transcribe
```

## Backend: rutas principales (`backend/app/routes.py` + `social.py` + `faces.py`)

- Auth/workspaces/sesiones/capturas/jobs: `/v1/auth/*`, `/v1/workspaces`,
  `/v1/sessions`, `/v1/captures`, `/v1/jobs/{id}`.
- Objetos/evidencia: `/v1/objects` (filtros `workspace_id`, `q`, `category`,
  `zone_id`), `/history`, `/facts`, `PATCH /v1/observations/{id}`,
  `POST /v1/observations/{id}/segment` (refinamiento SAM bajo demanda, 0,0025 USD).
- Query: `POST /v1/queries`, `/v1/queries/audio` (WAV), `/v1/device/queries`;
  medios: `/v1/media/{id}`, `/v1/observations/{id}/highlighted`.
- Dispositivos (admin + ingestión): `/v1/admin/devices/*`,
  `/v1/virtual-devices/bootstrap` (solo Live), `/v1/device/*`.
- Rostros/face search (nuevo, brazo aislado protegido en `AGENTS.md`, migración
  `20261028_0009`): consentimiento versionado, enrolamiento desde medios propios
  o foto de perfil, búsqueda 1:N solo-lectura rankeada por similitud. Ver
  `backend/app/faces.py` y `tests/test_faces.py`.
- Social (nuevo, migración `20261028_0008`): login Facebook, `/v1/gallery`,
  `/v1/groups`, miembros, invitaciones de un uso, likes, comentarios con hilo,
  reportes, moderación. Modelos en `social.py`: `FacebookIdentity`,
  `Publication`, `Reaction`, `Comment`, `Report`, `GroupInvite`.
- Perfil/directorio (migración `20261028_0014`): perfil público autenticado,
  un CV privado reemplazable por usuario, preguntas IA no persistidas y amigos
  devueltos realmente por Graph; `/v1/me/profile`, `/v1/profiles/*`.
- Medios de perfil (migración `20261028_0015`): publicaciones idempotentes de
  Facebook, avatar local, paginación cursor y búsqueda IA limitada a medios
  autorizados; `/v1/profiles/{id}/media`, `/v1/gallery/page`.
- Sistema: `/health/live`, `/health/ready`.

## Dónde leer según la tarea

| Quiero… | Leo |
| --- | --- |
| Estado real verificado vs pendiente | `docs/IMPLEMENTATION_STATUS.md` (actualizar si cambia) |
| Contrato REST / esquema DB | `docs/API.md`, `docs/DATABASE.md` |
| Integración Meta (Muse/SAM/ASR) | `docs/META_INTEGRATION.md` |
| Gateway, secretos, despliegue | `docs/GATEWAY.md`, `docs/DEPLOYMENT.md` (español) |
| Android/DAT/Display | `docs/WEARABLES.md`, `android/README.md` |
| Misión, plan, checklist, demo, UI | `docs/REALITYOS_MISSION.md`, `IMPLEMENTATION_PLAN.md`, `IMPLEMENTATION_CHECKLIST.md`, `DEMO.md`, `UI_DESIGN.md` |
| Probar con fotos propias | `docs/MANUAL_PHOTO_TEST.md` (opt-in, no registra ni llama a Meta) |
| Convenciones de agente | `AGENTS.md` (raíz) |

## Estado actual (2026-10-31)

Producción verificada:

- `realityos.luxisoft.com` (HTTPS, Let's Encrypt hasta 2027-01-25) y gateway
  `meta.luxisoft.com` en FRONTEND con token independiente e IP allowlist.
- API/worker en `META_MODE=live`; `.env` elige conexión directa o gateway y respaldo.
- Migraciones aplicadas hasta `20261031_0029` (head); seed con 6 objetos y
  jerarquía `Bodega A → Estantería 3 → Nivel 2`.
- API/worker usan `realityos-backend:processing-recovery-20261031`: evidencia
  versionada, revisión de duplicados y carrusel (`20261030_0026`), además del índice IA de
  galería (`20261030_0022`, etiquetas Muse + conteo local de rostros por
  publicación), historial de chat con galería/acciones persistidas
  (`20261030_0023/0024`), cajas de detección (`20261030_0025`,
  `GET /v1/gallery/{id}/boxed`), audio de chat persistido (`20261029_0021`),
  TTS natural con plurales reales. El directorio social productivo contiene
  20 perfiles con 10 escenas Muse ancladas cada uno (200 fotos,
  0 videos sintéticos, 200 publicaciones públicas y 20 de Trabajo) con
  embeddings InsightFace reales; el grupo "Mechanic Workshop" tiene
  5 miembros en turnos día/noche con 15 tomas del mismo taller más el
  video original.
- CI publica APK Debug (`realityos-android-debug-apk`, 14 días); Release sin firma.

Trabajo en curso **sin commitear** (ver `git status`):

- Capa social + login solo-Facebook en Android: backend `social.py`, migración
  `20261028_0008`, `tests/test_social.py`, pantallas `FacebookAccessScreen`,
  `SocialGallery`, `SocialAdministration`; App ID Meta `1465393708894529`
  (credenciales en archivos ignorados modo 0600).
- Imagen local `realityos-backend:history-languages-20261030` (InsightFace buffalo_l
  horneado) activa en API/worker con overlays privados de runtime y
  `.runtime/faces-live.json` (`FACE_ENGINE=insightface`); rollback de imagen en
  `.runtime/publication-languages-20261030-rollback.json` y respaldos históricos previos en
  `.runtime/pre-*.dump`. **Un futuro despliegue CI
  debe incluir estos fuentes** (no es release de GitHub).
- Pendiente externo: login real con cuenta Facebook en handset, QA visual en
  dispositivo, hardware físico Ray-Ban Display, run Live completo de SAM Video.
- Desplegado: navegación inferior Perfil/Trabajo/Buscar, galería dentro de
  Perfil, sincronización 25 fotos + 5 videos en cuentas reales, directorio
  sintético de 20 perfiles (10 fotos Muse cada uno) por el
  importador/InsightFace real, grupo "Mechanic Workshop" con turnos y
  reproducción por rangos HTTP del video del taller.

## Comandos

```bash
make install | lint | test | api | migrate | seed | compose-up | gateway-api | runtime-dirs
npm --prefix frontend run build
npm --prefix display-webapp run build
(cd android && ANDROID_HOME=/opt/android-sdk ./gradlew :app:assembleDebug)
```

Reglas de validación: usar el `Makefile`; añadir tests con cada cambio
(permisos + aislamiento de workspace); no afirmar build Android, test en
dispositivo, request Meta live, `docker run` o PR sin haberlo ejecutado de verdad.


## Actualización de arquitectura — 2026-10-30

La descripción histórica de tamaños anterior ya no representa el backend:
las implementaciones están separadas en `app.http`, `app.providers`,
`app.processing` y `app.social_features`; los módulos anteriores conservan
interfaces de compatibilidad. Ver `docs/ARCHITECTURE.md` para el mapa vigente,
validación y estado de despliegue. Android agrupa navegación y operaciones
en `host`, y presentación de chat en `chat`, conservando las interfaces
del host. API y worker
usan `realityos-backend:history-languages-20261030`; rollback de imagen en
`.runtime/publication-languages-20261030-rollback.json`. Alembic está en `20261030_0027`.
El índice de evidencia versionada y la revisión automática de subidas ya están
activos; la reindexación serial de 238 publicaciones se ejecuta en segundo
plano (task id en `.runtime/search-evidence-20261030-task.json`). El visor de Buscar solicita
`full_size=true` en `/v1/gallery/evidence/{evidence_id}` para conservar la resolución original
con los mismos recuadros; las miniaturas mantienen el límite de 360 × 480.
Las pruebas sociales viven en
`tests/social`, y el contrato público está congelado en `tests/contracts`.


Recuperación de Buscar (2026-10-30): el buscador distingue coincidencias exactas,
de familia y similares sobre todas las detecciones autorizadas. Se materializaron
189 imágenes anteriores con cajas válidas como evidencia v1 aproximada; SAM v2
se prefiere y continúa en segundo plano, primero las fotos del taller. Query
permanece solo lectura. Las dos frases reales de búsqueda de «alicate» devuelven
3 resultados señalizados; fotos grandes verificadas a 1920 × 1280 frente a
miniaturas de 360 × 240. API/worker y salud pública verificados; runtime del
gateway preservado. Android fuerza scroll al enviar/recibir, sigue cambios de
teclado/imágenes al estar abajo y respeta la lectura manual del historial.
Validación: 156 pruebas Python/gateway, 74 Android, lint y APK Debug. QA táctil
en teléfono y finalización del reindexado siguen pendientes.


Visor del chat localizado (2026-10-30): información abierta por defecto y
plegable desde su cabecera, fecha y confianza arriba, título y notas debajo.
El panel reserva hasta el 45 % de la altura para no tapar el recurso completo.
`POST /v1/gallery/evidence/information` consulta títulos, notas y etiquetas
preparados en español e inglés. Las traducciones se persisten al publicar;
abrir el recurso no llama al modelo ni modifica originales ni cajas. El idioma procede de la selección de la app. Confianza descendente
es ahora el orden principal, también en historial y miniaturas. Comprobación
real: 97 %, 92 %, 88 %, traducción en ambos idiomas y recurso señalizado de
1920 × 1280. Pasaron 167 pruebas Python/gateway, 79 Android, lint y APK Debug.
API/worker activos con salud, OpenAPI y Alembic `20261030_0026` verificados;
rollback `.runtime/publication-languages-20261030-rollback.json`. QA táctil pendiente.


Corrección de idiomas persistidos (2026-10-30): migración `20261030_0027`, tabla
`publication_translations`. Se preparan ambos idiomas antes de completar una
publicación nueva. Los resultados e historial incluyen `localized_information`
y el visor utiliza esos textos inmediatamente. Para historial anterior, el
endpoint consulta solo la base de datos y responde `pending` si falta algún
texto. La consulta no genera traducciones ni tareas. La carga está acotada y no
sustituye silenciosamente el idioma por inglés. Script administrativo reanudable
para el contenido existente: `scripts/prepare_publication_languages.py --apply`.
Validación: 173 pruebas Python/gateway, 80 Android, lint y APK Debug. Preparados
los 1852 textos anteriores, cero pendientes de traducción y 2232 versiones por
idioma al verificar. Lecturas internas del visor: 17 ms en español y 10 ms en
inglés, también sin proveedor de traducción. SAM reanudado; task id en
`.runtime/publication-languages-20261030-task.json`. Cierre y rollback en
`.runtime/publication-languages-20261030-final.json` y
`.runtime/publication-languages-20261030-rollback.json`. QA física pendiente.


Recuperación de historial (2026-10-30): GET de historial refresca las copias de
recursos con traducciones guardadas y resuelve referencias antiguas mediante
la señalización existente. Android actualiza mensajes ya cargados sin cambiar
sus IDs locales. Si falta un idioma, llama a la acción separada
`POST /v1/gallery/evidence/information/prepare`, que guarda ambos idiomas y
responde en la misma apertura; Query y la consulta normal siguen solo lectura.
Actualizados 14 adjuntos con ambos idiomas, 13 con señalización recuperada y
uno conservado como referencia histórica sin señalización recuperable. Lecturas
internas verificadas a 12–14 ms. Pasaron 182 pruebas Python/gateway y 81 Android,
lint y APK Debug. Alembic sigue en `20261030_0027`. Rollback actual en
`.runtime/history-languages-20261030-rollback.json`; QA física pendiente.

Actualización vigente de idioma de chat (2026-10-31): API/worker usan
`realityos-backend:chat-languages-20261031`, Alembic `20261031_0028`.
`/me/preferences` conserva el idioma de cuenta; las consultas humanas lo
respetan y el historial añade versiones persistentes de las respuestas IA.
Nueve respuestas anteriores del propietario recuperadas en español, con textos
originales conservados. GET de historial no llama al modelo. APK Debug 0.1.3,
code 4, compilación `20261031-0709`; 194 pruebas Python/gateway y 85 Android
aprobadas, sin QA físico. Rollback vigente:
`.runtime/chat-languages-20261031-rollback.json`; cadena de Compose en
`.runtime/chat-languages-20261031-deploy.json`. La prueba HTTP real del idioma
pasó; recuperación de imágenes respondió `unavailable`, pendiente de diagnóstico
(ver `IMPLEMENTATION_STATUS.md`). Índice serial reanudado: puntero actual en
`.runtime/chat-languages-20261031-task.json`.

Actualización vigente de búsqueda (2026-10-31): API/worker usan
`realityos-backend:search-repair-20261031`, Alembic `20261031_0029`.
SAM se divide en grupos de máximo 16; análisis nuevos se preparan aparte y se
activan de forma atómica. El buscador devuelve resultados parciales válidos con
motivo y contadores separados. El martillo quedó recuperado (0,93 visual;
0,832 localización); consultas HTTP reales entregan 1 martillo y 4 alicates,
imágenes grandes señalizadas 1920×1280 e idioma español. 220 pruebas backend y
85 Android, APK 0.1.4 code 5; QA físico pendiente. Reparación restante en segundo
plano: task/puntero `.runtime/search-repair-20261031-task.json` (183 candidatos
al comenzar ese lote, aún en ejecución). Rollback vigente:
`.runtime/search-repair-20261031-rollback.json`; cadena de despliegue en
`.runtime/search-repair-20261031-deploy.json`. Ver estado detallado en
`IMPLEMENTATION_STATUS.md` antes de afirmar que el lote completo terminó.


Actualización Meta Display (2026-10-31): API/worker usan
`realityos-backend:meta-display-20261031`; Alembic continúa en
`20261031_0029`. El Display y los controles Android ofrecen búsqueda en galería
o registro por ubicación, y publicación explícita de foto/video en Perfil o
Trabajo elegido en el teléfono. Medios temporales por recurso, evidencia
contenida en 600×280 y recuperación de cargas por cuenta. APK 0.1.5 code 6.
Salud, contrato y lectura HTTP autorizada de evidencia verificados; gateway y
módulo protegido preservados. Rollback `.runtime/meta-display-20261031-rollback.json`.
Ver `IMPLEMENTATION_STATUS.md`: QA física pendiente y lint Android bloqueado
por tres traducciones preexistentes de la interfaz protegida.


Corrección de zoom del chat (2026-10-31): APK 0.1.6 code 7. El visor ignora el
evento sin centroide al soltar el último dedo y evita traslaciones NaN; conserva
la imagen y permite seguir arrastrando. Solicitudes de imagen estables por
URL/token. 94 pruebas Android aprobadas (9 de zoom); QA táctil física pendiente.
Backend y Alembic siguen en el release Meta Display descrito anteriormente.


Recuperación de procesamiento (2026-10-31): API y worker desplegados con
`realityos-backend:processing-recovery-20261031`; Alembic sigue en
`20261031_0029` y el contrato REST no cambia. Corregidos el parser SAM fuera de
un bucle asyncio activo y la persistencia del heartbeat. Las revisiones usan
una segunda localización por concepto del mismo objeto confirmado cuando la
caja tiene confianza insuficiente, conservando umbrales y originales.
`rebuild_search_evidence.py --pending-only --apply` recupera solo publicaciones
incompletas mediante tareas durables por medio, sin retirar duplicados. Lote
inicial: 37 de 238 publicaciones; progreso y tareas en
`.runtime/processing-recovery-20261031-progress.json` y
`.runtime/processing-recovery-20261031-task.json`. Sigue en ejecución: no afirmar
cero pendientes sin consultar el progreso. Las ambigüedades visuales reales
conservan la revisión pendiente. Pasan 244 pruebas backend/gateway, ruff y
comprobación de arquitectura. Salud, OpenAPI, Alembic, gateway y módulo
protegido verificados. Rollback:
`.runtime/processing-recovery-20261031-rollback.json`. APK único existente
`android/app/build/outputs/apk/debug/app-debug.apk`, 0.1.6 code 7.

Actualización de UI Ray-Ban Meta (2026-11-01): el inicio conserva Buscar y
Capturar foto o video. Buscar muestra Foto / Comando de voz; Capturar abre la
cámara y envía cada foto/video al Perfil privado sin grupo ni formulario.
Se reutilizan los servicios existentes de consulta por imagen, voz y subida,
conservando duplicados y reintentos. No hay cambios de servidor ni migraciones.
Las subidas anteriores mantienen su destino para recuperación. Ver
`WEARABLES.md` e `IMPLEMENTATION_STATUS.md` para validación y QA física pendiente.

Corrección de sensores/vista previa (2026-11-01): el dispositivo elegible y sus
identificadores virtuales determinan la ruta; Mock Device Kit siempre utiliza
CameraX y voz del teléfono, y solo gafas reales conectadas usan DAT. La cámara
mantiene barras/menús, X superior y foto inferior; Capturar conserva video.
Superficies y callbacks se invalidan al cerrar/reabrir, y el renderer permanece
montado. Formato, 119 pruebas Android, 10 de integración y APK Debug
`0.1.6-debug-20261101-0936` verificados. Lint conserva las tres traducciones
protegidas pendientes. Sin dispositivos ADB ni emulador: QA de sensores/táctil
en teléfono y hardware Ray-Ban sigue pendiente. Backend sin cambios.

Toques del visor corregidos (2026-11-01): foto/video/X reciben prioridad frente
a capas Android transparentes del SDK; X permanece habilitada durante captura.
Se elimina una foto temporal si CameraX completa su guardado después de cancelar.
Seis pruebas Compose/Robolectric con eventos táctiles pasan sobre el componente
real de controles (125 pruebas Android en total). APK único actualizado a
`0.1.6-debug-20261101-0952`. Las pruebas sustituyen sensores y renderer: QA física
y WebView DAT real pendientes, sin dispositivo ADB conectado. Backend sin cambios.

Búsqueda objeto/persona en Display (2026-11-01): Buscar ofrece **Buscar objeto /
Buscar persona / Comando de voz**. Ambos botones de foto abren la misma cámara;
objeto usa `queries/image` y persona el brazo `faces/search` existente con el
mismo probe, mostrando nombre, similitud e insignia por candidato (retrato solo
con foto de perfil externa, sin cabeceras de auth en Display). Sin cambios de
servidor ni migraciones; módulo protegido intacto. Formato, 128 pruebas Android
y APK Debug verificados. QA en emulador/dispositivo pendiente.

Voz con intención en Display (2026-11-01): el comando de voz clasifica el texto
con `search/route` y rutea: descripciones de persona a `profiles/search` (con
respuesta hablada y nombres coincidentes), objetos y texto ambiguo a la consulta
de galería, saludos al chat e invitados bloqueados de personas como en la app.
Sin cambios de servidor ni migraciones. Formato, 132 pruebas Android y APK Debug
verificados. QA de voz en emulador/dispositivo pendiente.

Miniaturas del match en persona-foto (2026-11-01): `display/media-links` acepta
`face_enrollment` y sirve la miniatura enrolada del match (con recuadro del
rostro) en URL firmada de corta duración, reutilizando consentimiento y acceso
del brazo biométrico sin modificarlo. El Display muestra esa foto por candidato
en vez de la foto de perfil. Contrato OpenAPI regenerado. Validación: 246
pruebas backend/gateway, 134 Android, ruff, ktlint y APK Debug. Desplegado
`realityos-backend:face-display-20261101` en api/worker con salud local y
pública 200, OpenAPI con `face_enrollment`, Alembic en head `20261101_0030` y
worker activo; gateway intacto. Rollback:
`.runtime/face-display-20261101-rollback.json` (`face-single-20261101`).

Foto grupal señalizada (2026-11-01): `faces/search` devuelve `probe_box` y
`probe_face_index` por match; nuevo `display/face-group-links` dibuja recuadros
numerados de colores sobre el probe efímero (caché en memoria con TTL, sin
persistir) y sirve tarjeta firmada. El Display abre la foto grupal señalizada
con lista numerada (nombre, similitud, color) y conserva las tarjetas por
candidato. Contrato regenerado. Validación: 249 backend/gateway, 140 Android,
ruff, ktlint, APK Debug y E2E vivo (3 caras → 5 matches, 3 recuadros).
Desplegado `realityos-backend:face-group-20261101`, salud 200, Alembic head,
worker activo. Rollback:
`.runtime/face-group-20261101-rollback.json` (`face-display-20261101`).

Corrección integral de idiomas (2026-11-01): 191 textos Android incorporados a
recursos EN/ES; chat local e historial reconocen mensajes antes mal etiquetados,
voz/reconocimiento usan la selección actual y Display refresca controles.
Ambas webs sincronizan la cuenta, traducen interfaz y fijan el idioma de voz;
publicadas localmente por excepción explícita autorizada por el propietario.
API/worker: `realityos-backend:all-languages-20261101`; Alembic permanece en
`20261101_0030`. Salud/OpenAPI/worker/runtime verificados; 19 mensajes reparados,
21 respuestas históricas listas en inglés y consulta HTTP/TTS coherentes con
la cuenta. Pasan 259 pruebas backend/gateway, seis web, 143 Android y lint.
APK Debug único actualizado; QA física pendiente. Rollbacks:
`.runtime/all-languages-20261101-rollback.json` y
`.runtime/all-languages-web-20261101-rollback.json`. Ver detalles y límites en
`IMPLEMENTATION_STATUS.md`.

Segunda revisión de idiomas (2026-11-01): corregidos errores de consulta
ocultos, reproducción de respuestas sin coincidencias, plurales naturales y
respuestas/imágenes/refinamientos tardíos. El ejemplo del buscador sigue el
idioma sin cambiar el borrador del usuario. Validación: 265 pruebas backend,
144 Android, seis web y 20 comprobaciones en Chromium (API/voz simuladas),
lint, formato, builds y APK único. Backend productivo:
`realityos-backend:language-review-20261101`; webs:
`realityos-{frontend,display}:language-review-web-20261101`. Salud, contrato,
Alembic head, worker y runtime verificados; cuenta en inglés conservada.
Rollbacks `.runtime/language-review-20261101-rollback.json` y
`.runtime/language-review-web-20261101-rollback.json`. QA física pendiente.

Integración TTS SeamlessM4T v2 (2026-11-01): endpoint autenticado `POST /v1/tts`
y reproducción en Android/gafas y ambas webs, con un reintento transitorio y
respaldo de voz actual. API/worker desplegados como
`realityos-backend:seamless-tts-20261101-r2`; salud, OpenAPI WAV, Alembic
`20261101_0030` y runtime del gateway verificados. 291 pruebas Python/gateway,
147 Android, 12 web y 20 Chromium; lint, builds y APK Debug único
`0.1.6-debug-20261101-1529` aprobados. Imágenes de gateway/Seamless construidas;
procesador oficial EN/ES verificado sin pesos. **Seamless aún no está activo**:
la herramienta remota exige aprobación en chat activo y no permitió inspeccionar
FRONTEND. Inferencia real, benchmark, activación y QA acústica siguen pendientes;
webs preparadas para publicación por CI, sin publicar en esta tarea. Ver
`docs/TTS.md` y `IMPLEMENTATION_STATUS.md`. Rollback servidor:
`.runtime/seamless-tts-20261101-rollback.json`.

Tercera revisión de idiomas (2026-11-01): el chat y los botones de repetición
conservan el idioma del texto; respuestas sin traducción lista no se leen con
la voz de otra selección. El Display elimina el fallback automático a
notas/títulos originales de objetos cuando falta el idioma, y mantiene nombres
propios de matches enrolados. APK único reconstruido; 153 pruebas Android,
63 relevantes backend/gateway y 12 web aprobadas, ktlint/lint y salud pública
verificados. Sin cambios de servidor en esta pasada. API/worker observados en
`realityos-backend:seamless-tts-20261101`, con `/v1/tts` en el contrato vigente.
La prueba acústica y QA física continúan pendientes. Evidencia:
`.runtime/language-third-pass-final.json` y `IMPLEMENTATION_STATUS.md`.


## Directo y voz local — 2026-11-01

Producción usa `META_CONNECTION_MODE=direct` y respaldo explícito por FRONTEND.
API/worker: `realityos-backend:direct-meta-20261101`; voz local:
`realityos-tts:direct-20261101` (BF16, 4 GiB, dos CPU). El endpoint público
`/tts/synthesize` tiene token propio; el gateway sigue disponible como reserva.
La clave Meta activa está en el `.env` privado del servidor y en el runtime de
FRONTEND. CI respeta esta selección. Pasaron 326 pruebas y consultas reales
directas; 404 controlados recuperaron Meta y voz mediante el gateway real.
Seis muestras EN/ES: 2,22–3,01 s; salud, OpenAPI y Alembic `20261101_0030`
verificados. Ver [TTS](TTS.md), [Gateway](GATEWAY.md) y estado de implementación.
Rollback: `.runtime/direct-meta-20261101-rollback.json`.


## Alternativa Windows local — 2026-11-01

Ver [Windows local](LOCAL_WINDOWS.md). Proyecto Docker separado `realityos-local`
y `.env.local`; Meta Live con clave propia, InsightFace local y voz ElevenLabs real. No
seeds. La cuenta de prueba local permite entrar sin Facebook ni reconocimiento
facial exclusivamente en el Debug local confirmado por el backend local.
Producción mantiene sus motores reales, configuración y acceso habitual.
Rutas locales ausentes fuera de `ENVIRONMENT=local` + `LOCAL_LOGIN_ENABLED=true`.
340 pruebas backend/gateway y checks PowerShell/Compose locales aprobados;
Windows nativo y APK completo pasan por CI. QA física y prueba integral Docker
Desktop Windows requieren ese entorno. No modificar perfiles de producción para
arrancar la alternativa local.

Revisión de Buscar en la vista previa Android (2026-11-01): apertura compartida
de cámara en el hilo principal, avisos ante bloqueos y publicación pendiente,
timeout de inicio y liberación del estado ocupado independiente de la generación
de respuestas. CI pulsa Buscar objeto/persona en el WebView oficial y verifica
CameraX en cámara emulada, con regresiones de permisos y cancelación. Backend y
consentimientos sin cambios; QA física pendiente. Ver `IMPLEMENTATION_STATUS.md`.

Señalización facial y perfil desde Display (2026-11-01): las etiquetas numéricas
se colocan fuera de todos los rostros, con una banda de reserva para grupos
densos; los contornos de la foto encontrada se dimensionan según la cara.
Los resultados incorporan Abrir perfil en la app; varias coincidencias permiten
elegir el perfil y volver al mismo resultado. Se usa el `user_id` interno devuelto
por la búsqueda y la pantalla de perfil existente, con autorización habitual.
Sin cambios de contratos, reconocimiento, consentimientos ni migraciones.


## Voz sin modelo residente — 2026-11-02

Producción pasa a `TTS_PROVIDER=elevenlabs`, modelo `eleven_flash_v2_5`, voz
George y WAV PCM 24 kHz; `/v1/tts` conserva autenticación y contrato. Muse Voice
Transcribe, Muse Spark y SAM permanecen. La credencial se copia desde la
configuración privada de Luxisoft a `.env.elevenlabs` (solo API). Seamless
queda detenido y sin reinicio automático en producción; Windows local conserva
su opción explícita. CI reconcilia el estado aun si existe el contenedor viejo.
El antiguo endpoint de servicio `/tts/synthesize` responde 410. Ver `TTS.md`.

Validación previa: 369 pruebas backend/gateway y lint aprobados; muestras
reales ElevenLabs EN/ES válidas, cuenta Starter
activa; pruebas cubren autenticación, ausencia de egress en mock, independencia
del gateway Meta, concurrencia/cancelación, límites, errores sin replay y
reconciliación del despliegue. El recibo privado de release y las mediciones de
RAM quedan en `.runtime/ram-elevenlabs-20261102-*` y
`/home/jmarin/server-memory-audit-20261102/`. Consultar esos recibos para el
resultado efectivo del despliegue y sus límites; no confundir preflight con QA
física de Android/gafas.


## Eliminación de síntesis local — 2026-11-02

Por instrucción explícita del propietario se elimina Seamless, incluyendo código,
contenedor, imagen, volumen de pesos, dependencias, trabajos de CI y opciones
Windows. ElevenLabs es el único motor de síntesis; Muse Voice Transcribe/Spark/SAM
se conservan. Windows utiliza su propia clave ElevenLabs y no copia claves de
producción. Las referencias previas a modelos/volúmenes y rollbacks de Seamless
son históricas y quedan retiradas; la recuperación inmediata usa la última
versión ElevenLabs, sin modelo local. Se mantienen datos de usuario y biometría.


Carga verificada de fotos en Display (2026-11-02): se conserva el diseño actual.
Android valida y decodifica los derivados firmados antes de pasarlos a DAT como
Bitmap; la tarjeta grupal se restaura desde memoria durante la misma búsqueda,
respetando el vencimiento. Los matches solicitan enlaces autorizados nuevos y
los fallos muestran recuperación explícita. Cancelación y cambios de pantalla o
cuenta impiden restaurar imágenes anteriores. Pasan 170 pruebas Android locales;
regresiones HTTPS y de píxeles incorporadas al emulador de CI. Ver `WEARABLES.md`
e `IMPLEMENTATION_STATUS.md`. Sin cambios de backend ni biometría; QA física
pendiente.
