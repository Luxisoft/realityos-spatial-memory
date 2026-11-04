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

La revisión SQL `use-case-publication-classification-v1` clasifica las 25
publicaciones existentes: Police tiene cinco órdenes de captura, cuatro personas
desaparecidas, siete casos sin órdenes ni antecedentes y tres videos; Meta tiene
tres presentaciones y tres videos. Las etiquetas distinguen procesos activos,
búsqueda, ausencia de captura y antecedentes registrados. Los videos no tienen
etiquetas de estado judicial. Meta utiliza presentación personal/comunidad o
video/vida cotidiana. Una instalación nueva tiene 17 términos activos, sin las
anteriores etiquetas sobre temas de la escena. La actualización respeta
ediciones, eliminaciones, permisos, estados desconocidos y cargas pendientes;
no cambia medios ni referencias privadas. Se aplica en localhost mediante el
inicio habitual después de actualizar el repositorio.

La taxonomía aprobada pasó **54 pruebas distintas**: 18 casos nuevos de migración
en SQLite y PostgreSQL aislado, dos pruebas nuevas de API para los términos ES/EN
exactos, conteos de filtros y aislamiento por membresía, y 34 comprobaciones
existentes de consumidores y migraciones anteriores. Las bases nuevas y
actualizadas conservan 25 publicaciones, 28 medios base y 16 expedientes.
La migración retira asociaciones obsoletas, conserva cambios manuales y cargas
pendientes, revierte completamente ante fallos y no requiere los archivos de
instalación en reinicios posteriores.

La incidencia posterior con «Información del expediente» y «Video de observación»
reveló un caso que esas pruebas no cubrían: instalaciones anteriores al cargador
SQL generaban UUID distintos para el catálogo y conservaban referencias de
procedencia antiguas. Se reprodujo el resultado exacto con el inicializador real.
La revisión adicional `legacy-publication-classification-repair-v1` reconoce ese
estado y aplica la misma clasificación aprobada, incluso cuando ya existen los
recibos 008 y 010. Conserva los identificadores existentes, los medios, los textos
y las ediciones; las asociaciones se verifican por grupo y procedencia.

La reparación aprobó **38 pruebas distintas**: 16 casos de datos en SQLite y
PostgreSQL, dos pruebas API del fallo reproducido, dos pruebas API de instalación
nueva y 18 regresiones de la revisión 010. Cubren las siete etiquetas de Police y
las cuatro de Meta, sus categorías y conteos ES/EN, medios reutilizados,
actualizaciones parciales, historial manual, aislamiento, rollback y reinicio.
Pasaron formato, lint, arquitectura y documentación. Esta corrección no cambia
Android ni el contrato API; el APK canónico conserva la versión indicada abajo.

La revisión anterior de clasificación aprobó **101 pruebas distintas**: 21 regresiones nuevas en
SQLite y PostgreSQL aislado (119,33 segundos) y 80 comprobaciones anteriores de
datos locales y API (226,88 segundos), sin fallos ni omisiones. Cubren los filtros
por API, conservación de cambios, permisos y rollback. También pasaron
`make lint`, `make architecture-check`, `make docs-check` y el formato de los
archivos Python modificados. No se modificaron datos ni servicios productivos.

## Revisión de textos en español e inglés

Android utiliza el idioma seleccionado en la app para los errores habituales de
red, controles de medios, etiquetas de accesibilidad, fechas, campos de perfil
de solo lectura y estados de la vista previa local. Los campos editables del
perfil conservan sus valores originales. Los textos de publicaciones y conexiones
reflejan la galería por grupos y las reglas actuales de retiro de fuentes. La
edad de un año utiliza el recurso singular correspondiente.

Android y Postman envían `Accept-Language` de forma uniforme, incluida la
renovación automática de autenticación. Los errores de API y las páginas de
acciones por correo traducen los mensajes propios de RealityOS, conservando los
códigos de estado, estructura de respuesta, cabeceras de seguridad y diagnósticos
de proveedores externos. El gateway restringido traduce únicamente sus propios
errores. Los manejadores biométricos protegidos y sus textos específicos de
interfaz quedaron fuera de esta revisión general.

Quedan textos protegidos pendientes de una petición específica que nombre el
módulo biométrico: el consentimiento y la instrucción inicial en español omiten
video o pertenencia al grupo, una acción conserva «match» y las cantidades de
importación, fotogramas y enrolamientos necesitan formas singulares. Esta entrega
conserva esos textos y el comportamiento del módulo.

La revisión única `meta-social-profile-display-v1` añade traducciones faltantes
de género y ubicación de los perfiles públicos, después de inicializarlos.
Conserva campos originales, ediciones manuales, eliminaciones, membresías,
referencias privadas y consentimiento. La documentación tiene descripciones
revisadas en español para todas las operaciones de API; el generador rechaza
las etiquetas en español que falten.

Pasaron las comprobaciones focalizadas: **133 pruebas distintas de
backend/gateway**, **18 de datos locales y textos guardados** y **7 de
documentación y contratos**. Son comprobaciones específicas, no una repetición
de la suite completa. Newman también aprobó las pruebas con simulaciones HTTP
locales de escrituras deshabilitadas, renovación de autenticación y cabeceras de
idioma. Pasaron formato, lint, arquitectura y documentación.

## Base de validación y comprobaciones anteriores

