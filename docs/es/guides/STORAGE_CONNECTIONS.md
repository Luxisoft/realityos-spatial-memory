> **Corrección vigente: localhost principal.** Windows/Linux x64 ejecutan PostgreSQL, Redis, API y worker. Meta usa la clave propia del jurado; voz de salida instalada en Android. Gateway, buckets, Facebook, SMTP, scheduler y ElevenLabs están fuera del recorrido local. La configuración remota que aparece en esta guía es histórica. [Instalación vigente](../deployment/DEPLOYMENT_LOCALHOST.md).

# Conectar un bucket y usar sus recursos

[English](../../en/guides/STORAGE_CONNECTIONS.md) · [Proyecto](../README.md) · [API](../api/API.md)

El bucket es una fuente privada de la cuenta. Importar copia el recurso a PostgreSQL BYTEA y lo publica en un grupo al que perteneces. No existe un destino de publicación privado. Consultar no publica la imagen de búsqueda ni enrola caras automáticamente.

## Android

Abre el menú derecho → **Conexiones**, encima de About. Añade R2 o S3, endpoint HTTPS, bucket, región, carpeta y credenciales; selecciona un grupo autorizado. R2 usa región `auto`. Se recomiendan credenciales de lectura/listado; los secretos cifrados nunca se devuelven a la app.

El panel de conexiones sigue el diseño del buscador-chat. Cada fila tiene una miniatura a la derecha; tócala para abrir el visor de imagen/video. Selecciona recursos e impórtalos al grupo. Las importaciones recientes muestran progreso, revisión de duplicados y reintentos.

Editar permite cambiar proveedor, endpoint, bucket, región, carpeta y grupo. El servidor valida la fuente nueva antes de guardarla; si falla, conserva la conexión anterior. Rotar únicamente credenciales conserva las copias.

**Cambiar la fuente o desconectarla retira sus copias importadas comprobadas y las compartidas desde ellas.** Las revisiones impiden que un worker antiguo vuelva a publicarlas. Se conservan expedientes independientes, avatares y referencias biométricas. Esta operación nunca elimina objetos del bucket remoto.

## Sincronización y límites

Guardar una conexión con grupo activa la sincronización inmediatamente y cada **15 minutos**. Se mantienen Actualizar ahora, pausa y otros intervalos. El listado se recorre por páginas. Solo un recorrido completo y correcto retira copias cuyas claves desaparecieron; un error o recorrido incompleto no implica eliminación. La misma fuente/contenido/destino es idempotente.

JPEG, PNG, WebP y MP4 usan el análisis y revisión de duplicados existentes. Video: hasta 120 segundos. Descarga: hasta 64 MiB y los límites configurados del servidor. PDF/DOCX puede reemplazar el CV privado, hasta 10 MiB. La consulta de objetos por imagen espera hasta tres minutos. La búsqueda facial conserva consentimiento y autorización del grupo.

## Servidor y API

`/v1/me/storage-connections` incluye CRUD, test, objects, content, imports/retry, syncs/run y CV. Consulta el [contrato generado](../api/API_REFERENCE.md). Postman conserva **Server requests** y **Localhost requests**, con variables independientes.

Mantén estable `STORAGE_ENCRYPTION_KEY` en el runtime privado y compartida por API y worker. El scheduler emite trabajos y el worker los procesa. Se vuelve a comprobar pertenencia y revisión de conexión antes de descargar y publicar. Se mantienen validación HTTPS/dirección pública, IP fijada, TLS y rechazo de redirecciones.

## Recursos de evaluación local

La evaluación local inicializa las tablas de la aplicación mediante SQL versionado en `simulator/database/` e importa los originales de `simulator/media/` a PostgreSQL BYTEA. Las fuentes, licencias, hashes y rutas de recursos se conservan en `simulator/media/manifest.csv` como procedencia. No constituyen otra base de publicaciones.

El runtime local no utiliza buckets ni importaciones remotas. Sus dos grupos contienen 25 publicaciones. Los ejemplos Postman consultan una base desechable inicializada con el mismo SQL; las comprobaciones de reproducción, rangos y permisos se describen en [evaluación de videos](../testing/VIDEO_EVALUATION.md).

La integración de almacenamiento pertenece al servidor. Su evidencia histórica está fechada en el [estado de implementación](../project/IMPLEMENTATION_STATUS.md); la preparación local no modifica fuentes remotas ni datos del servidor.
