[English](../../en/project/IMPLEMENTATION_STATUS.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Estado vigente de implementación

Actualizado el **4 de noviembre de 2026**. Este documento describe el código y las comprobaciones indicadas; no certifica el estado de servicios productivos. Las entregas anteriores permanecen en Git.

## Reorganización de arquitectura

El backend comparte modelos y servicios entre API y worker, con composiciones explícitas local/server. Se retiró la selección de rutas por fragmentos de URL. El worker local excluye importadores remotos y programación de tareas de buckets. La configuración no lee `.env` automáticamente; los archivos privados se seleccionan explícitamente. La imagen `server` excluye datos y medios de instalación local.

PostgreSQL es la fuente única de cuentas, permisos, expedientes, publicaciones, clasificación y textos guardados. Los antiguos catálogos de negocio JSON y sus cargadores paralelos se retiraron. La instalación consume `simulator/database/*.sql` y recursos de `simulator/media/`, con [manifiesto de procedencia y hashes](../../../simulator/media/manifest.csv). El acceso operativo consulta la BD; los recibos versionados conservan ediciones y eliminaciones al reiniciar.

La base vacía dispone de un snapshot SQL inmutable de `20261104_0040`; después se aplica Alembic hasta `head`, actualmente `20261104_0041` en el código. Se preservaron las migraciones históricas y se rechazan bases no vacías sin versión. La inicialización y actualización del esquema se validaron en PostgreSQL efímero aislado, sin usar servicios ni datos productivos.

Los servicios de procesamiento, consultas de galería, clasificación y permisos ya no importan handlers HTTP. El checker de arquitectura inspecciona dependencias mediante AST y detecta regresiones hacia catálogos JSON. El código biométrico protegido conserva sus interfaces y controles.

## Evaluación local

Localhost es el PC Windows/Linux del jurado: PostgreSQL, Redis, API y worker. Meta mantiene llamadas reales directas con la clave privada del jurado; Android usa voces instaladas sin conexión. El servidor RealityOS y el gateway FRONTEND son destinos separados. No se desplegó ni se reinició ninguno como parte de estas comprobaciones.

Los datos preparados incluyen dos grupos y seis cuentas de acceso. Policía tiene 16 expedientes de personas ficticias con publicaciones de retratos vinculadas, además de tres videos. Cinco tienen orden de captura vigente y dos de ellas tienen procesos activos; cuatro expedientes independientes de personas desaparecidas tienen órdenes de búsqueda vigentes, sin captura ni antecedentes. Meta Social Media incorpora tres presentaciones mediante avatares separados, tres videos y trece perfiles sintéticos con tres referencias privadas cada uno. La galería local compartida contiene 25 publicaciones en total (Policía 19, Meta Social Media 6). Los perfiles adicionales no son cuentas seleccionables. No se publica ninguna referencia biométrica ni se omiten consentimientos.

El retiro local elimina el acceso y contenido exclusivo de Sonoran/Memory de las bases existentes, conservando dependencias compartidas y protegidas. Se retiraron sus cuentas locales, medios preparados y la ruta/interfaz clínica de comparación. Se conservan expedientes genéricos de persona/caso/evento/objeto, historial, permisos y búsqueda. Enfermería y Memoria permanecen como ejemplos conceptuales al final de los README.

Postman mantiene Localhost requests y Server requests. Los ejemplos locales se derivan de la BD inicializada; Server requests permanece deshabilitado y sin URL activa ni credenciales. Las antiguas autorizaciones para contraseñas de prueba no se aplican a nuevas exportaciones.

## Filtros y clasificación de publicaciones

Los filtros aplican cada cambio válido de categoría, etiqueta, autor, fecha o
texto, sin botón Aplicar. Limpiar comparte la fila del título y mantiene abierto
el menú. Los intervalos inválidos conservan la última consulta válida; cambiar
filtros o grupo descarta respuestas y cursores anteriores. Seleccionar otra vez
el grupo actual conserva sus resultados y filtrar no recarga la lista de grupos.

La revisión SQL `shared-publication-classification-v1` clasifica las 25
publicaciones existentes: Police tiene cinco órdenes de captura, cuatro personas
desaparecidas, siete casos sin órdenes ni antecedentes y tres videos; Meta tiene
tres presentaciones y tres videos. Las etiquetas distinguen procesos activos,
búsqueda, ausencia de captura y temas del contenido. Son 26 términos activos y
10 anteriores archivados en una instalación nueva. La actualización respeta
ediciones, eliminaciones, permisos, estados desconocidos y cargas pendientes;
no cambia medios ni referencias privadas. Se aplica en localhost mediante el
inicio habitual después de actualizar el repositorio.

Pasaron **101 pruebas distintas**: 21 regresiones nuevas de clasificación en
SQLite y PostgreSQL aislado (119,33 segundos) y 80 comprobaciones anteriores de
datos locales y API (226,88 segundos), sin fallos ni omisiones. Cubren los filtros
por API, conservación de cambios, permisos y rollback. También pasaron
`make lint`, `make architecture-check`, `make docs-check` y el formato de los
archivos Python modificados. No se modificaron datos ni servicios productivos.

## Base de validación y comprobaciones anteriores

- La entrega anterior de arquitectura aprobó la suite completa de backend/gateway: **660 pruebas** en 571,01 segundos, sin fallos ni omisiones. Incluye contratos API, permisos, aislamiento por grupo, instalación de esquema, retiro local, revisiones aditivas, rollback y conservación de ediciones, eliminaciones y consentimientos. Esta cifra no representa una repetición de la suite completa en la revisión de filtros.
- Una instalación local nueva tiene 25 publicaciones, 28 medios base, 16 expedientes y 16 adjuntos. La inicialización social añade trece perfiles, trece avatares separados y treinta y nueve referencias privadas: 80 medios y 19 usuarios en total, con solo seis cuentas en el selector. Policía conserva cinco órdenes de captura, dos procesos activos y cuatro órdenes independientes de búsqueda por desaparición.
- El inventario de medios tiene 423 entradas verificadas: 132 recursos del repositorio y 291 solo locales. Se retiraron 34 archivos exclusivos de Memory y su recibo QA de video obsoleto. Doce imágenes Meta nuevas se comprobaron con InsightFace local ya disponible: una cara por avatar/referencia y las nueve referencias privadas dentro de los requisitos de calidad. Es validación de recursos, no una afirmación de precisión representativa ni de integración real con Facebook.
- Pasaron `make lint`, `make architecture-check` y `make docs-check`. La documentación cubre 74 archivos Markdown y 352 peticiones Postman, incluidas 23 de escenarios locales y 71 guardas de escritura de referencia. Newman verificó 168 escrituras deshabilitadas, dos secuencias de login/refresh, nueve errores de autenticación previstos y códigos exactos, usando únicamente mocks HTTP locales.
- El fallo del CI anterior se debía a rutas de sockets Unix de PostgreSQL que excedían el límite de Linux en el checkout largo de GitHub. El helper de pruebas ahora crea rutas cortas de sockets y mantiene los archivos de la base en `.runtime`; cuatro casos PostgreSQL pasaron con ese helper. No se utilizó ninguna base ni servicio productivo.

## Validación Android

La revisión de filtros aprobó **26 pruebas focalizadas**: nueve de controles y
fechas, dos de integración de galería con respuestas HTTP retenidas, siete de
paginación y ocho de repositorios. No hubo fallos, errores ni omisiones. Se
revisaron renderizados ES/EN a 320–480 dp, incluido texto al 200 %. El panel
conserva el tema y sus controles compartidos. No se realizó validación en
teléfono físico ni emulador real para esta revisión.

El build final de filtros pasó `ktlintCheck`, `lintDebug`, `assembleDebug`,
`assembleRelease` y `compileDebugAndroidTestKotlin`. Lint mantiene cero errores,
100 advertencias y 10 sugerencias, sin advertencias nuevas.

La revisión anterior de logos aprobó **31 pruebas existentes focalizadas** de acceso, formularios de cuenta y navegación/perfil, más una comprobación temporal del splash nativo: 32 resultados, sin fallos, errores ni omisiones. Pasaron `ktlintCheck`, `assembleDebug`, `assembleRelease` y `compileDebugAndroidTestKotlin`. `lintDebug` completo informó cero errores, 100 advertencias y 10 sugerencias; las dos advertencias adicionales `VectorPath` corresponden al texto vectorial del splash. Estas ejecuciones focalizadas no suponen repetir la suite Android anterior de 313 pruebas.

Se revisaron renderizados nativos del splash en ES a 320 dp/texto 200%, EN a 390 dp y EN a 480 dp/200%. El archivo proporcionado `splash_logo.png` permanece intacto sobre el fondo oscuro existente, con `REALITYOS` y `BY JOSE MARIN` debajo. Las cabeceras de acceso/cuenta y el menú lateral comparten `AppBrandIcon`, que muestra el archivo existente `icon_app.png` con recorte completamente circular. Los renderizados Compose revisados cubrieron acceso EN a 390 dp, inicio de sesión ES a 320 dp/200% y menú lateral ES a 320 dp/200%. Se retiraron los logos sustituidos y sus comprobaciones obsoletas. Se conservaron el icono del lanzador, los colores internos de vistas/botones y el código biométrico. No se realizó validación con teléfono físico ni emulador real para esta revisión.

El [APK Debug canónico](../../../android/app/build/outputs/apk/debug/app-debug.apk), versión `0.1.6-debug-20261104-1212`, tiene SHA-256 `94592ebc27bcbb354a38b917862048c789cee1621c5b9de9541050f32c348e73` y conserva el certificado de firma existente. Los recursos de splash, icono y tema permanecen iguales a la revisión de logos. El APK se mantiene como artefacto de entrega del repositorio.

<a id="next-steps"></a>

## Aceptación pendiente

| Área | Evidencia necesaria |
| --- | --- |
| Android/dispositivo | Comprobación en teléfono y gafas físicos, incluida carga real de medios e interacciones. Los estados renderizados de Robolectric no sustituyen la validación en dispositivos. |
| Instalación completa | Primer inicio real en Windows/Linux con Docker, incluyendo descarga de imágenes y modelos; el test PostgreSQL aislado no valida ese recorrido. |
| Integraciones externas | Facebook Live, Meta real, DAT/gafas, correo y voz remota necesitan sus comprobaciones propias. |
| Derechos y entrega | Términos DAT autenticados, constancia de derechos de `buffalo_l` y grabación/recibo final según [Terceros](THIRD_PARTY.md) y [Hackathon](HACKATHON.md). |

[Arquitectura](../architecture/ARCHITECTURE.md) · [Datos](../architecture/DATABASE.md) · [Checklist](../testing/IMPLEMENTATION_CHECKLIST.md)