- La entrega anterior de arquitectura aprobó la suite completa de backend/gateway: **660 pruebas** en 571,01 segundos, sin fallos ni omisiones. Incluye contratos API, permisos, aislamiento por grupo, instalación de esquema, retiro local, revisiones aditivas, rollback y conservación de ediciones, eliminaciones y consentimientos. Esta cifra no representa una repetición de la suite completa en la revisión de filtros.
- Una instalación local nueva tiene 25 publicaciones, 28 medios base, 16 expedientes y 16 adjuntos. La inicialización social añade trece perfiles, trece avatares separados y treinta y nueve referencias privadas: 80 medios y 19 usuarios en total, con solo seis cuentas en el selector. Policía conserva cinco órdenes de captura, dos procesos activos y cuatro órdenes independientes de búsqueda por desaparición.
- El inventario de medios tiene 423 entradas verificadas: 132 recursos del repositorio y 291 solo locales. Se retiraron 34 archivos exclusivos de Memory y su recibo QA de video obsoleto. Doce imágenes Meta nuevas se comprobaron con InsightFace local ya disponible: una cara por avatar/referencia y las nueve referencias privadas dentro de los requisitos de calidad. Es validación de recursos, no una afirmación de precisión representativa ni de integración real con Facebook.
- Pasaron `make lint`, `make architecture-check` y `make docs-check`. La documentación cubre 74 archivos Markdown y 352 peticiones Postman, incluidas 23 de escenarios locales y 71 guardas de escritura de referencia. Newman verificó 168 escrituras deshabilitadas, dos secuencias de login/refresh, nueve errores de autenticación previstos y códigos exactos, usando únicamente mocks HTTP locales.
- El fallo del CI anterior se debía a rutas de sockets Unix de PostgreSQL que excedían el límite de Linux en el checkout largo de GitHub. El helper de pruebas ahora crea rutas cortas de sockets y mantiene los archivos de la base en `.runtime`; cuatro casos PostgreSQL pasaron con ese helper. No se utilizó ninguna base ni servicio productivo.

## Validación Android

La vista previa del Display en localhost ahora inicia automáticamente tras
inicializar Bluetooth/DAT, usando el perfil de la cuenta local existente. La
condición anterior de `LOCAL_DEVELOPMENT` omitía el arranque del simulador y
dejaba la pantalla en “Waiting for Meta Display…”. La corrección conserva la
selección de gafas físicas y los permisos de cámara/micrófono. En el teléfono
Android conectado se reprodujo la espera con el APK anterior; tras instalar
el reemplazo firmado, el preview mostró el menú Buscar/Capturar de RealityOS
dentro de la lente. Esta comprobación del dispositivo cubrió inglés al tamaño
normal. Sigue pendiente la aceptación visual completa ES/EN a anchos estrechos
y texto al 200 %, además de la validación con gafas físicas.

La corrección pasó 15 pruebas Android locales: cuatro regresiones de arranque,
cinco de selección de entrada y seis de interacción táctil de captura. Las
compilaciones Debug y Release pasaron en un directorio aislado de firma; el APK
Debug canónico conserva el certificado existente y se instaló correctamente
en el teléfono conectado.
También pasaron `ktlintCheck`, `lintDebug` y las revisiones de arquitectura y documentación.

La revisión de textos aprobó **57 pruebas focalizadas del proyecto**, más
**6 comprobaciones temporales de estados renderizados**. Las repeticiones tras
los últimos ajustes de fechas y plurales no se suman de nuevo. Se revisaron
perfiles, almacenamiento, filtros de galería y controles de audio en ES/EN a
320–480 dp, incluido texto al 200 %. La fila de acciones del perfil se adapta
para mantener Guardar accesible con texto ampliado. Son comprobaciones
Robolectric, sin teléfono físico, gafas ni emulador real.

El lint de la revisión de textos informa cero errores, 101 advertencias y
10 sugerencias. La advertencia adicional corresponde a un texto usado únicamente
por el controlador de vista previa Release; el nuevo plural de edad incluye la
forma CLDR `many` del español. Las advertencias previas de plurales biométricos
protegidos permanecen sin cambios.

La compilación final de esta revisión aprobó `ktlintCheck`, `lintDebug`,
`assembleDebug`, `assembleRelease` y `compileDebugAndroidTestKotlin`. El APK Debug
canónico incluye los últimos ajustes de fechas y plurales y mantiene la firma existente.

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

El [APK Debug canónico](../../../android/app/build/outputs/apk/debug/app-debug.apk), versión `0.1.6-debug-20261104-1316`, tiene SHA-256 `bab5148b6d3e6f861078c2b85f3706d9c0776f33a1cb344f2e292a83863eb575` y conserva el certificado de firma existente. Los recursos de splash, icono y tema permanecen iguales a la revisión de logos. El APK se mantiene como artefacto de entrega del repositorio.

<a id="next-steps"></a>

## Aceptación pendiente

| Área | Evidencia necesaria |
| --- | --- |
| Android/dispositivo | Comprobación en teléfono y gafas físicos, incluida carga real de medios e interacciones. Los estados renderizados de Robolectric no sustituyen la validación en dispositivos. |
| Instalación completa | Primer inicio real en Windows/Linux con Docker, incluyendo descarga de imágenes y modelos; el test PostgreSQL aislado no valida ese recorrido. |
| Integraciones externas | Facebook Live, Meta real, DAT/gafas, correo y voz remota necesitan sus comprobaciones propias. |
| Derechos y entrega | Términos DAT autenticados, constancia de derechos de `buffalo_l` y grabación/recibo final según [Terceros](THIRD_PARTY.md) y [Hackathon](HACKATHON.md). |

[Arquitectura](../architecture/ARCHITECTURE.md) · [Datos](../architecture/DATABASE.md) · [Checklist](../testing/IMPLEMENTATION_CHECKLIST.md)
