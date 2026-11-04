[English](../../en/guides/DEMO.md) · [Índice](../INDEX.md)

# Evaluación local y recursos de prueba

Los registros de cuentas, grupos, perfiles, expedientes, publicaciones, clasificación y traducciones residen en PostgreSQL. `simulator/database/` contiene únicamente SQL de instalación: se aplica una vez en la misma transacción que importa los originales y registra la revisión. API, Android y worker consultan las tablas de la aplicación.

`simulator/media/` conserva los archivos originales para pruebas locales:

- `memory/`: escenas, expedientes y recursos de cuentas de Memory.
- `police/`: dieciséis retratos de expedientes, recursos de cuentas y tres videos de parques.
- `meta-social/`: avatares, referencias privadas de los perfiles sintéticos autorizados y tres videos de espacios públicos.
- `shared/`: avatares compartidos de los escenarios.
- `regression/`: imágenes de consulta, documentos y recursos históricos de pruebas; no se publican ni se importan como escenarios.

`media/manifest.csv` conserva ruta, SHA-256, fuente, licencia y disponibilidad de cada archivo. `repository` identifica archivos entregados con el repositorio; `local-only` identifica generaciones previas conservadas únicamente en este checkout. El inventario es técnico y no contiene registros de publicaciones o perfiles.

<a id="access"></a>

El inicio local mediante `make local-start` o el lanzador PowerShell prepara el esquema y ejecuta el único inicializador. Los originales se almacenan en BYTEA. Un reinicio consulta los comprobantes de instalación y conserva ediciones, eliminaciones, membresías y revocaciones de consentimiento. No hay sincronización de los archivos de instalación con los registros del usuario. Android Debug y Postman permiten seleccionar las nueve cuentas locales sin contraseñas; el servidor no expone este acceso.

<a id="video"></a>

Los videos se publican mediante las mismas tablas y rutas de medios que las imágenes. Las consultas utilizan la evidencia indexada; no crean resultados anticipados ni autorizaciones biométricas. Las preguntas de validación están documentadas en [evaluación de video](../testing/VIDEO_EVALUATION.md).

La revisión SQL `004-group-videos.sql` añade los seis videos solicitados una vez, sin reemplazar los expedientes ni las presentaciones existentes:

| Grupo | Videos de Pexels |
| --- | --- |
| Policial | [Ibirapuera, 25757454](https://www.pexels.com/video/pessoas-caminhando-e-pedalando-no-parque-do-ibirapuera-25757454/), [parque en día nublado, 29401365](https://www.pexels.com/video/busy-park-walkway-on-an-overcast-day-29401365/), [Edimburgo, 30614848](https://www.pexels.com/video/busy-park-pathway-in-edinburgh-during-spring-30614848/) |
| Meta Social Media | [acera urbana, 33802407](https://www.pexels.com/video/busy-city-sidewalk-with-people-walking-33802407/), [parque arbolado, 12557513](https://www.pexels.com/video/park-with-trees-and-pedestrians-12557513/), [parque en invierno, 3699519](https://www.pexels.com/video/people-spending-their-day-enjoying-the-park-in-winter-season-3699519/) |

Los MP4 se entregan mediante Git LFS, sin transcodificar. El propietario proporcionó el archivo 29401365 mediante Drive cuando Pexels rechazó la descarga directa; su procedencia queda registrada junto con su hash. Las instalaciones nuevas tienen 41 publicaciones: 19 en Policial, 6 en Meta Social Media y 16 en Memoria. La revisión `005-police-records.sql` añade los expedientes 11 y 12 con orden de arresto y del 13 al 16 como personas desaparecidas con orden de búsqueda. Cada uno comparte su retrato original con su publicación vinculada. Una actualización respeta grupos y membresías eliminados; no los recrea para insertar contenido.

Las referencias privadas nunca son publicaciones ni miniaturas públicas. Los datos internos de simulación y la procedencia se conservan. Los recursos históricos no recrean Hospital, Workshop ni otros grupos retirados.

<a id="handoff"></a>

Las revisiones nuevas de datos deben ser explícitas, transaccionales y tener pruebas de actualización y reinicio. No se deben añadir catálogos JSON, generadores de usuarios alternativos ni copias de registros en código. La entrega incluye la [colección Postman](../../postman/RealityOS.postman_collection.json) y el APK Debug canónico indicado en el README.
