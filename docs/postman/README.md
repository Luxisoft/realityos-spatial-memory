<p align="center"><a href="README.md"><img src="../assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="README.es.md"><img src="../assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# Postman: import and test

[API / steps](../API.md) · [Documentation index](../README.md)

| Download | Usage |
| --- | --- |
| [↓ RealityOS.postman_collection.json](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json) | Full collection and quick start |
| [↓ RealityOS.public.postman_environment.json](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.public.postman_environment.json) | Optional: server with included public demo account |
| [↓ RealityOS.local.postman_environment.json](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.local.postman_environment.json) | Optional: localhost with included demo account; requires local setup |

**To start, import only the collection and select No environment.** Open **Server requests → 00 Quick start** and click **Send** on a request. The account, password and IDs are already included; sign-in and token renewal run automatically. Use **Run** to execute the whole subfolder.

[Buttons and expected results →](../API.md#quick-start). The public account uses an empty workspace; to try the app with prepared photos, posts and groups, use [scenario accounts](../DEMO.md#access).

The environments in the table are optional. For your own account, change its variables and sign in again. Writes require `server_enable_write_requests=true` or `localhost_enable_write_requests=true` and account permissions. Response examples are synthetic.
