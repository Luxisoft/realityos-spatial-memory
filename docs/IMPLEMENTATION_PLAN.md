# Plan de ejecución — RealityOS

Este plan traduce la misión de
[REALITYOS_MISSION.md](REALITYOS_MISSION.md) en incrementos ejecutables. La
prioridad es completar un recorrido honesto de **registrar → procesar →
consultar evidencia** antes de ampliar superficie. Cada fase se valida, se
documenta y se versiona antes de comenzar la siguiente.

## Fase 0 — Fundaciones y trazabilidad

**Resultado:** monorepo operativo, configuración segura y reglas de trabajo.

1. Crear la rama `feat/realityos-initial-platform`, conservar Apache-2.0 y no
   modificar trabajo ajeno.
2. Crear `backend/`, `frontend/`, `display-webapp/`, `android/`,
   `infrastructure/`, `simulator/`, `tests/`, `docs/`, `scripts/` y CI.
3. Añadir `.gitignore`, `.env.example`, `Makefile`, convenciones de agentes
   y documentación de arquitectura inicial.
4. Fijar configuración tipada: URLs, secretos, `META_MODE`, CORS, límites de
   carga/vídeo, expiración JWT, proxy y flags de desarrollo.
5. Establecer formatter, lint, pruebas y comandos reproducibles.

**Puerta de salida:** una instalación limpia puede validar configuración y
ejecutar checks mínimos sin secretos reales.

## Fase 1 — Backend funcional y seguridad

**Resultado:** API FastAPI protegida y conectada a PostgreSQL mediante
migraciones reales.

1. Crear aplicación, configuración Pydantic v2, sesión SQLAlchemy 2 y health
   endpoints `live`/ `ready`.
2. Diseñar modelos y migración inicial con UUID, FK, índices, `pg_trgm`, FTS,
   constraints y `BYTEA` en `media_assets`.
3. Implementar usuarios, hash de contraseña, JWT access/refresh, revocación,
   endpoint `me`, RBAC y aislamiento de workspace.
4. Implementar workspaces, membresías y zonas jerárquicas.
5. Implementar sesiones explícitas de captura y cargas de imagen con
   autorización, validación MIME/tamaño/dimensiones y SHA-256.
6. Servir medios originales autorizados desde PostgreSQL y auditar acciones.

**Puerta de salida:** migraciones sobre PostgreSQL, login, workspace, creación
de sesión, carga y lectura del mismo binario pasan pruebas de integración.

## Fase 2 — Memoria espacial y recuperación

**Resultado:** observaciones verificables y consultas de solo lectura.

1. Añadir objetos lógicos, alias, observaciones, relaciones espaciales,
   verificación y jobs idempotentes por captura, hash y sesión.
2. Implementar búsqueda textual con FTS/trigramas y una interfaz de repositorio
   que permita añadir búsqueda vectorial sin dependencia de pgvector.
3. Resolver la última observación **verificada**, con desempate y respuestas de
   evidencia insuficiente o ambigua.
4. Implementar historial de objeto, revisión humana y cálculo de ubicación sin
   borrar observaciones.
5. Generar imagen resaltada desde geometría persistida sin alterar el original y
   exponer media/resultado bajo autorización.
6. Hacer las rutas y servicios de consulta solo lectura; telemetría y auditoría
   se mantienen separadas del dominio de capturas.

**Puerta de salida:** pruebas de existencia, ausencia, ambigüedad, historial,
resaltado, permisos query-only y aislamiento de workspaces.

## Fase 3 — Pipeline Meta, mock y vídeo acotado

**Resultado:** procesamiento asíncrono verificable sin credenciales y preparado
para Meta Live.

1. Definir contratos Pydantic para análisis visual, segmentación, ASR e
   interpretación de consultas.
2. Implementar `MetaModelClient` live después de contrastar endpoints y
   respuestas con documentación oficial vigente; añadir Bearer, timeout, backoff,
   límites, métricas y errores explícitos.
3. Implementar proveedor mock determinista con fixtures etiquetados, sin salida
   a red.
