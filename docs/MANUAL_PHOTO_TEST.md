# Manual photo test

This test is deliberately opt-in. Staging a photo does not register it, start a
capture session, send it to Meta, or make it visible in RealityOS.

## Stage photos

On the RealityOS server, use the private, Git-ignored directory:

```text
/var/lib/realityos/manual-captures/incoming/
```

Upload only original photos you are authorized to use. Do not stage photos that
show people, credentials, customer data, or unrelated private material. The API
accepts JPEG, PNG and WebP up to 10 MiB each.

```bash
scp ./taladro-amarillo.jpg \
  jmarin@backend.com:/var/lib/realityos/manual-captures/incoming/
```

## Register and process deliberately

Run this on the RealityOS server after confirming capture consent. It prompts
for the RealityOS account password and never writes it to disk. `--process`
starts Muse Spark and SAM processing; omit it to store capture evidence only.

```bash
cd /var/www/realityos-spatial-memory
.venv/bin/python scripts/import_manual_photos.py \
  --confirm-consent --process --wait \
  --workspace "Taller RealityOS" --zone "Bodega A" \
  /var/lib/realityos/manual-captures/incoming/taladro-amarillo.jpg
```

Use a second photo in a distinct zone for an explicit “last seen” history test.
The importer opens and closes one capture session, uses the regular authorized
API, and prints capture/job IDs. It never scans the staging directory or starts
capture automatically.

## Verify

Use the Web panel or `POST /v1/queries` with “¿Dónde está el taladro amarillo?”.
The response must identify the evidence as “last seen”, return a highlighted
BYTEA-backed image, and never claim that the object is currently present.
