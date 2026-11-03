[English](../../en/project/IMPLEMENTATION_STATUS.md) · [RealityOS](../README.md) · [Índice](../INDEX.md)

# Estado vigente de implementación

Actualizado el **3 de noviembre de 2026**. Esta página reúne el estado actual; los cambios anteriores se consultan en Git. Un build o una comprobación HTTP no aprueba una prueba física.

## Implementado

| Componente | Estado |
| --- | --- |
| Android y Display nativo | Perfil, Trabajo, Buscar y Ray-Ban; captura explícita, evidencia y contexto autorizado. Debug incluye Mock Device Kit; Release lo excluye. |
| Acceso y perfiles | Cuentas por correo y Facebook, confirmación/recuperación, corrección de correo pendiente y edición de perfil según origen de datos. |
| Objetos y publicaciones | Originales BYTEA, análisis Muse/SAM, evidencia versionada, revisión de duplicados y traducciones persistidas. |
| Biometría | Consentimiento, enrolamiento explícito, búsqueda de candidatos de usuario/expediente y confirmación humana. Brazo separado del procesamiento de objetos. |
| Expedientes | Importación versionada, relaciones y adjuntos; comparación clínica de campos explícitos con referencias. |
| Voz | Muse Voice Transcribe para entrada; ElevenLabs para síntesis autenticada. |
| Buckets R2/S3 | Conexiones privadas, explorador, copias importadas al perfil/grupo, consultas, CV y sincronización manual/programada. [Guía](../guides/STORAGE_CONNECTIONS.md). |

## Código y producción verificados

