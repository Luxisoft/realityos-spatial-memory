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

## Escenas de evaluación con licencia

`simulator/real-scenes/catalog.json` y `manifest.json` describen **48 recursos con licencia**: 12 fotos y cuatro grabaciones con movimiento para seguridad, enfermería y memoria, respectivamente. Los videos duran 10–15 segundos, a 24 fps y al menos 720p; se comprueba cambio entre fotogramas. Las cuentas y roles son ficticios. El manifiesto contiene fuentes, licencias, hashes y métricas. Los archivos descargados están excluidos de Git.

`scripts/prepare_real_scenes.py` prepara y valida los recursos. `scripts/prepare_bucket_demo.py --upload --credentials-file /private/r2.json` sube y vuelve a descargar cada objeto para comprobar SHA-256. Incluye 48 escenas y seis pruebas QA separadas. El archivo privado contiene endpoint, bucket, region, access_key y secret_key; no se publica.

Las carpetas `demo/v2/{scenario}/{username}/` distribuyen recursos distintos por autor. QA conserva `demo/v1/qa/`. `scripts/connect_demo_buckets.py --apply --read-credentials-file /private/r2.json` configura las nueve cuentas de escenarios y cuatro QA existentes, sin crear cuentas o membresías. Valida cada fuente antes de retirar copias anteriores. Se desactiva la antigua conexión de exploración del directorio social, conservando sus objetos remotos.

`scripts/refresh_demo_gallery.py --apply --journal /private/demo-visibility.json` sustituye solo publicaciones antiguas identificadas como demo, conservando expedientes y retratos biométricos. El diario permite `--rollback`. La indexación usa el proveedor real configurado; el manifiesto no inventa detecciones.

Consulta las comprobaciones R2/API ejecutadas en el [estado de implementación](../project/IMPLEMENTATION_STATUS.md). La aceptación en teléfono y gafas requiere evidencia del dispositivo.
