<p align="center"><a href="../../en/api/POSTMAN.md"><img src="../../assets/readme/language-en.svg" alt="English" height="32"></a> <a href="POSTMAN.md"><img src="../../assets/readme/language-es-active.svg" alt="Español" height="32"></a></p>

# Postman: servidor y localhost

[API y datos precargados](API.md#quick-start) · [Documentación](../INDEX.md)

1. [Descarga e importa la colección pública](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json).
2. Deja **No environment** y abre **Server requests** o **Localhost requests**.
3. En **00 Quick start**, abre una petición y pulsa **Send**. URL, cuenta, contraseña, workspace y pregunta ya están configurados; login y renovación son automáticos.

**Server requests → 00 Live scenarios** conserva Police, Nursing y Memory con las 39 consultas sobre datos existentes. Ambas carpetas contienen el catálogo completo: 393 solicitudes en total.

Localhost apunta a `http://localhost:8080` y usa su propia cuenta. El backend local debe estar iniciado; si falta la cuenta Postman, ejecuta una vez `scripts/local/Enable-PostmanDemo.ps1`. No se copian datos ni credenciales del servidor.

| Descarga | Uso |
| --- | --- |
| [Colección principal](../../postman/RealityOS.postman_collection.json) | Ambas carpetas completas y datos precargados. |
| [Entorno servidor opcional](../../postman/RealityOS.public.postman_environment.json) | Variables del servidor y sus escenarios. |
| [Entorno localhost opcional](../../postman/RealityOS.local.postman_environment.json) | Variables y credenciales locales. |
| [Referencia adicional](../../postman/RealityOS.reference.postman_collection.json) | Copia de las 354 plantillas API originales. |

Las operaciones avanzadas con archivos, dispositivos e integraciones conservan sus requisitos. Cambiar las variables por datos propios es opcional para los inicios rápidos y escenarios listos.
