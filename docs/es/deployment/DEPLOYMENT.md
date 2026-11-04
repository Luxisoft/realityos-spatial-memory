> **Corrección vigente: localhost principal.** Windows/Linux x64 ejecutan PostgreSQL, Redis, API y worker. Meta usa la clave propia del jurado; voz de salida instalada en Android. Gateway, buckets, Facebook, SMTP, scheduler y ElevenLabs están fuera del recorrido local. La configuración remota que aparece en esta guía es histórica. [Instalación vigente](../deployment/DEPLOYMENT_LOCALHOST.md).

[English](../../en/deployment/DEPLOYMENT.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Instalación y operación

| Entorno | Guía |
| --- | --- |
| Servidor Ubuntu con acceso directo | [Instalar servidor](DEPLOYMENT_DIRECT.md) |
| Gateway Meta o respaldo | [Instalar gateway](DEPLOYMENT_GATEWAY.md) |
| Windows + Docker Desktop | [Instalación local aislada](DEPLOYMENT_LOCALHOST.md) |

## Configuración privada

El servidor usa `.env` para seleccionar Meta directo o gateway y el respaldo. Los archivos opcionales `.env.facebook`, `.env.elevenlabs` y `.env.storage` contienen ajustes de sus integraciones. Mantenerlos fuera de Git y con permisos 0600. La síntesis ElevenLabs y las conexiones R2/S3 son independientes del gateway Meta.

Para conectar buckets, configura una `STORAGE_ENCRYPTION_KEY` aleatoria y persistente en `.env.storage`. API y worker deben compartirla; perderla o reemplazarla impide descifrar conexiones existentes. El scheduler programa sincronizaciones y el worker las procesa. Sigue la [guía de buckets](../guides/STORAGE_CONNECTIONS.md) antes de preparar datos demo.

## Despliegue y comprobación

El [workflow de producción](../../../.github/workflows/deploy-production.yml) publica imágenes inmutables y despliega API/worker/scheduler y gateway por trabajos independientes. Conserva el entorno de ejecución y guarda el rollback de imágenes en `.runtime/ci-runtime-rollback.json`. El proxy publica la API y las páginas de acciones de correo sobre HTTPS.

Después de cada despliegue, comprueba `/health/ready`, el documento completo `/v1/openapi.json` y la revisión `alembic current`. Los comandos de una instalación nueva están en la [guía directa](DEPLOYMENT_DIRECT.md). No des por buena una API solo porque responde salud.

Si el host tiene instalado el ingreso bajo demanda de `scripts/deploy/enable_demand_api.py`, reinicia `backend-demand-realityos.service` del usuario de despliegue después de recrear la API: ese servicio mantiene la dirección del contenedor. El workflow ya ejecuta este paso y verifica una petición pública `/v1/`.

## Reversión y datos

Para volver a una imagen publicada, ejecuta **Deploy production** con su `release_tag` inmutable. Una reversión de código no elimina tablas nuevas ni recupera datos borrados. Si la versión anterior no tenía scheduler, detenlo antes de aplicar su rollback. Cualquier reversión de esquema/datos necesita un procedimiento específico probado para esa migración.

Las publicaciones ordinarias no requieren un dump de PostgreSQL. Solo una migración que necesite reversión puede crear una instantánea técnica `pre-*.dump` en `.runtime/`, con vencimiento de 24 horas —una hora bajo presión de disco—. Las copias oficiales de código/base de datos pertenecen al destino GitHub privado aprobado por el propietario; R2 se reserva para medios. Conserva los volúmenes de datos al detener servicios.

Para ejecutar comandos Docker en este host, aplica la autorización definida en [AGENTS.md](../../../AGENTS.md). Tras una publicación, retira imágenes y contenedores de trabajo que ya no se usen, conservando la imagen necesaria para rollback.
