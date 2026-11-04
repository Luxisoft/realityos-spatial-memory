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

Los datos preparados incluyen los tres grupos y nueve cuentas de acceso. Policía tiene 16 expedientes de personas ficticias con publicaciones de retratos vinculadas, además de tres videos. Cinco tienen orden de captura vigente y dos de ellas tienen procesos activos; cuatro expedientes independientes de personas desaparecidas tienen órdenes de búsqueda vigentes, sin captura ni antecedentes. Memoria conserva sus 16 publicaciones. Meta Social Media incorpora tres presentaciones mediante avatares separados, tres videos y diez perfiles sintéticos con tres referencias privadas cada uno. La galería local compartida contiene 41 publicaciones en total (Policía 19, Meta Social Media 6, Memoria 16). Los perfiles adicionales no son cuentas seleccionables. No se publica ninguna referencia biométrica ni se omiten consentimientos.

Postman mantiene Localhost requests y Server requests. Los ejemplos locales se derivan de la BD inicializada; Server requests permanece deshabilitado y sin URL activa ni credenciales. Las antiguas autorizaciones para contraseñas de prueba no se aplican a nuevas exportaciones.

## Comprobaciones de este bloque

- La ejecución amplia de backend/gateway evaluó 628 casos sin omisiones: 621 pasaron y se identificaron siete fallos de configuración/contrato. Los siete se corrigieron y verificaron en ejecuciones específicas posteriores; no queda ningún fallo conocido de pruebas.
- La validación final de datos/API/gateway aprobó **118 pruebas distintas** sin fallos ni omisiones: 110 casos existentes de integración y consumidores de datos en la ejecución de cierre, más ocho casos nuevos SQLite/PostgreSQL de la revisión policial aditiva. Se comprobaron 41 publicaciones, 57 medios base, 34 expedientes y 26 adjuntos de expediente; los seis retratos nuevos; reproducción y rangos de bytes de los seis videos; acceso por grupo; propietarios inactivos; membresías/grupos retirados; rollback y conservación de ediciones y eliminaciones. Las cinco órdenes de captura y las cuatro órdenes de búsqueda por desaparición permanecen separadas, sin autorización biométrica automática.
- Las pruebas PostgreSQL aisladas verificaron el baseline inmutable, equivalencia de migraciones, conservación de datos, actualizaciones SQL por grupo, términos de catálogo renombrados y rollback de referencias duplicadas. No se utilizó ninguna base productiva.
- Pasaron `make lint`, `make architecture-check` y `make docs-check`. La comprobación documental cubrió 74 archivos Markdown y 383 peticiones Postman con variables locales y del servidor aisladas.
- La comprobación de runtime Newman pasó: 170 escrituras deshabilitadas, dos secuencias de login/refresh, nueve errores de autenticación previstos y códigos de respuesta exactos. Solo utilizó mocks HTTP locales.

## Validación Android

La ejecución Android actual aprobó **313 pruebas**, sin fallos, errores ni pruebas omitidas. Pasaron `assembleDebug`, `assembleRelease` y `compileDebugAndroidTestKotlin`. `ktlintCheck` pasó para el conjunto de fuentes `refactoredKotlin` configurado; no equivale a comprobar el formato de todo el repositorio. `lintDebug` completo informó cero errores, 98 advertencias y 10 sugerencias.

Las pruebas renderizadas en Robolectric y las capturas PNG revisadas cubrieron el selector de cuentas en ES a 320 dp/texto 200% y EN a 390 dp; filtros ES/EN a 320 dp/200%; y miniaturas ES a 320 dp/200% y EN a 480 dp. Son los estados comprobados, no todas las combinaciones de idioma, ancho y texto. Las miniaturas usaron URLs de prueba. No se realizó validación con dispositivo físico ni emulador real.

El [APK Debug canónico](../../../android/app/build/outputs/apk/debug/app-debug.apk) tiene SHA-256 `6a848835e43ad641d3b6a620a70e771cffdc8ed92eb30c3dc7763dcd08d905cc`. Se conserva como artefacto de entrega del repositorio.

<a id="next-steps"></a>

## Aceptación pendiente

| Área | Evidencia necesaria |
| --- | --- |
| Android/dispositivo | Comprobación en teléfono y gafas físicos, incluida carga real de medios e interacciones. Los estados renderizados de Robolectric no sustituyen la validación en dispositivos. |
| Instalación completa | Primer inicio real en Windows/Linux con Docker, incluyendo descarga de imágenes y modelos; el test PostgreSQL aislado no valida ese recorrido. |
| Integraciones externas | Facebook Live, Meta real, DAT/gafas, correo y voz remota necesitan sus comprobaciones propias. |
| Derechos y entrega | Términos DAT autenticados, constancia de derechos de `buffalo_l` y grabación/recibo final según [Terceros](THIRD_PARTY.md) y [Hackathon](HACKATHON.md). |

[Arquitectura](../architecture/ARCHITECTURE.md) · [Datos](../architecture/DATABASE.md) · [Checklist](../testing/IMPLEMENTATION_CHECKLIST.md)
