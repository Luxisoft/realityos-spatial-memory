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

## Comprobaciones de esta entrega

- La suite completa de backend/gateway aprobó **660 pruebas** en 571,01 segundos, sin fallos ni omisiones. Incluye contratos API, permisos, aislamiento por grupo, instalación de esquema, retiro local, revisiones aditivas, rollback y conservación de ediciones, eliminaciones y consentimientos.
- Una instalación local nueva tiene 25 publicaciones, 28 medios base, 16 expedientes, 16 adjuntos y 10 términos de clasificación. La inicialización social añade trece perfiles, trece avatares separados y treinta y nueve referencias privadas: 80 medios y 19 usuarios en total, con solo seis cuentas en el selector. Policía conserva cinco órdenes de captura, dos procesos activos y cuatro órdenes independientes de búsqueda por desaparición.
- El inventario de medios tiene 423 entradas verificadas: 132 recursos del repositorio y 291 solo locales. Se retiraron 34 archivos exclusivos de Memory y su recibo QA de video obsoleto. Doce imágenes Meta nuevas se comprobaron con InsightFace local ya disponible: una cara por avatar/referencia y las nueve referencias privadas dentro de los requisitos de calidad. Es validación de recursos, no una afirmación de precisión representativa ni de integración real con Facebook.
- Pasaron `make lint`, `make architecture-check` y `make docs-check`. La documentación cubre 74 archivos Markdown y 352 peticiones Postman, incluidas 23 de escenarios locales y 71 guardas de escritura de referencia. Newman verificó 168 escrituras deshabilitadas, dos secuencias de login/refresh, nueve errores de autenticación previstos y códigos exactos, usando únicamente mocks HTTP locales.
- El fallo del CI anterior se debía a rutas de sockets Unix de PostgreSQL que excedían el límite de Linux en el checkout largo de GitHub. El helper de pruebas ahora crea rutas cortas de sockets y mantiene los archivos de la base en `.runtime`; cuatro casos PostgreSQL pasaron con ese helper. No se utilizó ninguna base ni servicio productivo.

## Validación Android

La ejecución Android final aprobó **313 pruebas permanentes del proyecto** y una comprobación temporal de renderizado nativo del icono: 314 resultados XML, sin fallos, errores ni omisiones. Pasaron `assembleDebug`, `assembleRelease` y `compileDebugAndroidTestKotlin`. `ktlintCheck` pasó para el alcance de fuentes configurado; no equivale a comprobar el formato de todo el repositorio. `lintDebug` completo informó cero errores, 98 advertencias y 10 sugerencias.

Los renderizados Robolectric revisados cubrieron el selector de dos grupos/seis cuentas en ES a 320 dp/texto 200% y EN a 390 dp; el recorrido Explorar de cuatro páginas en ES a 320 dp/200% y EN a 480 dp; y el icono nativo del lanzador. La imagen RGBA de 150×150 proporcionada por el propietario se conserva en `icon_app.png`; `#017df7` se aplica únicamente al fondo del lanzador. Se mantuvieron los colores y tokens de las vistas y botones internos. Estas comprobaciones no cubren todas las combinaciones de idioma, ancho y texto. No hubo validación con dispositivo físico ni emulador real para esta entrega.

El [APK Debug canónico](../../../android/app/build/outputs/apk/debug/app-debug.apk), versión `0.1.6-debug-20261104-1053`, tiene SHA-256 `ae810778e8b41772d8baf5e4815da20dc7abb224997be9aa0becdb4f3e4d1aca` y conserva el certificado de firma existente. Se mantiene como artefacto de entrega del repositorio.

<a id="next-steps"></a>

## Aceptación pendiente

| Área | Evidencia necesaria |
| --- | --- |
| Android/dispositivo | Comprobación en teléfono y gafas físicos, incluida carga real de medios e interacciones. Los estados renderizados de Robolectric no sustituyen la validación en dispositivos. |
| Instalación completa | Primer inicio real en Windows/Linux con Docker, incluyendo descarga de imágenes y modelos; el test PostgreSQL aislado no valida ese recorrido. |
| Integraciones externas | Facebook Live, Meta real, DAT/gafas, correo y voz remota necesitan sus comprobaciones propias. |
| Derechos y entrega | Términos DAT autenticados, constancia de derechos de `buffalo_l` y grabación/recibo final según [Terceros](THIRD_PARTY.md) y [Hackathon](HACKATHON.md). |

[Arquitectura](../architecture/ARCHITECTURE.md) · [Datos](../architecture/DATABASE.md) · [Checklist](../testing/IMPLEMENTATION_CHECKLIST.md)
