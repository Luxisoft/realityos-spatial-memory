# Catálogos, clasificación y filtros de publicaciones

[English](../../en/guides/PUBLICATION_CLASSIFICATION.md) · [Proyecto](../README.md) · [API](../api/API.md)

## Catálogo de cada grupo

El dueño del grupo añade categorías y tags al crearlo, y puede renombrarlos, archivarlos o restaurarlos en Administrar grupo. Los demás miembros pueden consultarlos y seleccionarlos, sin modificar el catálogo. Los valores tienen identificadores propios de su grupo; un nombre coincidente en otro grupo no comparte permisos ni identidad.

Publicar exige una categoría y entre uno y veinte tags activos del grupo seleccionado. La nota escrita o transcrita sigue siendo opcional. Si cambia el grupo, hay que volver a elegir la clasificación. Un catálogo vacío bloquea la publicación y señala que debe completarlo el dueño.

Los nombres se muestran como los escribe el dueño; los controles están disponibles en español e inglés. Renombrar conserva las asociaciones. Archivar conserva las etiquetas de publicaciones anteriores y las opciones históricas del filtro, pero impide nuevas selecciones. La clasificación manual no se convierte en evidencia visual ni sustituye al análisis de objetos.

## Miniaturas y búsqueda

La miniatura muestra la categoría y hasta dos tags, con `+N` para los restantes. El visor muestra la clasificación completa. Los videos llevan un icono de reproducción. La antigua etiqueta de procedencia «MEDIA/Archivo» desaparece; la procedencia se conserva internamente.

El botón de filtro contiene solo el icono y una descripción para accesibilidad. Su desplegable permite elegir categorías, tags y autores; fechas Desde/Hasta; y texto en descripción o nota. Aplicar reinicia la paginación; Limpiar elimina los criterios. Cambiar de grupo limpia los filtros; abrir y cerrar el visor los conserva.

Los distintos criterios se combinan con AND; varias selecciones dentro de un criterio se combinan con OR. Las fechas abarcan días completos en la zona horaria del teléfono. Las opciones y los resultados proceden de todo el contenido autorizado, no solo de las miniaturas ya descargadas.

## API

Todas las rutas requieren autenticación y comprueban el grupo correspondiente.

| Operación | Contrato |
| --- | --- |
| Consultar catálogo | `GET /v1/groups/{workspace_id}/publication-catalog` devuelve `categories`, `tags` y `can_manage`. |
| Crear valor | `POST /v1/groups/{workspace_id}/publication-catalog/{kind}`, con `kind=category` o `tag` y `{"name":"Instrumental clínico"}`. Solo el dueño. |
| Renombrar/archivar/restaurar | `PATCH /v1/groups/{workspace_id}/publication-catalog/{term_id}`, con `name` y `active`. Solo el dueño. |
| Publicar o subir | Añadir `category_id` y `tag_ids`. En JSON, `tag_ids` es un array de UUID; en multipart, es un campo de texto que contiene ese array JSON. |
| Corregir publicación | `PATCH /v1/gallery/{post_id}/classification`, con `category_id` y `tag_ids`. Solo el autor. |
| Opciones del filtro | `GET /v1/gallery/filter-options`, con `workspace_id` opcional. Devuelve únicamente valores y autores de publicaciones visibles. |
| Consultar publicaciones | `GET /v1/gallery/page`, con `category_ids`, `tag_ids`, `owner_ids` repetibles, `published_from`, `published_before` y `description_q`, además del grupo y cursor. |

`published_from` es inclusivo y `published_before` exclusivo; ambos requieren zona horaria. El teléfono convierte Hasta al inicio del día siguiente. El texto ignora mayúsculas y trata `%` y `_` como caracteres literales.

Copiar mediante `/v1/groups/{workspace_id}/publications/import` recibe `publication_ids` y un objeto `classifications` indexado por ID de publicación. Cada entrada contiene `category_id` y `tag_ids` del grupo de destino. La app permite asignarlos individualmente o aplicar una selección al lote. Se conservan los originales compartidos y las interacciones independientes.

## Importaciones y sincronización

`POST /v1/me/storage-connections/{connection_id}/imports` acepta `classifications` indexado por clave de archivo. Una entrada con clasificación válida continúa al procesamiento. Un archivo sin clasificación queda en `awaiting_classification`, con originales privados en BYTEA y sin publicación visible.

La sincronización de la carpeta cada 15 minutos utiliza este mismo estado para archivos nuevos. En Conexiones, el propietario revisa la vista previa y selecciona la clasificación. La API equivalente es `POST /v1/me/publication-uploads/{upload_id}/classify`, con `category_id` y `tag_ids`. Después continúa el análisis y, si corresponde, la confirmación de duplicados.

Reintentar o volver a sincronizar no aprueba candidatos pendientes. Se comprueban de nuevo propietario, membresía, catálogo y vigencia de la fuente. Desconectar o cambiar la fuente cancela sus candidatos y conserva las reglas de retiro existentes, sin borrar objetos remotos.

## Clasificación de publicaciones existentes

El manifiesto `simulator/real-scenes/publication-classification.json` asigna valores a las 48 publicaciones existentes revisadas, vinculadas a sus hashes originales y grupos actuales. No incluye medios privados ni crea grupos.

`scripts/classify_existing_publications.py` verifica el manifiesto sin escribir por defecto. `--apply` aplica la revisión y guarda un diario privado; repetir una asignación idéntica no la duplica. `--rollback --journal RUTA` comprueba una reversión y, con `--apply`, restaura la clasificación anterior, siempre que no haya cambios posteriores. Conserva bytes, fechas, descripciones e interacciones. El estado de despliegue y las pruebas ejecutadas se documentan en [Estado de implementación](../project/IMPLEMENTATION_STATUS.md).
