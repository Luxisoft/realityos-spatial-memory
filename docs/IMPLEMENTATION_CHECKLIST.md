# Checklist por fases — RealityOS

Marca un ítem únicamente cuando existe implementación, verificación y evidencia
documentada. `[~]` significa trabajo parcial; `[x]` exige resultado real de
comando, prueba o simulador. Este documento no sustituye
`IMPLEMENTATION_STATUS.md` para bloqueos detallados.

## Fase 0 — Fundaciones

- [x] Repositorio inspeccionado y licencia Apache-2.0 preservada.
- [x] Rama local `feat/realityos-initial-platform` creada.
- [x] Misión y plan de implementación incorporados en `docs/`.
- [x] Checklist de aceptación por fases creada.
- [x] Estructura completa de monorepo creada.
- [x] `.env.example`, `.gitignore`, Makefile y convenciones de agentes creados.
- [x] Toolchain de formato, lint y pruebas configurado.
- [x] Arquitectura inicial y estado de implementación documentados.
- [ ] Commit de fundaciones creado.

## Fase 1 — API, persistencia y seguridad

- [x] FastAPI inicia y expone `/health/live` y `/health/ready`.
- [x] Configuración tipada distingue desarrollo y producción.
- [x] PostgreSQL, SQLAlchemy 2, Psycopg y Alembic configurados.
- [x] Migración inicial crea todas las entidades requeridas.
- [x] `pg_trgm`, FTS, claves foráneas, índices y constraints están migrados.
- [x] `media_assets.original_bytes` (o equivalente) es `BYTEA` fuente de verdad.
- [x] Login, refresh con revocación y `me` están implementados.
- [x] Contraseñas usan hash seguro y secretos no aparecen en logs.
- [x] RBAC separa `register`, `query` y `admin`.
- [x] Workspaces, miembros y zonas se aíslan por autorización.
- [x] Sesiones se abren y cierran explícitamente.
- [x] Upload valida autorización, consentimiento, MIME, tamaño, hash y dimensiones.
- [x] Originales se leen desde PostgreSQL con autorización.
- [x] Auditoría registra acciones sin datos sensibles.
- [~] Pruebas: SQLite cubre inicio, workspace, upload BYTEA, hash y lectura; las migraciones e índices se verificaron contra PostgreSQL real, pero falta una suite de integración PostgreSQL automatizada.

## Fase 2 — Memoria y consultas

- [x] Objetos lógicos, alias, observaciones y relaciones espaciales modelados.
- [x] Se conserva historial completo de observaciones.
- [x] Verificación y corrección humana de observaciones implementada.
- [x] Última ubicación se calcula desde observaciones verificadas.
- [x] Búsqueda FTS/trigramas encuentra alias y nombres relevantes.
- [ ] Interfaz de búsqueda vectorial futura existe sin requerir pgvector.
- [x] Consulta existente devuelve evidencia, fecha, geometría y confianza.
- [x] Consulta inexistente informa falta de evidencia sin inventar ubicación.
- [x] Consulta ambigua solicita o explica desambiguación.
- [x] La respuesta usa «última vez visto» y separa confianza visual/recuperación.
- [x] La consulta identifica la observación exacta y devuelve máscara SAM en caché o caja Muse aproximada sin alterar el original.
- [x] Query-only no crea captura, sesión, media, observación ni job.
- [~] Pruebas: última observación, ausencia, ambigüedad, permisos, aislamiento, alias y geometría están cubiertos; falta caso automatizado específico de historial multievidencia.

## Fase 3 — Meta, jobs y vídeo

- [x] Contratos Pydantic de análisis, segmentación, ASR e interpretación definidos.
- [x] `META_MODE=mock` es determinista, documentado y nunca llama a Meta.
- [x] Fixtures mock se etiquetan como simulados.
- [~] `META_MODE=live` usa endpoints oficiales revisados; el catálogo Meta real se verificó por gateway, falta una inferencia visual/ASR de producción.
- [x] Gateway de egreso restringe rutas Meta, inyecta la credencial y preserva multipart sin persistir medios.
- [x] Producción guarda `MODEL_API_KEY` exclusivamente en FRONTEND y API/worker usan el gateway sin recibirla.
- [~] Cliente aplica timeout, backoff, validación y error explícito; faltan métricas de uso y rate limiter distribuido.
- [~] Muse Spark está conectado a análisis, relaciones e intención cuando Live está configurado; falta una inferencia visual pagada verificada.
- [x] SAM 3.1 se invoca bajo demanda por observación verificada, persiste máscara one-bit BYTEA y reutiliza el job idempotente.
- [~] Muse Voice Transcribe está conectado solo como STT; falta una transcripción real verificada.
- [~] Redis/Celery y la tarea están implementados; falta prueba de entrega de broker.
- [x] Reintentos e idempotencia evitan observaciones duplicadas.
- [~] Vídeo limitado conserva original BYTEA, frames representativos, timestamps aproximados y trazabilidad; falta una prueba Live de un clip subido por usuario y no hay streaming ni audio de video.
- [ ] Pruebas de contrato: mock, live simulado, timeout, error e idempotencia.

