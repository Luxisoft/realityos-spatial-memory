<p align="center"><a href="POSTMAN.md"><img src="../../assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="../../es/api/POSTMAN.md"><img src="../../assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# Postman: server and localhost

[API and prefilled values](API.md#quick-start) · [Documentation](../INDEX.md)

1. [Download and import the public collection](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json).
2. Leave **No environment** selected and open **Server requests** or **Localhost requests**.
3. Under **00 Quick start**, open a request and click **Send**. URL, account, password, workspace and question are prefilled; login and renewal are automatic.

**Localhost requests → 00 Local scenarios** contains Police and Meta Social Media, generated from the installed SQL data. The disabled Server requests catalog has no active URL or credentials. Reference operations match the current OpenAPI contract; quick starts and local scenarios reuse those operations.

The live scenarios include **48 video queries in Spanish and English** with checks for the expected publication, timestamp and real evidence. See the [video matrix and results](../testing/VIDEO_EVALUATION.md) for the objects to find in each recording.

Localhost points to `http://localhost:8080` and uses its own account. The local backend must be running; if its Postman account is missing, run `scripts/local/Enable-PostmanDemo.ps1` once. Server data and credentials are not copied.

| Download | Usage |
| --- | --- |
| [Main collection](../../postman/RealityOS.postman_collection.json) | Both complete folders and prefilled values. |
| [Optional server environment](../../postman/RealityOS.public.postman_environment.json) | Server and live scenario variables. |
| [Optional localhost environment](../../postman/RealityOS.local.postman_environment.json) | Local variables and credentials. |
| [Additional reference](../../postman/RealityOS.reference.postman_collection.json) | Copy of the 354 original API templates. |

Advanced file, device and integration operations retain their prerequisites. Replacing values with your own data is optional for quick starts and ready scenarios.

To **create another account**, fill `registration_email`, `registration_username`, `registration_password` and `registration_display_name`, using the destination prefix (`server_` or `localhost_`). These are separate from jury login credentials. Resending confirmation uses `registration_email`; password recovery uses `account_email`, always a real email address. Mail endpoints cannot deliver to a login username.

Login and refresh update tokens in all Postman scopes, including local variables during a collection run. An HTTP 200 response without both tokens fails validation. Reimport an older collection to include this correction; a second refresh must use the new token.

## Profile pictures and references

In the selected destination catalog, use **Facial recognition** and **Profiles and social**. To execute writes, set `server_enable_write_requests` or `localhost_enable_write_requests` to `true` only for the intended destination.

1. Read `GET /v1/faces/consent` and send `POST /v1/faces/consent` with `confirm=true` after accepting consent.
2. Send the portrait to `POST /v1/faces/profile-photo` to register the face and to `POST /v1/me/profile/avatar` for the visible picture.
3. Send each reference separately to `POST /v1/faces/reference-photos`: choose **Body → form-data → file → File**. Do not manually add `Content-Type`; Postman builds the multipart boundary.
4. Read `GET /v1/faces/setup`: `accepted_photos` counts distinct accepted images, not attempts. You need 3–25; each photo must contain exactly one face matching the profile. A duplicate does not increase the count; a 422 explains the reason in `detail`.
5. Send `POST /v1/faces/setup/complete` and check `complete=true`. References remain private.

## Publications and groups

The publish, share and upload preparation examples include `workspace_id`, which must identify an existing group the account belongs to. To upload images or videos, use `POST /v1/me/publication-uploads`; select `file`, retain the group and use a different `request_key` for each new upload. A 202 requires checking that upload's status. To import your own publications into another group, use `POST /v1/groups/{workspace_id}/publications/import` with their IDs.

## R2/S3 connections

Creating or editing a connection includes `storage_endpoint`, `storage_bucket`, `storage_prefix`, `storage_access_key`, `storage_secret_key` and `workspace_id`, with the destination prefix. The endpoint must use public HTTPS; for R2 use the account's S3 endpoint. For S3 also change `provider` and `region`. Credentials start empty and are marked secret in the environments; fill them locally and never publish the populated environment.

Imports use `storage_object_key` from the authorized listing and a new `storage_request_key` for each attempt. Synchronization examples include the group, folder, interval and `enabled`: `false` pauses the matching rule; change it to `true` to schedule it.

## Checking freshness

The catalog is generated from `tests/contracts/openapi.json`. Run `make docs-check` and the tests in `tests/test_api_documentation.py`, `tests/test_postman_current_examples.py`, `tests/test_postman_contract_alignment.py` and `tests/test_postman_storage_examples.py`; they check every catalog against the FastAPI models, fields, authentication, destination isolation, publication and storage. Scripts require each endpoint’s declared success codes; a redirect does not count as a pass. The contract is also compared against the application in `tests/test_architecture_contract.py`. [Server OpenAPI](https://realityos.luxisoft.com/v1/openapi.json).

CI also executes the scripts in Newman's real sandbox against a local mock server. It checks repeated token rotation with and without an environment, authentication failures, response codes and disabled writes. A failed login records a failed test before skipping the protected request. To repeat it:

```bash
npm install --prefix .runtime/postman-tools --ignore-scripts --no-audit --no-fund newman@6.2.3
NODE_PATH="$PWD/.runtime/postman-tools/node_modules" make postman-runtime-check
```

This check calls neither production nor providers. Files, integration credentials and physical devices remain prerequisites for their live tests.