4. Crear Celery/Redis: guardar original, encolar, analizar Muse, segmentar SAM,
   asociar identidad, persistir derivados/observaciones y finalizar job.
5. Garantizar reintentos seguros, estado observable y deduplicación.
6. Añadir carga de vídeo limitada, validación, frame extraction FFmpeg,
   timestamps y trazabilidad; documentar límites de clips largos.
7. Implementar `queries/audio` con Muse Voice Transcribe live o mock y separar
   STT, recuperación y TTS.

**Puerta de salida:** worker completa pipeline mock, un job duplicado no duplica
observaciones y pruebas de contrato cubren mock, live simulado, timeout y error.

## Fase 4 — Panel administrativo web

**Resultado:** panel React/TypeScript en español que recorre el producto.

1. Crear base Vite tipada, cliente API autenticado, sesión y estados de carga,
   vacío, error y reintento.
2. Implementar inicio, registro, explorador de objetos, árbol de ubicaciones,
   consulta, historial, administración y estado de jobs.
3. Registrar elige ubicación, abre/cierra sesión y carga recursos; Consultar
   nunca ofrece captura.
4. Mostrar evidencia real, overlay de máscara/caja, fecha y texto «última vez
   visto»; usar Web Speech/TTS solo cuando el navegador lo soporte.
5. Diseñar responsive, accesible y seguro para una demostración de hackatón.

**Puerta de salida:** `build` pasa y una demo mock permite registro y consulta
desde el navegador contra la API.

## Fase 5 — Android, Wearables y Display

**Resultado:** clientes preparados para capacidades oficiales verificables.

1. Crear Android Kotlin/Compose con build reproducible, login, workspace,
   Registrar, Consultar, upload, STT y TTS nativo.
2. Integrar Meta Wearables DAT únicamente tras confirmar API, permisos,
   inicialización, sesión y capacidades oficiales; usar Mock Device Kit y
   documentar lo simulado.
3. Gestionar pairing, desconexión, permisos y errores. Los dispositivos sin
   display usan audio y teléfono; no se presupone cámara ni pantalla.
4. Crear `display-webapp` independiente: 600×600, alto contraste, texto
   breve, D-pad/teclado, login seguro, consulta y audio soportado.
5. Incorporar toolkit oficial Display solo si se confirma compatible y validar
   visualmente en el simulador disponible.

**Puerta de salida:** Gradle se marca correcto solo tras ejecución real; Display
compila y se prueba en simulador sin equipararlo a gafas físicas.

## Fase 6 — Operación, demostración y calidad

**Resultado:** entrega Docker, CI y documentación lista para jurado.

1. Construir Dockerfiles y Compose para PostgreSQL, Redis, API, worker, panel,
   Display y proxy con red interna, volúmenes, health checks, restarts y
   migración/seed controlados.
2. Añadir configuración localhost HTTP y guía de HTTPS real, dominio, CORS,
   backups/restauración PostgreSQL y rotación de secretos.
3. Crear seed legal/sintético del Taller RealityOS y scripts de bootstrap,
   migración, pruebas y backup.
4. Configurar GitHub Actions para lint, tests, build frontend/Display y Android
   solo si el entorno es capaz.
5. Completar README inglés y documentación de arquitectura, base de datos, API,
   Meta, wearables, despliegue, demo, seguridad y estado.
6. Ejecutar demo E2E y preparar commits por fase; publicar rama/PR solo con
   permisos reales y sin force-push.

**Puerta de salida:** Compose inicia servicios disponibles, demo mock es
repetible, pruebas se reportan con resultados y bloqueos externos con precisión.

## Decisiones transversales

- Ninguna función se entrega sin prueba proporcional y documentación actualizada.
- No se suben credenciales, tokens o fotografías privadas al repositorio.
- La respuesta muestra confianza visual y confianza de recuperación por separado.
- No se inventan endpoints, SDKs, resultados Meta ni ejecuciones de comandos.
- Una integración externa bloqueada conserva interfaz real, mock claro y estado
  documentado.
