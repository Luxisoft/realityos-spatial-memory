# Despliegue en Ubuntu

1. Instale Docker Engine y Compose v2, clone el repositorio y copie .env.example
   a .env.
2. Cambie POSTGRES_PASSWORD, JWT_SECRET y la credencial demo. Mantenga
   META_MODE=mock hasta disponer de una clave Meta con Muse Spark/SAM habilitado.
3. Ejecute docker compose --env-file .env -f infrastructure/docker-compose.yml up --build.
4. El proxy Compose queda ligado a `127.0.0.1:HTTP_PORT` por defecto. Para
   producción, el workflow administra el host TLS
   `https://realityos.luxisoft.com`, que publica panel, Display y `/v1/` sobre
   443; no exponga 8090 a Internet.
5. Cree backups con scripts/backup-postgres.sh y pruebe pg_restore.

API y worker no exponen PostgreSQL ni Redis al host; los volúmenes persistentes
son postgres_data y redis_data. Solo API, worker y proxy se unen a la red de
egress: API/worker la necesitan para Meta y proxy la necesita para publicar el
puerto HTTP. Restrinja CORS a dominios reales antes de producción.

## Producción mediante GitHub Actions

Los merges a `main` activan `.github/workflows/deploy-production.yml`. El
workflow prueba el código y publica imágenes inmutables en GHCR. RealityOS y
el gateway de FRONTEND se despliegan de forma independiente; un fallo de FRONTEND
no bloquea la actualización de API/worker con conexión directa. Configure el
Environment protegido `production` con los secretos indicados en
[Gateway](GATEWAY.md). Los secretos no se almacenan en Git ni en archivos del
repositorio.

Antes del primer merge de despliegue, cree el registro DNS `A` de
`meta.luxisoft.com` apuntando a `198.252.105.131`. El workflow valida Docker,
Nginx, TLS, el catálogo de modelos de Meta y la salud de RealityOS. La selección `META_CONNECTION_MODE=direct|gateway` y el respaldo
`META_GATEWAY_FALLBACK_ENABLED=true|false` se configuran en `.env`; CI no los
sobrescribe. Instale la clave Meta activa y el token de gateway en ese archivo
privado antes de activar Live. Un fallo de catálogo en FRONTEND afecta únicamente
al despliegue del gateway.

Para el teléfono sin gafas físicas, cree también el DNS de
`realityos.luxisoft.com` hacia este servidor. El mismo workflow emite el
certificado Let's Encrypt, instala el virtual host Nginx, limita el bootstrap
de dispositivos virtuales por IP de Cloudflare y habilita una identidad
temporal para el workspace `Taller de electrónica`. Esa identidad funciona
solo con `META_MODE=live`, se entrega al teléfono por HTTPS y puede revocarse
o reemplazarse por una credencial administrada.

### Cloudflare y el primer certificado

Si la zona usa un Worker o Pages para `*.luxisoft.com`, cree una ruta más
específica `realityos.luxisoft.com/*` con Worker **None** (o excluya ese host
de la ruta comodín). El registro DNS `A` debe apuntar a la IP pública de este
servidor. Para el primer despliegue, la alternativa más sencilla es dejar ese
registro como **DNS only** (nube gris), ejecutar el workflow y, cuando el
certificado exista, reactivar el proxy de Cloudflare con SSL/TLS en **Full
(strict)**. Una página 404 de LUXIPANEL en
`/.well-known/acme-challenge/...` indica que Cloudflare sigue enviando el
desafío al origen equivocado; no es un fallo de Nginx ni de Certbot.

## Reanudación de análisis de búsqueda

El runtime backend define `PYTHONPATH=/app` para que API, worker y scripts
administrativos importen el mismo código de la imagen, también cuando Python
se ejecuta con un archivo bajo `/scripts`.

`python /scripts/rebuild_search_evidence.py --pending-only` inspecciona sin
modificar datos los análisis incompletos y revisiones pendientes. Añadir
`--apply` encola una cadena serial de tareas durables por publicación. No
retira duplicados ni modifica originales. Cada tarea comprueba que el medio
siga siendo el mismo, omite trabajo ya completado y reutiliza fotogramas y
revisiones guardados. La confirmación de tarea se realiza al finalizar y el
trabajo se rechaza para reentrega si se pierde el proceso del worker. Un lease
activo impide repetir inferencia concurrente; uno vencido permite reanudar.
El heartbeat se persiste en la columna `updated_at` ya existente en
`gallery_index_runs`, sin migración nueva.

La espera por otro propietario del lease no consume el presupuesto de dos
reintentos del proveedor ni abandona una cadena por la duración de un video.
En reanudaciones sin objetos nuevos por revisar, se guardan igualmente las
resoluciones retenidas y se recalcula el contador de revisión pendiente.


## Voz por API

La síntesis usa ElevenLabs desde el API, con `ELEVENLABS_API_KEY` en el archivo
privado `.env.elevenlabs` (0600), inyectado únicamente en el API. Muse Voice
Transcribe continúa usando Meta. No hay imágenes ni servicios de síntesis local
que construir o activar. Ver [TTS](TTS.md).