- Backend revisado: [`0090bdf`](https://github.com/Luxisoft/realityos-spatial-memory/commit/0090bdfcb8d8f298da73ece3c8d6e57e6b5448b6). Incluye las correcciones de firma S3, reimportación tras cancelar/borrar/sustituir, estado de duplicados y evidencia seleccionada. Los reintentos usan el estado vigente del archivo y la sincronización manual procesa sin cola. El análisis libera la conexión y vuelve a comprobar permisos antes de publicar; las búsquedas por imagen mantienen la API disponible.
- [Despliegue productivo aprobado](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/41684655293): API, worker y scheduler; Alembic `20261103_0035`. Se verificaron los hashes del código ejecutado, la salud y la igualdad exacta del contrato OpenAPI público.
- **492 pruebas locales backend/gateway** —35 del conector y dos regresiones de concurrencia en búsqueda— aprobadas. [CI de la versión de backend](https://github.com/Luxisoft/realityos-spatial-memory/actions/runs/41684656174). El Android vigente pasó **224 pruebas locales**, formato/lint y builds Debug/Release. Las búsquedas por imagen admiten hasta tres minutos: la consulta real tardó 60,77 segundos y superaba el límite anterior de un minuto. [Comprobante](../../assets/storage/review-verification.json).
- APK instalable: `android/app/build/outputs/apk/debug/app-debug.apk`. Identificar cada ejecución por SHA-256; la etiqueta de versión sola no distingue builds.
- Producción usa Meta directo con gateway habilitado como respaldo. ElevenLabs y R2 tienen conexiones independientes. Las claves permanecen privadas.
- El rollback verificado de la revisión está conservado en `.runtime/storage-followup-20261103-ci-rollback.json`. Revertir código no revierte automáticamente migraciones o datos; seguir la [guía operativa](../deployment/DEPLOYMENT.md).
- Limpieza del 3 de noviembre: retirados indexadores sin llamadas, pantallas y controles Android sin uso, 93 textos obsoletos por idioma, scripts sustituidos, la función antigua de acceso invitado sin llamadas y la repetición de una regresión histórica en CI. Las regresiones vigentes se conservan. También se retiraron 2,42 GB de cachés duplicadas y archivos de la web retirada del servidor.
- Segunda revisión del proxy: corregido el bloqueo de Swagger en `/docs` y su callback. **27 comprobaciones locales con Nginx real** aprobaron las configuraciones productiva, local y con activación por socket: documentación y API accesibles, rutas de la web retirada en `410`. Se añadió una regresión para el contrato público usado por Swagger. Tras el despliegue se confirmaron `/docs` y su callback en `200`, y `/` y `/display` en `410`.
- GitHub conserva el paquete retirado `realityos-tts`; no interviene en la ejecución ni en el despliegue actual. El intento de borrarlo recibió `403`: el token disponible necesita `read:packages` y `delete:packages`. No se añadió ninguna automatización de limpieza.

## Datos disponibles para evaluar

Los tres escenarios preparados conservan **47 registros, 27 adjuntos y seis retratos de expediente enrolados**. Las nueve cuentas de escenario tienen avatar, publicaciones y grupo. Las cuatro cuentas QA y sus permisos están descritos en el [checklist](../testing/IMPLEMENTATION_CHECKLIST.md); la preparación se registró en `.runtime/acceptance-readiness.json`.

Postman mantiene **Server requests** y **Localhost requests**, **393 solicitudes** en total y los **39 recorridos sobre datos existentes**. Solo las tres cuentas del jurado autorizadas tienen contraseñas públicas; otras cuentas y credenciales permanecen en archivos privados. En la segunda revisión, las tres cuentas aprobaron login, descarga del avatar y del archivo de una publicación preparada; cada una conserva siete publicaciones de grupo y una conexión de bucket.

**R2 preparado:** 426 recursos cargados y verificados por lectura remota/SHA-256; 14 conexiones para las nueve cuentas de escenario y cuatro QA. El administrador QA dispone también del directorio social/taller. API: originales y previews por cuenta, video `206`, PDF, rechazo entre cuentas `404` y sin sesión `401`. El endpoint S3 rechaza la petición sin firma (`400`, `Authorization`). [Comprobante](../../assets/storage/demo-verification.json) · [Entrada desde la app](../guides/STORAGE_CONNECTIONS.md). Las claves Luxisoft reutilizadas por autorización del propietario conservan sus permisos; la aplicación no las devuelve y usa operaciones de lectura.

**Comprobación adicional de API con R2 real:** originales de imagen/video con SHA-256 idéntico tras importarlos a BYTEA; permisos privados/de grupo, reimportación idempotente, confirmación de duplicados, dos versiones privadas de CV y desconexión aprobados. Se ejecutó un ciclo real del planificador sobre una carpeta vacía, pausa y actualización manual. La búsqueda de objetos devolvió dos evidencias sin crear publicaciones. Desde el host de producción, encolar y desconectar durante el análisis tardó 0,010/0,011 segundos; la salud siguió disponible. Las conexiones temporales quedaron desconectadas. Estas pruebas no aprueban el checklist físico de Android.

**Revisión de terceros realizada:** inventario de 93 paquetes Python y 210 dependencias Android. El cierre de derechos de `buffalo_l` y términos DAT necesita la evidencia indicada en [Terceros](THIRD_PARTY.md).

<a id="next-steps"></a>

## Pendientes de cierre

| Pendiente | Evidencia necesaria |
| --- | --- |
| Aceptación de la app | Ejecutar los **89 casos de aceptación y seis de cierre** del checklist con el APK y servidor identificados; conservar resultados y capturas. |
| Teléfono y proveedores externos | Completar cámara, permisos, audio, correo real, Facebook real y los recorridos Live de la demo. No se marcan aprobados por las pruebas unitarias. |
| Hardware y Windows | Gafas físicas y una instalación completa Windows/Docker requieren su propia evidencia. El Display simulado y los tests de scripts Windows tienen un alcance distinto. |
| Hackathon | Confirmar equipo/track y requisitos, revisar derechos y salidas de la demo, grabar video accesible y guardar recibo del portal. [Guía de entrega](HACKATHON.md). |

El 100 % aprobado solo puede declararse para el alcance del checklist cuando todos sus casos tengan evidencia y no queden fallos, pendientes ni bloqueos. Las credenciales, respuestas privadas y capturas personales no se publican en este documento.
