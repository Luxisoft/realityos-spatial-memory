<p align="center"><a href="README.md"><img src="../assets/readme/language-en.svg" alt="English" height="32"></a> <a href="README.es.md"><img src="../assets/readme/language-es-active.svg" alt="Español" height="32"></a></p>

# Postman: importar y probar

[API / pasos / steps](../API.es.md) · [Índice / Index](../README.es.md)

| Descarga | Uso |
| --- | --- |
| [↓ RealityOS.postman_collection.json](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json) | Colección completa e inicio rápido |
| [↓ RealityOS.public.postman_environment.json](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.public.postman_environment.json) | Opcional: servidor con cuenta pública demo incluida |
| [↓ RealityOS.local.postman_environment.json](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.local.postman_environment.json) | Opcional: localhost con cuenta demo incluida; requiere instalación local |

**Para empezar, importa solo la colección y deja seleccionado No environment.** Abre **Server requests → 00 Quick start** y pulsa **Send** en una solicitud. La cuenta, contraseña e IDs ya están incluidos; el acceso y la renovación de tokens son automáticos. Usa **Run** para ejecutar toda la subcarpeta.

[Guía con botones y resultados esperados →](../API.es.md#quick-start). La cuenta pública usa un espacio vacío; para probar la app con fotos, publicaciones y grupos preparados, sigue [las cuentas de escenario](../DEMO.es.md#access).

Los entornos de la tabla son opcionales. Para una cuenta propia, cambia sus variables y vuelve a iniciar sesión. Las escrituras requieren `server_enable_write_requests=true` o `localhost_enable_write_requests=true` y permisos de la cuenta. Los ejemplos de respuesta son sintéticos.
