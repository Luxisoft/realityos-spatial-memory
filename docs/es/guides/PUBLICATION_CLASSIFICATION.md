# Catálogos, clasificación y filtros de publicaciones

[English](../../en/guides/PUBLICATION_CLASSIFICATION.md) · [Proyecto](../README.md) · [API](../api/API.md)

## Catálogo de cada grupo

El dueño del grupo añade categorías y etiquetas al crearlo, y puede renombrarlas, archivarlas o restaurarlas en Administrar grupo. Los demás miembros pueden consultarlas y seleccionarlas, sin modificar el catálogo. Los valores tienen identificadores propios de su grupo; un nombre coincidente en otro grupo no comparte permisos ni identidad.

Publicar exige una categoría y entre una y veinte etiquetas activas del grupo seleccionado. La nota escrita o transcrita sigue siendo opcional. Si cambia el grupo, hay que volver a elegir la clasificación. Un catálogo vacío bloquea la publicación y señala que debe completarlo el dueño.

Las categorías y etiquetas de los dos grupos locales tienen nombres redactados y guardados en español e inglés. Categorías, etiquetas, miniaturas, filtros y visor leen la versión del idioma seleccionado sin traducir al abrir la pantalla. Los identificadores y asociaciones permanecen iguales. Las publicaciones, los expedientes y los textos descriptivos de los perfiles preparados también conservan ambas versiones en la base de datos.

La copia revisada y las asociaciones de clasificación están en el SQL versionado de `simulator/database/` y se incorporan una sola vez, sin recrear filas borradas ni sustituir ediciones del propietario. No hay un nuevo servicio, modelo, cola ni traductor automático. Los nombres propios, identificadores y fechas no se traducen. Una edición posterior conserva el texto del dueño y deja de mostrar una versión antigua que ya no corresponde. Archivar conserva las etiquetas de publicaciones anteriores y las opciones históricas del filtro, pero impide nuevas selecciones. La clasificación manual no se convierte en evidencia visual ni sustituye al análisis de objetos.

## Miniaturas y búsqueda

La miniatura muestra la categoría y hasta dos etiquetas, con `+N` para las restantes. El visor muestra la clasificación completa. Los videos llevan un icono de reproducción. La antigua etiqueta de procedencia «MEDIA/Archivo» desaparece; la procedencia se conserva internamente.

El botón de filtro contiene solo el icono y una descripción para accesibilidad. Su desplegable permite elegir categorías, etiquetas y autores; fechas Desde/Hasta; y texto en descripción o nota. Cada cambio válido aplica el filtro inmediatamente y reinicia la paginación, manteniendo abierto el menú. Limpiar es un botón de texto en la fila del título y elimina los criterios. No hay botón Aplicar. Cambiar de grupo limpia los filtros; abrir y cerrar el visor los conserva.

Los distintos criterios se combinan con AND; varias selecciones dentro de un criterio se combinan con OR. Las fechas abarcan días completos en la zona horaria del teléfono. Las opciones y los resultados proceden de todo el contenido autorizado, no solo de las miniaturas ya descargadas.

## API

Todas las rutas requieren autenticación y comprueban el grupo correspondiente.

| Operación | Contrato |
| --- | --- |
| Consultar catálogo | `GET /v1/groups/{workspace_id}/publication-catalog` devuelve `categories`, `tags` y `can_manage`. |
| Crear valor | `POST /v1/groups/{workspace_id}/publication-catalog/{kind}`, con `kind=category` o `tag` y `{"name":"Espacios públicos"}`. Solo el dueño. |
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

## Inicialización local y cambios posteriores

El SQL compartido instala los catálogos de los dos grupos y clasifica las 25 publicaciones preparadas en las mismas tablas que usan las cargas y consultas normales. No existe otro manifiesto de clasificación ni otra base de publicaciones. Los recibos de instalación impiden que un reinicio recree filas eliminadas o reemplace ediciones del dueño.

Las correcciones posteriores usan las APIs autenticadas de catálogo y clasificación descritas arriba. Conservan los medios originales y comprueban propiedad del grupo, membresía y autoría. La importación y sincronización de almacenamiento solo están disponibles en la composición del servidor; la evaluación local importa los bytes organizados directamente a BYTEA.


