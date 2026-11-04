[English](../../en/project/IMPLEMENTATION_STATUS.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Estado vigente de implementación

Actualizado el **3 de noviembre de 2026**. Un build o una comprobación HTTP no aprueba pruebas físicas. Las entregas anteriores permanecen en Git.

## Evaluación local — entrega vigente

La instalación principal es localhost Windows/Linux x64: PostgreSQL, Redis, la API existente y el worker. No requiere gateway/proxy/scheduler local, almacenamiento externo, login Facebook ni ElevenLabs. El selector de nueve cuentas solo está en Debug local. El procesamiento y la búsqueda Meta mantienen sus rutas reales; la salida de voz usa voces instaladas sin conexión en Android.

Verificado en Docker Linux aislado: PostgreSQL 16 desde cero en `20261104_0039`, 9 cuentas, 3 grupos, 47 expedientes, 27 adjuntos, hashes de 48 publicaciones y descarga de 9 avatares; aislamiento por membresía, edición de perfil, crear/borrar grupos, OpenAPI local exacto, comunicación worker/Redis y persistencia al reiniciar. No se usaron datos ni credenciales de producción. Las 48 escenas existentes con licencia se incluyen ahora en Git, junto con su manifiesto de fuente/licencia/hash.

Backend/gateway: **591 pruebas aprobadas**, más la regresión adicional de reanudación de la cola local. Android: **290 pruebas unitarias aprobadas**; selector renderizado revisado en ES/EN, incluyendo 320 dp y texto al 200 %. Pasaron los scripts Postman y las pruebas Newman de acceso, renovación y errores. Pasaron `ktlintCheck`, `lintDebug`, compilaciones Debug/Release y compilación de pruebas Android. [Comprobante sin secretos](../../assets/local/verification.json).

El inicio de Windows ahora abre Docker Desktop instalado si el motor local no está disponible y espera hasta dos minutos. Pasaron nueve casos de regresión en PowerShell 5.1 con comandos Docker/procesos simulados, cubriendo arranque, tiempo agotado y rechazo de contextos remotos; esto no verifica un inicio real de Desktop.

Pendiente de validación externa: instalación Windows completa, teléfono físico/USB/voces, gafas y llamadas reales con la clave Meta del jurado. Las pruebas Linux/Docker no certifican estos recorridos. Los resultados históricos del servidor que siguen se conservan como referencia y no son requisitos de localhost. El despliegue remoto automático está desactivado; el instalador local no detiene ni modifica servidores históricos.

## Clasificación de publicaciones

Los catálogos de grupo, la clasificación manual obligatoria, etiquetas en miniaturas, iconos de video y filtros autorizados están incluidos en la revisión `20261103_0038`. Los archivos de bucket sin clasificar siguen privados para revisión del propietario. La [guía de clasificación](../guides/PUBLICATION_CLASSIFICATION.md) documenta este flujo.

El manifiesto revisado cubre las 48 publicaciones de evaluación con licencia. Se aplicó la clasificación a esas y a una publicación visible adicional revisada por separado: **49 publicaciones visibles de cuatro grupos existentes** ya tienen categoría y tags. Se comprobaron los hashes originales antes y después; repetir la asignación produjo cero cambios. El diario privado de reversión es `.runtime/publication-classification-journal.json` y su comprobación sin escritura aprobó. Las tres cuentas del jurado verificaron clasificación y filtros combinados en la API real; filtrar otro grupo devolvió `403`. No se clasificaron publicaciones ocultas ni medios privados.

## Implementado

| Área | Comportamiento vigente |
| --- | --- |
| Android | Galería principal única y una barra inferior para cuenta, edición, gafas y buscador/chat Muse; las acciones de grupo permanecen arriba del contenido. El avatar vuelve al grupo seleccionado. Los controles Meta están junto a su título local. |
| Grupos | Publicar exige pertenencia. Las publicaciones propias se pueden copiar a varios grupos, con reacciones/comentarios independientes; las antiguas sin grupo se eliminaron por instrucción del propietario. La paginación con cursor y un único modelo de publicaciones de grupo reemplazan las rutas personales/públicas. |
| Biometría | Se mantienen consentimiento y búsqueda facial aislada. El ingreso por email solicita foto de perfil/avatar y 3–25 referencias privadas aceptadas, con continuación y nueva selección. Los originales y URLs de referencias Meta no aparecen en galerías ni miniaturas de candidatos de cuenta. |
| Almacenamiento | R2/S3 editable, miniaturas a la derecha, destino por grupo, sincronización inmediata/cada 15 minutos, reconciliación tras recorrido completo y retiro de copias importadas/compartidas protegido por revisión. Los objetos remotos se conservan. |
| Evidencia | Originales BYTEA, proveedor real, evidencia versionada y traducciones. Consultar no inicia capturas ni inventa observaciones. |
| Expedientes y voz | Se conservan expedientes versionados y comparación clínica; transcripción Muse y síntesis ElevenLabs autenticada. |

## Servidor vigente verificado

- Desplegada `realityos-backend:unified-groups-20261103-verified`, Alembic **`20261103_0038`**. Salud y comparación exacta de OpenAPI público aprobadas. Las tres cuentas del jurado consultaron sus 16 publicaciones de grupo y abrieron Mis conexiones conservando la sesión.
- Eliminadas **234** publicaciones antiguas sin grupo; conservadas **70** publicaciones de grupos y sus originales sin cambios. Las huellas de tablas confirmaron perfiles, enrolamientos/consentimientos biométricos, 47 expedientes y 27 adjuntos intactos. La migración también conserva los hashes de 25 solicitudes de importación. Actualización/reversión/actualización de PostgreSQL aprobadas sobre una base restaurada aislada.
- Backend/gateway: **588 pruebas aprobadas**, más **14 comprobaciones específicas** tras la limpieza final. Formato, lint, arquitectura, documentación y runtime Newman aprobados.
- Android: **287 pruebas aprobadas**, `ktlintCheck`, `lintDebug` y builds Debug/Release aprobados. Revisión visual ES/EN con 320 dp y texto al 200 %. No hubo dispositivo físico conectado. APK Debug vigente: `android/app/build/outputs/apk/debug/app-debug.apk`; SHA-256 `5bc5984115419477bd516652c370d463872ae1fdfc806766aa26010d0765e3f1`.
- Instrucciones privadas de reversión: `.runtime/unified-groups-20261103-rollback.md`, con overlay de imagen/runtime `.runtime/unified-groups-20261103-rollback.json`. La reversión de datos necesita el snapshot técnico `pre-unified-publications.dump`, que caduca a las 24 horas (una hora con presión de disco). Las imágenes anteriores requieren revertir primero esquema/datos.

## Verificación anterior

- Renovación de videos desplegada en `realityos-backend:evaluation-videos-20261103-final`: API, worker y scheduler saludables, contrato OpenAPI público idéntico y Alembic `20261103_0036`. Las 16 pruebas de renovación pasaron; formato, lint, estructura y documentación/Postman también. El [recibo de videos](../../assets/storage/video-evaluation-verification.json) registra los resultados reales y la eliminación solicitada del material sin uso. Rollback del código: `.runtime/evaluation-videos-20261103-rollback.json`; los videos eliminados no tienen reversión.
- [Despliegue productivo aprobado](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/41709265025): imagen inmutable `99fe11f`, después de la entrega local `realityos-backend:workspace-privacy-20261103`. API, worker y scheduler conservan runtime y conexiones. Esa entrega usó la revisión PostgreSQL **`20261103_0036`**. Actualización → reversión → actualización aprobadas sobre un esquema PostgreSQL temporal; actualización productiva, salud y comparación exacta de OpenAPI público aprobadas.
- La suite de 499 pruebas backend/gateway terminó CI con **496 aprobadas y tres omitidas**, incluidos contrato corregido, pérdida de membresía y privacidad de referencias. Android aprobó **228 pruebas**, formato/lint y builds Debug/Release. Documentación, estructura y Postman validados.
- APK instalable: `android/app/build/outputs/apk/debug/app-debug.apk`; SHA-256 `2666a4ee7a15decca18311a28f8d3072e05afe22823b2cae04167a46d78953bc`.
- Rollback de imagen: `.runtime/workspace-privacy-20261103-rollback.json`. Diario de visibilidad demo: `.runtime/real-scenes-20261103-visibility.json`. El snapshot técnico `pre-workspace-privacy-20261103.dump` caduca mediante mantenimiento tras 24 horas, o una bajo presión de disco; no es un respaldo oficial y no se envió a R2.
- Producción conserva Meta directo con gateway de respaldo, claves privadas y la excepción aislada de ingreso Windows/Debug. El mantenimiento protege imágenes activas y rollback.
- [Comprobante de API real](../../assets/storage/workspace-privacy-verification.json): las tres cuentas de jurados accedieron, descargaron avatar y media nueva, consultaron expedientes y exploraron su bucket por autor. Las consultas a otro grupo devolvieron `403`; publicar en privado devolvió `422`.

## Datos vigentes de evaluación

El alcance se limita a los grupos **existentes**. Los tres grupos de evaluación tienen **48 escenas con licencia: 12 fotos y cuatro videos por grupo**. Los 12 videos nuevos son grabaciones completas de 7,04–28,36 segundos, con resolución nativa HD y cadencia original de 25–50 fps. Incluyen recogida de llaves, preparación de instrumental, traslado de muestras y organización de pertenencias. El [manifiesto de fuentes, licencias y hashes](../../../simulator/real-scenes/manifest.json) conserva su procedencia; los archivos multimedia permanecen fuera de Git. Los 12 análisis reales están completos.

Se conservan **47 expedientes, 27 adjuntos y seis retratos de expediente enrolados**, además de las 36 fotos y sus identificadores. La renovación no añadió grupos, cuentas ni membresías. Nueve conexiones existentes sincronizan únicamente su subcarpeta `evaluation-v3/` cada 15 minutos. Se verificaron las 48 escenas actuales por lectura remota y SHA-256. Por instrucción expresa del propietario se eliminaron los 12 videos anteriores, un candidato descartado y 96 copias remotas obsoletas, además de sus bytes y evidencia locales. Dos recorridos completos posteriores de las nueve fuentes conservaron las publicaciones vigentes, sin duplicados ni reaparición del material eliminado. La reversión de esos videos ya no está disponible.

El [recibo de evaluación](../../assets/storage/video-evaluation-verification.json) registra **48 consultas positivas ES/EN, seis negativas, seis comprobaciones entre grupos y 12 descargas originales verificadas**. Se revisaron visualmente los fotogramas y sus recuadros. La [matriz reproducible](../testing/VIDEO_EVALUATION.md) conserva las preguntas; sus revisiones y una toma rechazada por recuadros incorrectos quedan documentadas. Es una demostración seleccionada, no una estimación general de precisión.

Postman mantiene exactamente **Server requests** y **Localhost requests**, con **449 solicitudes**, incluidos los **87 recorridos sobre datos existentes** (48 consultas ES/EN de videos). Los IDs de publicaciones del jurado apuntan al contenido renovado. Solo las tres contraseñas autorizadas por el propietario son públicas. Las cuentas por email, incluidas las de prueba sin configuración completa, reciben el nuevo ingreso biométrico privado; no se inventó consentimiento ni enrolamiento completado.

<a id="next-steps"></a>

## Aceptación pendiente

| Pendiente | Evidencia necesaria |
| --- | --- |
| UI en teléfono | Teclado físico, insets de navegación Android, gestos sobre cámara y checklist completo con el APK identificado. No hubo dispositivo conectado en esta sesión. |
| Integraciones externas | Login/importación Facebook Live, DAT/gafas físicas, correo real e instalación Windows completa necesitan recorridos propios registrados. Las pruebas unitarias no los aprueban. |
| Base vacía | Se detectó un problema previo del baseline histórico: `0001` carga modelos actuales y el arranque SQLite desde cero falla por una clave foránea de publicaciones sin resolver. La actualización y reversión sobre esquema PostgreSQL existente aprobaron. No se declara aprobada una instalación Windows nueva. |
| Terceros y entrega | Siguen pendientes términos DAT autenticados, constancia de derechos de `buffalo_l` y grabación/recibo final, según [Terceros](THIRD_PARTY.md) y [Hackathon](HACKATHON.md). |

Este informe excluye credenciales privadas, tokens y media personal. La aceptación manual completa requiere evidencia de todos los casos del checklist.
