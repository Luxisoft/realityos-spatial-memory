<p align="center"><a href="../../en/api/API.md"><img src="../../assets/readme/language-en.svg" alt="English" height="32"></a> <a href="API.md"><img src="../../assets/readme/language-es-active.svg" alt="Español" height="32"></a></p>

# API de RealityOS

**Consulta personas, expedientes y evidencia visual desde tus herramientas.** Esta guía explica qué enviar, qué esperar y cómo comenzar. Los permisos son los mismos que en Android.

[📥 Colección Postman](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json) · [Entornos opcionales](POSTMAN.md) · [Referencia completa](API_REFERENCE.md) · [Índice](../INDEX.md)

<a id="quick-start"></a>

## Servidor y localhost: Import → Send

**La colección tiene exactamente dos carpetas principales: Server requests y Localhost requests.** Ambas incluyen el catálogo completo y un inicio rápido con URL, usuario, contraseña, workspace y pregunta precargados. Server requests conserva además las 39 consultas listas sobre los datos existentes del jurado.

1. En Postman, pulsa **Import** y pega este enlace:

   ```text
   https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json
   ```

2. Deja seleccionado **No environment**. Abre **Server requests → 00 Quick start** o **Localhost requests → 00 Quick start**. Para los tres escenarios existentes: **Server requests → 00 Live scenarios → 01 Police / 02 Nursing / 03 Memory**.
3. Abre cualquier petición y pulsa **Send**. El acceso y la renovación son automáticos. Puedes usar **Run** para ejecutar una carpeta completa.

| Carpeta | Usuario incluido | Contraseña incluida | Espacio existente |
| --- | --- | --- | --- |
| 01 Police | `alex-rivera` | `liMPaFG6f8KPbzSRcNFFpdu74dHmVxU5` | Pacific Ridge Police Department |
| 02 Nursing | `elena-marquez` | `GS112vlwNHjj4tVuaxDZrOpTs0s7lomj` | California Valley Medical Center |
| 03 Memory | `noah-brooks` | `FqgO_9etDGlTkZDJj_MxYGekwFatXNMB` | Sonoran Neurological Institute |

Estas tres cuentas de evaluación y sus contraseñas son públicas por autorización del propietario del 3 de noviembre de 2026. Conservan su rol actual de administrador en su espacio. La colección de evaluación consulta datos existentes. Los proveedores y el servidor son reales; las personas y escenas preparadas conservan su procedencia ficticia.

Cada escenario de **Server requests → 00 Live scenarios** permite probar sesión, login, renovación, espacios, listado y detalle de expedientes, revisiones, publicaciones, descarga de una imagen, perfiles y consultas de IA. Policía abre el caso 1; Enfermería abre Ana Solis; Memoria abre Luis Moreno. El servidor contiene 47 expedientes y 21 publicaciones de grupo. Las respuestas se obtienen del servidor al enviar la petición.

Los entornos opcionales de [servidor](../../postman/RealityOS.public.postman_environment.json) y [localhost](../../postman/RealityOS.local.postman_environment.json) contienen las variables de cada destino. Para usar otra cuenta, cambia sus variables; hacerlo es completamente opcional. [Acceso Android con estas cuentas](../guides/DEMO.md#access).

## Destinos precargados

| Carpeta principal | URL | Cuenta y espacio |
| --- | --- | --- |
| Server requests | `https://realityos.luxisoft.com` | El inicio rápido usa la cuenta existente de Memoria. Los tres escenarios conservan sus cuentas y datos. |
| Localhost requests | `http://localhost:8080` | `postman-local@realityos.example.test`, contraseña `RealityOS-Postman-Local-2026!` y su workspace local están precargados. |

Para localhost debe estar iniciado el backend local. Si esa instalación aún no tiene la cuenta Postman, ejecuta una vez `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\local\Enable-PostmanDemo.ps1`; después basta Send. El script prepara la cuenta local existente del flujo de instalación; no copia datos ni claves del servidor. La colección no puede iniciar por sí misma el backend de otro equipo.

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

[Todos los métodos, campos y respuestas declaradas →](API_REFERENCE.md)

## Variables y autenticación

Los prefijos `server_` y `localhost_` separan los destinos. Los escenarios del servidor conservan `security_`, `hospital_` y `memory_`. Los inicios rápidos y escenarios tienen sus valores precargados; las sesiones se mantienen separadas. Solo los tokens y `session_identity` empiezan vacíos: el script los obtiene automáticamente antes de enviar una petición protegida. Un fallo de autenticación detiene la petición. Cambiar la cuenta o URL inicia otra sesión.

`query` es la pregunta visual y `record_question` consulta expedientes; `language=en` solicita respuestas de IA en inglés. Las observaciones indican «visto por última vez». Una respuesta sin coincidencias no inventa evidencia.

## Referencia completa para integradores

La colección principal contiene las 354 plantillas API y las 39 consultas de los escenarios: 393 en total. El catálogo completo permanece dentro de cada destino. La [colección de referencia](../../postman/RealityOS.reference.postman_collection.json) también sigue disponible. Esas plantillas requieren los permisos, archivos y credenciales propios de cada operación. Sus entornos opcionales son [servidor](../../postman/RealityOS.reference.postman_environment.json) y [localhost](../../postman/RealityOS.local.postman_environment.json). No es necesario importar entornos para usar las carpetas de la colección principal.

Las escrituras de la referencia conservan `enable_write_requests=false`. La [instalación Windows](../deployment/DEPLOYMENT_LOCALHOST.md) sigue siendo opcional y no se necesita para evaluar los datos del servidor.

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

[Swagger interactivo](https://realityos.luxisoft.com/docs) · [OpenAPI](https://realityos.luxisoft.com/v1/openapi.json) · [Contrato versionado](../../../tests/contracts/openapi.json) · [Datos e importaciones](../guides/WORKSPACE_DATA.md)

Regenera la referencia y Postman con `python scripts/build_api_docs.py`; verifica diferencias con `python scripts/build_api_docs.py --check`. La colección usa el [formato oficial v2.1](https://schema.postman.com/); la [guía de importación](https://learning.postman.com/docs/getting-started/importing-and-exporting/importing-data/) explica el flujo de Postman.

Prueba offline de scripts: `node scripts/check_postman_scripts.cjs`.
