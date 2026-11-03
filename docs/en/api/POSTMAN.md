<p align="center"><a href="POSTMAN.md"><img src="../../assets/readme/language-en-active.svg" alt="English" height="32"></a> <a href="../../es/api/POSTMAN.md"><img src="../../assets/readme/language-es.svg" alt="Español" height="32"></a></p>

# Postman: server and localhost

[API and prefilled values](API.md#quick-start) · [Documentation](../INDEX.md)

1. [Download and import the public collection](https://raw.githubusercontent.com/Luxisoft/realityos-spatial-memory/main/docs/postman/RealityOS.postman_collection.json).
2. Leave **No environment** selected and open **Server requests** or **Localhost requests**.
3. Under **00 Quick start**, open a request and click **Send**. URL, account, password, workspace and question are prefilled; login and renewal are automatic.

**Server requests → 00 Live scenarios** retains Police, Nursing and Memory with queries against existing data. Each destination contains the 176 server operations; localhost adds its two exclusive operations. Quick starts and scenarios reuse those operations.

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

Login and refresh update tokens in all Postman scopes, including local variables during a collection run. Reimport an older collection to include this correction; a second refresh must use the new token.

## Profile pictures and references

In the selected destination catalog, use **Facial recognition** and **Profiles and social**. To execute writes, set `server_enable_write_requests` or `localhost_enable_write_requests` to `true` only for the intended destination.

1. Read `GET /v1/faces/consent` and send `POST /v1/faces/consent` with `confirm=true` after accepting consent.
2. Send the portrait to `POST /v1/faces/profile-photo` to register the face and to `POST /v1/me/profile/avatar` for the visible picture.
3. Send each reference separately to `POST /v1/faces/reference-photos`: choose **Body → form-data → file → File**. Do not manually add `Content-Type`; Postman builds the multipart boundary.
4. Read `GET /v1/faces/setup`: `accepted_photos` counts distinct accepted images, not attempts. You need 3–25; each photo must contain exactly one face matching the profile. A duplicate does not increase the count; a 422 explains the reason in `detail`.
5. Send `POST /v1/faces/setup/complete` and check `complete=true`. References remain private.

## Publications and groups

The publish, share and upload preparation examples include `workspace_id`, which must identify an existing group the account belongs to. To upload images or videos, use `POST /v1/me/publication-uploads`; select `file`, retain the group and use a different `request_key` for each new upload. A 202 requires checking that upload's status. To import your own publications into another group, use `POST /v1/groups/{workspace_id}/publications/import` with their IDs.

## Checking freshness

The catalog is generated from `tests/contracts/openapi.json`. Run `make docs-check` and the tests in `tests/test_api_documentation.py` and `tests/test_postman_current_examples.py`; they check routes, fields, authentication, destination isolation and publication examples. The contract is also compared against the application in `tests/test_architecture_contract.py`. [Server OpenAPI](https://realityos.luxisoft.com/v1/openapi.json).
