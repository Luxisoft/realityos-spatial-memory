[English](../../en/project/PROJECT_CONTEXT.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Contexto del proyecto

RealityOS tiene un monolito modular y dos composiciones: **local** en el PC Windows/Linux del jurado y **server** en el servidor RealityOS. El host de desarrollo actual es el servidor RealityOS; localhost no designa sus servicios productivos. **FRONTEND** es otro servidor, dedicado al gateway Meta restringido. Esta reorganización no autoriza despliegues, reinicios ni cambios en los datos de ninguno de esos servidores.

Lee las [convenciones](../../../AGENTS.md), el [estado verificado](IMPLEMENTATION_STATUS.md) y la guía del área que vas a cambiar. El historial de entregas permanece en Git.

## Estructura

| Ruta | Responsabilidad |
| --- | --- |
| `backend/app/runtime/` | Composición explícita de routers y worker local/server; instalador de esquema. |
| `backend/app/` | HTTP, servicios, proveedores, modelos y persistencia compartidos por API y worker. |
| `backend/app/local/` | Acceso local desde BD e inicialización SQL separada del runtime operativo. |
| `backend/app/faces.py`, `face_setup.py` | Brazo biométrico protegido; consentimiento y enrolamiento privado. |
| `backend/schema/20261104_0040/` | Snapshot DDL inmutable para PostgreSQL vacío. |
| `backend/alembic/versions/` | Historial preservado; revisión de código `20261104_0041`. |
| `android/` | Única app: Kotlin/Compose, CameraX, DAT y Display nativo; repositorios y componentes compartidos. |
| `meta-gateway/` | Egreso remoto restringido a rutas Meta permitidas. |
| `infrastructure/` | Compose local de cuatro servicios y composición server separada. |
| `simulator/database/` | SQL único de inicialización de escenarios locales. |
| `simulator/media/` | Imágenes/videos locales organizados y manifiesto técnico de licencia/hash. |
| `tests/`, `gateway-tests/` | Regresiones, PostgreSQL efímero y contratos OpenAPI. |
| `scripts/` | Instalación local, mantenimiento y generadores/verificadores. |
| `docs/es/`, `docs/en/` | Guías equivalentes por idioma; recursos en `docs/assets/` y `docs/postman/`. |
| `.runtime/` | Archivos privados, pruebas y builds aislados; ignorados por Git. |

## Invariantes

- PostgreSQL/BYTEA es la fuente de verdad. Las consultas no leen catálogos JSON ni SQL de instalación.
- Captura/publicación explícita → original → procesamiento → evidencia persistida. Query no registra evidencia nueva.
- Las publicaciones requieren grupo. Cada lectura, descarga y modificación revalida permisos y pertenencia.
- La inicialización local es transaccional y versionada; no repone contenido borrado ni sobrescribe ediciones en reinicios.
- Biometría mantiene sus permisos, consentimientos y referencias privadas, fuera del procesamiento de objetos.
- Localhost usa PostgreSQL, Redis, API y worker; Meta directo con clave del jurado y voces instaladas en Android. No incluye gateway, buckets, Facebook, SMTP, scheduler ni ElevenLabs.
- El servidor conserva sus integraciones privadas y la alternativa de gateway FRONTEND. Las claves permanecen fuera del cliente y de Git.
- Los archivos de entorno se seleccionan explícitamente con `REALITYOS_ENV_FILE`; Compose inyecta la configuración del entorno elegido.

## Guías y validación

[Arquitectura](../architecture/ARCHITECTURE.md) · [Datos](../architecture/DATABASE.md) · [Seguridad](../architecture/SECURITY.md) · [Diseño](../architecture/UI_DESIGN.md) · [API y Postman](../api/API.md)

[Android](../integrations/ANDROID.md) · [Gafas](../integrations/WEARABLES.md) · [Meta](../integrations/META_INTEGRATION.md) · [Localhost](../deployment/DEPLOYMENT_LOCALHOST.md) · [Servidor](../deployment/DEPLOYMENT.md) · [Gateway](../deployment/DEPLOYMENT_GATEWAY.md)

Desde la raíz: `make docs-check`, `make architecture-check`, `make lint`, `make test` y `make android-check`, según el cambio. Las pruebas PostgreSQL crean clusters temporales en `.runtime/`, separados de los servicios existentes. No declarar como realizadas pruebas de dispositivo, proveedores externos, Docker o Windows que no se ejecutaron.

La primera instalación usa `Start-RealityOS.ps1` o `make local-start`. Para
correcciones de código/datos en una instalación existente, usar
`Update-RealityOS.ps1` o `make local-update`: reutilizan la imagen instalada y
montan las fuentes locales en lectura. Cambios de dependencias o imagen base
requieren el instalador completo. Ver [actualizaciones](../README.md#local-updates).

Los cambios se entregan en `main` según AGENTS.md; el despliegue remoto requiere autorización separada. El APK Debug canónico está en `android/app/build/outputs/apk/debug/app-debug.apk`, bajo Git LFS y con la firma existente. Un cambio Android o de contrato requiere reconstruirlo; el estado de esa validación se registra por entrega.