## Clasificación preparada de Police y Meta

La revisión [010-use-case-classification.sql](../../../simulator/database/010-use-case-classification.sql) reemplaza la clasificación anterior por temas de la escena con las categorías y etiquetas por caso de uso aprobadas por el propietario. Cada grupo tiene sus propios términos bilingües.

| Grupo | Categoría | Publicaciones | Etiquetas complementarias |
| --- | --- | --- | --- |
| Police | Órdenes de captura vigentes | 5 | Orden de captura vigente; Sin antecedentes registrados; Proceso judicial activo en 2, Sin procesos activos en 3. |
| Police | Personas desaparecidas | 4 | Orden de búsqueda vigente; Sin órdenes de captura; Sin procesos activos; Sin antecedentes registrados. |
| Police | Sin órdenes ni antecedentes | 7 | Sin órdenes de captura; Sin procesos activos; Sin antecedentes registrados. |
| Police | Material audiovisual | 3 | Video de observación. |
| Meta Social Media | Presentaciones | 3 | Presentación personal; Comunidad. |
| Meta Social Media | Contenido social | 3 | Video; Vida cotidiana. |

Los 16 expedientes no tienen condenas ni antecedentes penales registrados. Una orden de captura no implica condena. La categoría «Sin órdenes ni antecedentes» reúne los siete expedientes que además no tienen orden de captura, búsqueda ni proceso activo. Los cuatro expedientes de personas desaparecidas tienen órdenes de búsqueda, separadas de las órdenes de captura. El filtro Sin órdenes de captura devuelve 11 retratos; Sin procesos activos, 14; Proceso judicial activo, 2; Orden de búsqueda vigente, 4.

Las etiquetas de video describen su función dentro del caso de uso. No identifican personas ni les atribuyen antecedentes, órdenes, procesos, incidentes o resultados de análisis. Los temas de paisaje, como estaciones, clima, parques, caminata o ciclismo, dejan de ser etiquetas de la clasificación preparada. Los 13 perfiles privados de Meta y sus referencias siguen fuera de las publicaciones.

La revisión se instala una vez mediante el cargador SQL compartido y su recibo `use-case-publication-classification-v1`, después de la revisión 008. Solo corrige publicaciones preparadas cuya categoría, etiquetas, texto y hechos pertinentes siguen intactos, con autor activo y membresía vigente. Conserva clasificaciones manuales, vocabularios renombrados o archivados, publicaciones ocultas, borrados, grupos retirados y estados desconocidos. No repone filas ni modifica los medios. Los términos equivalentes ya creados por el dueño se reutilizan sin sobrescribirlos.

Una instalación nueva queda con 17 términos activos: cuatro categorías y siete etiquetas de Police, dos categorías y cuatro etiquetas de Meta. Se retiran las asociaciones preparadas anteriores antes de archivar los términos sin uso, para que dejen de aparecer en los filtros de publicaciones. En instalaciones editadas, un término anterior continúa activo si todavía clasifica otra publicación o figura en una carga pendiente; tampoco se archiva un término renombrado por el dueño. Un reinicio no vuelve a aplicar la revisión.

### Instalaciones anteriores al cargador SQL

Las versiones anteriores creaban los identificadores del catálogo al instalarlo
y guardaban algunas referencias de procedencia sin el prefijo del grupo.
Las revisiones 008 y 010 esperaban los identificadores y referencias exportados
en el SQL y podían omitir esos expedientes aunque registraran la actualización como ejecutada. El
síntoma reproducido es conservar «Información del expediente» junto a «Video de
observación», sin las etiquetas judiciales; las presentaciones de Meta también
podían conservar su clasificación anterior.

La revisión [011-legacy-classification-repair.sql](../../../simulator/database/011-legacy-classification-repair.sql), con recibo
`legacy-publication-classification-repair-v1`, corrige esas instalaciones una sola
vez. Reconoce el vocabulario anterior por grupo y contenido original, valida la
procedencia y los vínculos de las publicaciones, y conserva los identificadores
existentes. Aplica los mismos 17 términos aprobados y respeta las ediciones,
eliminaciones y permisos. Se ejecuta con el inicio local habitual después de
actualizar el repositorio; no requiere borrar la base ni los recibos anteriores.
