# Conectar tu bucket y utilizar sus recursos

[English](STORAGE_CONNECTIONS.md) · [Proyecto](../README.es.md) · [API](API.es.md)

RealityOS conserva sus cuentas, permisos y procesamiento. Tu bucket es una fuente privada: eliges qué importar. **Importar guarda una copia en RealityOS**; desconectar el bucket conserva las publicaciones e historial ya importados. Usar un archivo para buscar no lo publica ni lo registra como evidencia nueva.

## Desde Android

1. Abre **Perfil → Mis conexiones → Añadir bucket**.
2. Selecciona R2 o S3. Escribe nombre, endpoint HTTPS, bucket, región y carpeta inicial opcional. Para R2 usa el endpoint S3 de tu cuenta y región `auto`.
3. Introduce Access Key ID y Secret Access Key con permisos de **lectura y listado**. Guarda y pulsa **Comprobar acceso**. El bucket no necesita ser público. Las claves se cifran en el servidor y no se vuelven a mostrar.
4. Explora carpetas; abre una vista previa o selecciona archivos. Elige **Mi perfil privado** o un grupo al que pertenezcas.
5. Pulsa **Importar selección** y confirma. Revisa cada archivo en **Importaciones recientes**. Los duplicados requieren la decisión existente de reemplazar o cancelar; los fallidos se pueden reintentar.

Fotos: JPEG, PNG y WebP. Video: MP4, hasta 120 segundos en publicaciones. La descarga remota está limitada a 64 MiB y respeta además los límites existentes de imagen/video del servidor (imagen: 10 MiB por defecto). PDF/DOCX: **Usar como CV**, hasta 10 MiB, con confirmación de reemplazo. Otros formatos se muestran como incompatibles.

Para consultar, selecciona un archivo y usa **Buscar objeto** (imagen) o **Buscar persona** (imagen/video). La búsqueda se realiza en el espacio elegido. Biometría conserva consentimiento, calidad y enrolamientos previos; importar retratos nunca enrola todas sus caras automáticamente. Los resultados enlazan con evidencia, perfiles o expedientes autorizados.

## Actualización y privacidad

Configura sincronización manual o actívala cada 15 minutos, cada hora o diariamente. Se recorre la carpeta seleccionada y sus subcarpetas, por páginas. **Actualizar ahora** procesa la siguiente página; la sincronización automática continúa cada minuto mientras queden páginas.

Los recursos nuevos se importan y las sustituciones siguen la revisión de duplicados. Archivos idénticos en el mismo origen/destino no generan otra publicación. Un borrado remoto o error de listado no elimina copias existentes. **Pausar** desactiva el horario; **Desconectar** impide nuevas descargas y conserva lo ya importado.

Una conexión pertenece solo a su creador. Compartir una publicación con un grupo no entrega las claves ni acceso al resto del bucket. Los permisos del grupo se comprueban antes de descargar y publicar. Para cambiar bucket, endpoint o carpeta raíz, crea otra conexión; **Editar claves** permite rotarlas sin mostrar las anteriores.

## API y operación

Familia `/v1/me/storage-connections`: CRUD privado, `/test`, `/objects`, `/content`, `/imports`, `/imports/{id}/retry`, `/syncs`, `/syncs/{id}/run` y `/cv`. Ver contrato generado en [API_REFERENCE](API_REFERENCE.es.md). La colección Postman conserva **Server requests** y **Localhost requests**; sus nuevas operaciones requieren configurar una conexión propia y habilitar explícitamente las escrituras.

Configura `STORAGE_ENCRYPTION_KEY` con un secreto aleatorio persistente del servidor en `.env.storage` (modo 0600, ignorado por Git). API y worker deben usar la misma clave. No la reemplaces sin recifrar las conexiones existentes. El planificador `scheduler` emite tareas; el worker ejecuta descargas y análisis. Los trabajos pendientes y leases vencidos se recuperan sin incluir archivos ni secretos en Redis.

La implementación usa firma S3 SigV4, HTTPS, validación de direcciones públicas y conexión a IP validada conservando TLS/SNI. No acepta redirecciones ni endpoints internos. Las importaciones se serializan por conexión; el worker productivo conserva concurrencia máxima uno.

## Recursos demo y aceptación

`scripts/prepare_bucket_demo.py` genera por defecto un inventario offline en `.runtime/bucket-demo-manifest.json`. Con `--upload --credentials-file /ruta/privada/r2.json` carga y verifica los recursos sintéticos mediante lectura posterior y SHA-256; `--create-bucket` crea el bucket configurado cuando se necesita.

El archivo privado requiere `endpoint`, `bucket`, `region`, `access_key` y `secret_key`. Para esta carga inicial necesita escritura; las conexiones de evaluación deben usar credenciales de lectura/listado. Los prefijos son `demo/v1/police/`, `nursing/`, `memory/` y `qa/`; el directorio social y el taller están en `demo/v1/social-directory/`. No se modifican los escenarios existentes ni se copian recursos personales/Facebook. Los JSON de escenario son referencias de preparación, no expedientes importados automáticamente por el explorador multimedia.

Prueba en QA: conectar → comprobar acceso → previsualizar → importar imagen/video → esperar análisis → buscar → repetir importación → cambiar un objeto → actualizar → desconectar. Repite desde otra cuenta para comprobar que no accede a la conexión. La carga R2 y la prueba física solo se consideran aprobadas con evidencia de ejecución; consulta [estado](IMPLEMENTATION_STATUS.es.md).

Después de verificar la carga, el responsable ejecuta `scripts/connect_demo_buckets.py --apply --read-credentials-file /ruta/privada/r2-readonly.json` en el entorno del backend con `DATABASE_URL` y `STORAGE_ENCRYPTION_KEY`. Prepara conexiones privadas para las nueve cuentas de escenario y las cuatro QA existentes. Sin `--apply` solo comprueba las cuentas. Es idempotente; no crea usuarios, publicaciones, grupos ni enrolamientos. Las credenciales de lectura pueden usar el mismo formato JSON que las de carga, pero deben tener permisos de lectura/listado. El evaluador recibe las conexiones listas en **Mis conexiones**.

La preparación local inventaría **426 recursos sintéticos**; la cifra depende de los medios generados presentes en el host. El manifiesto identifica cada archivo y su SHA-256. No se borran originales de la base de datos ni se sustituyen escenarios por conexiones vacías.

Referencia del proveedor: [API S3 de Cloudflare R2](https://developers.cloudflare.com/r2/api/s3/api/) y [configuración de boto3](https://developers.cloudflare.com/r2/examples/aws/boto3/).

Una importación nueva permite volver a revisar un archivo cuyo duplicado cancelaste; repetir la solicitud original conserva la cancelación. Al confirmar todos los archivos pendientes, la importación se muestra completada. Las carpetas con espacios, Unicode y caracteres reservados conservan la firma S3 correcta.
