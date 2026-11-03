<p align="center"><a href="README.md"><img src="../assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="README.es.md"><img src="../assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# Postman: server and localhost

[API and prefilled values](../API.md#quick-start) · [Documentation](../README.md)

1. [Download and import the public collection](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json).
2. Leave **No environment** selected and open **Server requests** or **Localhost requests**.
3. Under **00 Quick start**, open a request and click **Send**. URL, account, password, workspace and question are prefilled; login and renewal are automatic.

**Server requests → 00 Live scenarios** retains Police, Nursing and Memory with all 39 existing-data queries. Both destinations include the complete catalog: 363 requests in total.

Localhost points to `http://localhost:8080` and uses its own account. The local backend must be running; if its Postman account is missing, run `scripts/local/Enable-PostmanDemo.ps1` once. Server data and credentials are not copied.

| Download | Usage |
| --- | --- |
| [Main collection](RealityOS.postman_collection.json) | Both complete folders and prefilled values. |
| [Optional server environment](RealityOS.public.postman_environment.json) | Server and live scenario variables. |
| [Optional localhost environment](RealityOS.local.postman_environment.json) | Local variables and credentials. |
| [Additional reference](RealityOS.reference.postman_collection.json) | Copy of the 324 original API templates. |

Advanced file, device and integration operations retain their prerequisites. Replacing values with your own data is optional for quick starts and ready scenarios.
