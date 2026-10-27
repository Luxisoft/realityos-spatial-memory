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
workflow prueba el código, publica imágenes inmutables en GHCR, despliega el
gateway en FRONTEND y solo después actualiza API y worker. Configure el
Environment protegido `production` con los secretos indicados en
[Gateway](GATEWAY.md). Los secretos no se almacenan en Git ni en archivos del
repositorio.

Antes del primer merge de despliegue, cree el registro DNS `A` de
`meta.luxisoft.com` apuntando a `198.252.105.131`. El workflow valida Docker,
Nginx, TLS, el catálogo de modelos de Meta y la salud de RealityOS. Si FRONTEND
no devuelve `muse-spark-1.3`, el workflow falla sin activar Live en RealityOS.

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
