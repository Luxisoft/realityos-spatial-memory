<p align="center"><a href="API.md"><img src="assets/readme/language-en.svg" alt="English" height="32"></a> <a href="API.es.md"><img src="assets/readme/language-es-active.svg" alt="Español" height="32"></a></p>

# API de RealityOS

**Consulta personas, expedientes y evidencia visual desde tus herramientas.** Esta guía explica qué enviar, qué esperar y cómo comenzar. Los permisos son los mismos que en Android.

[📥 Colección Postman](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json) · [Entornos opcionales](postman/README.es.md) · [Referencia completa](API_REFERENCE.es.md) · [Índice](README.es.md)

<a id="quick-start"></a>

## Primera prueba: importar y ejecutar

**Usa Postman de escritorio y el servidor ya instalado.** La cuenta pública comprueba acceso y consultas en un espacio vacío. Para ver fotos, publicaciones y expedientes preparados en Android, usa la [guía de cuentas de escenario](DEMO.es.md#access).

1. En Postman, abre **Import** (en versiones recientes, **Use resources or import → Import**) y pega este enlace:

   ```text
   https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json
   ```

2. Confirma la importación y deja el selector de entorno en **No environment**. Usuario, contraseña y espacio ya vienen en la colección.
3. Abre **Server requests → 00 Quick start** y pulsa **Run**. Ejecuta las cinco solicitudes de esa subcarpeta, en el orden incluido, una vez. Si aparece **Start run**, úsalo para comenzar.
4. Comprueba las respuestas:

Si tu colección anterior muestra **Consultas servidor / Consultas localhost**, son las mismas carpetas; **00 Quick start / Inicio rápido** es el mismo inicio rápido.

| Solicitud | Resultado esperado |
| --- | --- |
| `GET /health/live` | `200`: servidor disponible. |
| `POST /v1/auth/login` | `200`: inicio de sesión; guarda los tokens automáticamente. |
| `GET /v1/auth/me` | `200`: cuenta de prueba autenticada. |
| `GET /v1/workspaces` | `200`: aparece **Postman Demo - public test workspace**. |
| `POST /v1/queries` | `200`: consulta sin coincidencias porque este espacio está vacío. |

**Acceso incluido:** `postman-demo@realityos.example.test` / `RealityOS-Postman-Demo-2026!`. Es una cuenta compartida con permiso de consulta en su espacio, sin administración ni captura. Ya está confirmada; su dirección `example.test` no recibe correo. Los [pasos oficiales de importación](https://learning.postman.com/docs/getting-started/importing-and-exporting/importing-data/) y [ejecución de carpetas](https://learning.postman.com/docs/tests-and-scripts/running-collections/intro-to-collection-runs/) detallan los controles de Postman.

### Consultar un escenario con datos preparados

En **Collection → Variables**, pon el usuario de tu ficha en `server_email` y su contraseña en `server_password`. Vacía `server_access_token` y `server_refresh_token`. Ejecuta **login** y después **GET /v1/workspaces**; copia el ID del grupo asignado a `server_workspace_id` antes de ejecutar la consulta. Las fotos y expedientes de ese grupo ya están cargados; la cuenta pública no tiene acceso a ellos.

<details>
<summary><strong>Opcional: probar tu instalación localhost</strong></summary>

Primero completa la [instalación Windows](DEPLOYMENT_LOCALHOST.es.md). Después, desde la raíz del repositorio, ejecuta una sola vez:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Enable-PostmanDemo.ps1
```

Ejecuta **Localhost requests → 00 Quick start**. Esta carpeta usa `http://localhost:8080`, `postman-local@realityos.example.test` y `RealityOS-Postman-Local-2026!`, ya incluidos. Crea una cuenta local de consulta y un espacio vacío independiente. No copia los escenarios ni las credenciales del servidor.

</details>

<details>
<summary><strong>Opcional: entornos y cuenta propia</strong></summary>

Los archivos de entorno descargables contienen las mismas variables demo y son opcionales. Un entorno activo prevalece sobre la colección: edita sus valores o vuelve a **No environment** para evitar mezclar cuentas. Los tokens se guardan tras el login; no se publican en GitHub. Una cuenta propia nueva requiere confirmar un correo real. [Alcance de variables de Postman](https://learning.postman.com/docs/sending-requests/variables/variables/).

</details>

## Qué operación necesito

| Quiero… | Solicitud | Qué obtengo / necesito |
| --- | --- | --- |
| Verificar disponibilidad | `GET /health/live` · `GET /health/ready` | Estado del proceso y disponibilidad de la base de datos. |
| Acceder o renovar sesión | `POST /v1/auth/login` · `/v1/auth/refresh` | Tokens; la renovación rota el refresh token anterior. |
| Elegir organización | `GET /v1/workspaces` | IDs y rol de mis espacios. |
| Buscar un rostro | `POST /v1/faces/search` | Candidatos `matches` y `matches_records`; requiere autorización y enrolamientos previos. |
| Abrir un expediente | `GET /v1/workspaces/{workspace_id}/records/{record_id}` | Datos, fuente y relaciones autorizados. |
| Consultar expedientes | `POST /v1/workspaces/{workspace_id}/records/search` | Respuesta contextual con referencias permitidas. |
| Encontrar un objeto | `POST /v1/queries` · `/v1/queries/image` · `/v1/queries/audio` | Última evidencia observada, no ubicación actual garantizada. |
| Registrar evidencia | `POST /v1/sessions` → `/v1/captures` → `/v1/captures/{capture_id}/process` | Original guardado y trabajo de análisis; requiere rol y sesión consentida. |
| Ver progreso | `GET /v1/jobs/{job_id}` | Estado del trabajo solicitado; no confundir 202 con trabajo terminado. |
| Consultar un perfil | `GET /v1/profiles/{user_id}` | Proyección visible; no devuelve el archivo privado de CV. |
| Importar datos propios | `POST /v1/integrations/imports` | Lote versionado e idempotente con clave de integración. |
| Escuchar una respuesta | `POST /v1/tts` | WAV de ElevenLabs; requiere autenticación y consume proveedor. |

[Todos los métodos, campos y respuestas declaradas →](API_REFERENCE.es.md)

## Variables y autenticación

Todas las variables llevan `server_` o `localhost_`. Cada carpeta referencia exclusivamente su prefijo, incluidos tokens, IDs y controles de escritura. Las rutas locales adicionales solo aparecen dentro de **Localhost requests → Local installation only**.

| Variable (añadir el prefijo) | Valor o uso |
| --- | --- |
| `base_url` | URL preconfigurada, sin `/v1`. Si cambias `LOCAL_HTTP_PORT`, actualiza `localhost_base_url`. |
| `email`, `username`, `password`, `display_name` | Cuenta demo preconfigurada; sustituibles por tu cuenta. |
| `access_token`, `refresh_token` | Se guardan por destino después de login y renovación correctos, incluso sin entorno activo. |
| `user_id`, `workspace_id` | IDs de la cuenta y espacio demo; se mantienen separados por destino. |
| `query`, `language` | Pregunta de ejemplo e idioma (`en` o `es`), editables. |
| `new_email`, `new_password` | Destino nuevo o contraseña nueva para corregir/recuperar una cuenta propia; no reemplazan las credenciales actuales. |
| Otros IDs | Declarados y descritos; completar con respuestas autorizadas. No hay IDs ficticios de medios o expedientes inexistentes. |
| `device_id`, `device_key`, `integration_key`, `facebook_access_token`, `token` | Se obtienen al provisionar el dispositivo/integración, iniciar Facebook o recibir un enlace; no son credenciales de la demo. |
| `enable_write_requests` | `false` inicialmente; el control es independiente por destino. |

[Preparar la instalación Windows](DEPLOYMENT_LOCALHOST.es.md). La colección no instala el backend local.

## Archivos, ejemplos y ejecución

- En **Body → form-data**, selecciona tu archivo en el campo de tipo File. Activa el campo si es opcional y desactivado. Postman añade el `Content-Type` multipart y su boundary.
- Consulta por imagen: JPEG/PNG/WebP; consulta de voz: WAV. Capturas admiten imagen y video conforme al contrato. Los CV aceptan PDF/DOCX.
- Los cuerpos incluidos son plantillas sintéticas: completa los campos y sustituye IDs antes de enviar. Para un rostro, selecciona una foto/video autorizado o un medio existente; una imagen de enrolamiento repetida solo prueba integración.
- Las escrituras se omiten mientras `server_enable_write_requests=false` / `localhost_enable_write_requests=false`. Actívalo explícitamente para una prueba de captura, enrolamiento o administración. Ejecuta primero una solicitud individual; ejecutar toda la colección incluye operaciones de alta, revocación y borrado.
- Consultas con IA, transcripción y voz pueden consumir proveedores aunque no creen evidencia. La colección no hace llamadas por el mero hecho de importarla.
- Un 200 puede contener `found=false`, resultados parciales o `simulated`. Revisa el cuerpo, la fuente y la fecha. La similitud facial no es probabilidad de identidad.

## Resolver problemas

| Resultado | Qué revisar |
| --- | --- |
| 401 | Sesión ausente, vencida o revocada; renovar o iniciar sesión. |
| 403 | Rol, pertenencia o consentimiento insuficiente; otra credencial no amplía tus permisos. |
| 404 | ID/ruta inexistente, recurso no accesible o ruta local usada en producción. |
| 409 | Conflicto de versión, duplicado o clave idempotente reutilizada con otro contenido. |
| 422 | Campos, formato, límites o calidad del archivo; leer `detail`. |
| 429 | Límite de solicitudes o intentos; respetar la espera indicada. |
| 5xx / trabajo fallido | Disponibilidad del servicio/proveedor; revisar el trabajo antes de repetir una operación con coste. |

## Contrato y mantenimiento

[Swagger interactivo](https://realityos.luxisoft.com/docs) · [OpenAPI](https://realityos.luxisoft.com/v1/openapi.json) · [Contrato versionado](../tests/contracts/openapi.json) · [Datos e importaciones](WORKSPACE_DATA.es.md)

Regenera la referencia y Postman con `python scripts/build_api_docs.py`; verifica diferencias con `python scripts/build_api_docs.py --check`. La colección usa el [formato oficial v2.1](https://schema.postman.com/); la [guía de importación](https://learning.postman.com/docs/getting-started/importing-and-exporting/importing-data/) explica el flujo de Postman. Las notas originales permanecen en [referencia histórica](reference/API.legacy.md).

Prueba offline de scripts: `node scripts/check_postman_scripts.cjs`.
