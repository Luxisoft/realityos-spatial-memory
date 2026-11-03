<p align="center"><a href="../../en/api/POSTMAN.md"><img src="../../assets/readme/language-en.svg" alt="English" height="32"></a> <a href="POSTMAN.md"><img src="../../assets/readme/language-es-active.svg" alt="Español" height="32"></a></p>

# Postman: servidor y localhost

[API y datos precargados](API.md#quick-start) · [Documentación](../INDEX.md)

1. [Descarga e importa la colección pública](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json).
2. Deja **No environment** y abre **Server requests** o **Localhost requests**.
3. En **00 Quick start**, abre una petición y pulsa **Send**. URL, cuenta, contraseña, workspace y pregunta ya están configurados; login y renovación son automáticos.

**Server requests → 00 Live scenarios** conserva Police, Nursing y Memory con consultas sobre datos existentes. Cada destino contiene las 176 operaciones del servidor; localhost añade sus dos operaciones exclusivas. Los inicios rápidos y escenarios reutilizan esas operaciones.

Localhost apunta a `http://localhost:8080` y usa su propia cuenta. El backend local debe estar iniciado; si falta la cuenta Postman, ejecuta una vez `scripts/local/Enable-PostmanDemo.ps1`. No se copian datos ni credenciales del servidor.

| Descarga | Uso |
| --- | --- |
| [Colección principal](../../postman/RealityOS.postman_collection.json) | Ambas carpetas completas y datos precargados. |
| [Entorno servidor opcional](../../postman/RealityOS.public.postman_environment.json) | Variables del servidor y sus escenarios. |
| [Entorno localhost opcional](../../postman/RealityOS.local.postman_environment.json) | Variables y credenciales locales. |
| [Referencia adicional](../../postman/RealityOS.reference.postman_collection.json) | Copia de las 354 plantillas API originales. |

Las operaciones avanzadas con archivos, dispositivos e integraciones conservan sus requisitos. Cambiar las variables por datos propios es opcional para los inicios rápidos y escenarios listos.

Para **crear otra cuenta**, completa las variables `registration_email`, `registration_username`, `registration_password` y `registration_display_name` con el prefijo del destino (`server_` o `localhost_`). Son independientes del acceso del jurado. Reenviar la confirmación usa `registration_email`; recuperar la contraseña usa `account_email`, siempre un correo real. Los endpoints de correo no aceptan el nombre de usuario como dirección de entrega.

Login y renovación actualizan los tokens en todos los ámbitos de Postman, incluidas las variables locales de una ejecución. Si tienes una colección anterior, vuelve a importarla para incorporar esta corrección; una segunda renovación debe utilizar el token nuevo.

## Fotos de perfil y referencias

En el catálogo del destino elegido, usa **Facial recognition** y **Profiles and social**. Para ejecutar escrituras, cambia `server_enable_write_requests` o `localhost_enable_write_requests` a `true` solo en el destino correspondiente.

1. Consulta `GET /v1/faces/consent` y envía `POST /v1/faces/consent` con `confirm=true` después de aceptar el consentimiento.
2. Envía el retrato a `POST /v1/faces/profile-photo` para registrar el rostro y a `POST /v1/me/profile/avatar` para la foto visible.
3. Envía cada referencia por separado a `POST /v1/faces/reference-photos`: selecciona **Body → form-data → file → File**. No agregues manualmente `Content-Type`; Postman construye el multipart.
4. Consulta `GET /v1/faces/setup`: `accepted_photos` cuenta las imágenes distintas aceptadas, no los intentos. Necesitas entre 3 y 25; cada foto debe mostrar un solo rostro que coincida con el perfil. Un duplicado no aumenta el contador; un 422 incluye el motivo en `detail`.
5. Envía `POST /v1/faces/setup/complete` y comprueba `complete=true`. Las referencias permanecen privadas.

## Publicaciones y grupos

Los ejemplos de publicar, compartir y preparar una carga incluyen `workspace_id`, que debe identificar un grupo existente al que pertenezca la cuenta. Para cargar imágenes o videos usa `POST /v1/me/publication-uploads`; selecciona `file`, conserva el grupo y utiliza un `request_key` distinto para cada nueva carga. Un 202 requiere consultar el estado de esa carga. Para importar publicaciones propias en otro grupo usa `POST /v1/groups/{workspace_id}/publications/import` con sus IDs.

## Comprobar vigencia

El catálogo se genera desde `tests/contracts/openapi.json`. Ejecuta `make docs-check` y las pruebas `tests/test_api_documentation.py` y `tests/test_postman_current_examples.py`; verifican rutas, campos, autenticación, separación de destinos y ejemplos de publicación. El contrato se compara también con la aplicación en `tests/test_architecture_contract.py`. [OpenAPI del servidor](https://realityos.luxisoft.com/v1/openapi.json).