## Fase 4 — Panel web

- [x] Vite + React + TypeScript compilan.
- [x] Login y sesión segura contra API implementados.
- [ ] Inicio muestra resumen de espacios, objetos, medios y observaciones.
- [x] Registrar permite elegir ubicación, controlar sesión y cargar fotos.
- [x] Objetos filtra por nombre/alias, categoría y zona autorizados.
- [x] Mapa representa jerarquía sin prometer coordenadas 3D.
- [x] Consultar muestra evidencia real, overlay, fecha, confianza y texto TTS.
- [~] Historial autorizado de objetos está implementado; administración de miembros y roles sigue pendiente en el panel.
- [x] Estados de carga, vacío, error y recuperación implementados.
- [ ] TTS de navegador solo se anuncia si el runtime lo soporta.
- [x] Build de frontend y Display pasa; faltan pruebas de UI.

## Fase 5 — Android y Display

- [ ] Proyecto Android Kotlin/Compose tiene build reproducible.
- [ ] Android implementa login, workspace, Registrar y Consultar.
- [ ] Android carga recursos y usa TTS nativo cuando está disponible.
- [ ] DAT SDK se integra solo con APIs oficiales confirmadas.
- [ ] Sesión, pairing, permisos, desconexión y error se manejan.
- [ ] Mock Device Kit cubre estados de dispositivo posibles en el entorno.
- [ ] Limitación display/no-display se comunica correctamente.
- [x] Web app Display 600×600 compila de forma independiente.
- [x] Display soporta login, consulta, resultado, audio y D-pad/teclado nativos.
- [ ] Aspecto Display se comprueba en simulador oficial disponible.
- [ ] Gradle/simulador se registran sin equipararlos a gafas físicas.

## Fase 6 — Operación, demo y entrega

- [x] Docker Compose define PostgreSQL, Redis, API, worker, panel, Display y proxy.
- [ ] Servicios usan health checks, red interna, volúmenes y restarts.
- [ ] Migración y seed son comandos reproducibles.
- [ ] Localhost HTTP funciona y HTTPS/dominio real están documentados.
- [ ] Existe estrategia y script de backup/restauración PostgreSQL.
- [x] Seed legal/sintético crea Taller RealityOS y seis objetos de demo.
- [ ] Demo prueba registro, BYTEA, proceso mock, consulta, resaltado, audio y Display.
- [ ] Demo verifica que Consultar no realiza grabación.
- [x] GitHub Actions ejecuta checks realmente disponibles.
- [x] Workflow versionado construye imágenes GHCR y prepara despliegue/rollback gateway y RealityOS tras merge a `main`.
- [x] DNS, secretos GitHub, certificado TLS y primer despliegue en FRONTEND se verificaron mediante el workflow de producción 40434117386.
- [x] README inglés y documentación de arquitectura, DB, API, Meta, Wearables, despliegue, demo y seguridad existen.
- [x] `IMPLEMENTATION_STATUS.md` enumera pendientes y bloqueos verificables.
- [x] Commits de implementación creados; PR #1 fusionado a `main` con CI y despliegue verde.

## Criterios finales de aceptación

- [x] Docker Compose inicia los servicios disponibles; la producción reporta API, PostgreSQL y Redis saludables.
- [ ] Migraciones reales crean el esquema y datos demo.
- [ ] Fotos se registran, verifican y recuperan desde PostgreSQL `BYTEA`.
- [ ] Objetos, ubicaciones, observaciones e historial funcionan con aislamiento.
- [ ] Consultar recupera evidencia resaltada sin iniciar una captura.
- [ ] Mock funciona sin credenciales y Live falla de forma comprensible sin ellas.
- [ ] Panel y Display compilan; Android solo se aprueba después de Gradle real.
- [ ] Pruebas, limitaciones y estado Wearables son honestos y documentados.
