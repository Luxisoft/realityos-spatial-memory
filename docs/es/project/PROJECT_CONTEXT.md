[English](../../en/project/PROJECT_CONTEXT.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Contexto del proyecto

Mapa de trabajo vigente. Lee primero las [convenciones](../../../AGENTS.md), consulta el [estado verificado](IMPLEMENTATION_STATUS.md) y abre la guía del área que vas a cambiar. El historial de cambios está en Git.

## Estructura

| Ruta | Responsabilidad |
| --- | --- |
| `backend/app/` | API y contratos compartidos con el worker: HTTP, proveedores, procesamiento, cuentas, social, expedientes y almacenamiento. |
| `backend/app/faces.py` | Biometría aislada y protegida por AGENTS.md. |
| `backend/alembic/versions/` | Esquema Alembic; revisión vigente documentada `20261103_0035`. |
| `android/` | Única app: Kotlin/Compose, CameraX, DAT y Display nativo; Mock Device Kit solo Debug. |
| `meta-gateway/` | Egreso restringido a rutas Meta permitidas. |
| `infrastructure/` | Compose para postgres, redis, api, worker, scheduler y proxy; TLS y gateway. |
| `simulator/` | Recursos sintéticos para escenarios y QA. |
| `tests/`, `gateway-tests/` | Regresiones y contrato OpenAPI congelado. |
| `scripts/` | Preparación de datos, importación, mantenimiento y generadores/verificadores de documentación. |
| `docs/es/`, `docs/en/` | Guías por idioma y tema, con los mismos nombres de archivo. |
| `docs/assets/`, `docs/postman/` | Recursos compartidos y colecciones descargables. |
| `.runtime/` | Archivos privados ignorados: accesos, evidencias, releases y rollback. |

## Flujos e invariantes

- Captura/publicación/importación explícita → original BYTEA → procesamiento → evidencia y traducciones persistidas. Consultar no registra nueva evidencia.
- R2/S3 es una fuente privada por cuenta; importar conserva una copia en RealityOS. Desconectar no elimina publicaciones existentes.
- Todo recurso se vuelve a autorizar al consultarlo o descargarlo. Los grupos no reciben las claves del bucket del creador.
- Biometría mantiene consentimiento y enrolamiento explícitos, separada del flujo de objetos. No modificar sus módulos como efecto secundario.
- Meta directo con gateway como respaldo configurable; Muse Voice Transcribe para entrada y ElevenLabs para salida. Claves solo en servidor.
- Windows local usa `.env.local`, el proyecto Docker `realityos-local` y su propio APK Debug. No reutiliza datos ni claves productivas automáticamente.

## Guías de trabajo

- [API y Postman](../api/API.md), [contrato generado](../api/API_REFERENCE.md) y [datos](../architecture/DATABASE.md).
- [Arquitectura](../architecture/ARCHITECTURE.md), [seguridad](../architecture/SECURITY.md) y [diseño](../architecture/UI_DESIGN.md).
- [Android](../integrations/ANDROID.md), [gafas](../integrations/WEARABLES.md), [Meta](../integrations/META_INTEGRATION.md) y [voz](../integrations/TTS.md).
- [Instalación y operación](../deployment/DEPLOYMENT.md), [gateway](../deployment/DEPLOYMENT_GATEWAY.md) y [Windows](../deployment/DEPLOYMENT_LOCALHOST.md).
- [Buckets](../guides/STORAGE_CONNECTIONS.md), [expedientes](../guides/WORKSPACE_DATA.md), [demo](../guides/DEMO.md) y [checklist](../testing/IMPLEMENTATION_CHECKLIST.md).
- [Estado y pendientes](IMPLEMENTATION_STATUS.md) y [entrega hackathon](HACKATHON.md).

## Validación y entrega

Desde la raíz: `make docs-check`, `make architecture-check`, `make lint`, `make test` y `make android-check`, según el cambio. APK único: `android/app/build/outputs/apk/debug/app-debug.apk`.

Los cambios se publican en `main` siguiendo AGENTS.md. Los cambios de documentación no requieren otro APK. Para servidor, conservar runtime/rollback y comprobar salud, OpenAPI y Alembic; las reglas de autorización Docker están en AGENTS.md. No registrar como aprobadas pruebas de dispositivo, R2, proveedores o Windows que no se hayan ejecutado.
