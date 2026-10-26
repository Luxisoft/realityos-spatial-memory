# Despliegue en Ubuntu

1. Instale Docker Engine y Compose v2, clone el repositorio y copie .env.example
   a .env.
2. Cambie POSTGRES_PASSWORD, JWT_SECRET y la credencial demo. Mantenga
   META_MODE=mock hasta disponer de una clave Meta con Muse Spark/SAM habilitado.
3. Ejecute docker compose --env-file .env -f infrastructure/docker-compose.yml up --build.
4. El proxy queda en HTTP_PORT, 8090 por defecto. Para producción ubique un
   proxy TLS administrado delante, configure dominio y exponga solo 443/80.
5. Cree backups con scripts/backup-postgres.sh y pruebe pg_restore.

API y worker no exponen PostgreSQL ni Redis al host; los volúmenes persistentes
son postgres_data y redis_data. Solo API, worker y proxy se unen a la red de
egress: API/worker la necesitan para Meta y proxy la necesita para publicar el
puerto HTTP. Restrinja CORS a dominios reales antes de producción.
