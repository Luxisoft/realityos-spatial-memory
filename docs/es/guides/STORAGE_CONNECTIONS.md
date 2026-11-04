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

`simulator/real-scenes/catalog.json` y `manifest.json` describen 36 fotos conservadas y 12 videos completos: cuatro por cada grupo existente de seguridad, enfermería y memoria. Las grabaciones mantienen su duración original (7–29 segundos) y al menos 720p nativos. Fuentes, autores, licencias y hashes permiten verificar su procedencia; los archivos descargados están excluidos de Git.

La [matriz de videos](../testing/VIDEO_EVALUATION.md) contiene las consultas ES/EN y los intervalos esperados. `scripts/prepare_evaluation_videos.py` prepara únicamente los videos y reutiliza los bytes ya verificados. `scripts/renew_evaluation_videos.py` administra inventario, carga, análisis real, aceptación, activación y reversión con un diario privado. No vuelve a crear cuentas, grupos ni expedientes.

La sincronización selecciona `demo/v2/{scenario}/{username}/evaluation-v3/` en las nueve conexiones existentes, cada 15 minutos. Las 36 fotos mantienen sus identificadores. Por petición expresa del propietario se eliminaron los videos sustituidos, el candidato descartado y 96 copias remotas obsoletas, incluida `evaluation-v2-rollback/`. La generación activa conserva sus 48 escenas. QA permanece en `demo/v1/qa/`.

Mantén seleccionada únicamente la carpeta activa; los preparadores anteriores rechazan la renovación versionada. `scripts/prepare_bucket_demo.py` respeta ahora la carpeta y el propietario explícitos del manifiesto. Las claves de escritura/lectura permanecen en archivos privados y no se incluyen en Postman.

Consulta las comprobaciones R2/API ejecutadas en el [estado de implementación](../project/IMPLEMENTATION_STATUS.md). La aceptación en teléfono y gafas requiere evidencia del dispositivo.
