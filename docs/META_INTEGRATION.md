# Meta Model API integration

The Live provider is isolated in backend/app/meta.py. It applies Bearer
authentication, explicit timeout, exponential retry for transient errors,
Pydantic validation and client-safe failures. API keys never reach a browser or
Android project.

- Muse Spark 1.3 uses the Responses API with image data URLs for visual analysis
  and validated structured facts. A fact is omitted when brand/model/text/count
  cannot be supported by visible evidence.
- For captured-object evidence, SAM 3.1 is used by an explicit, authorized refinement job. RealityOS
  sends the selected image plus Muse Spark's existing box as an official box
  prompt, requests SSE with `mask_encoding=one_bit`, decodes it with Meta's
  `meta-sam-parser` Python package and stores the mask as a related PNG BYTEA.
  Query endpoints never enqueue this job or write the cache.
- Muse Voice Transcribe uses the ASR transcription endpoint with multipart
  request JSON and WAV audio in PUSH_TO_TALK mode.
- Detailed video mode creates temporary faststart MP4 clips, uploads them to
  Files API with `purpose=user_data`, sends their `file_id` to SAM 3.1 through
  Responses streaming, and deletes them after the attempt. SAM's decoded masks
  are retained as RealityOS RLE geometry; source video pixels remain BYTEA.
  File upload or stream failures after submission become `uncertain` and are
  deliberately not retried automatically.

The model IDs and endpoint contracts were checked against official Meta
[overview](https://dev.meta.ai/docs/overview),
[SAM guide](https://dev.meta.ai/docs/sam/overview) and
[voice reference](https://dev.meta.ai/docs/api-reference/voice/transcribe) on
2026-10-26. A deployment-time credential check reached Models successfully, but
its model list was empty and a Muse Spark 1.3 request returned model_not_found.
The original RealityOS host received an empty model catalog from its egress IP,
while the same credential worked from an alternate network. A restricted
gateway is therefore implemented for `meta.luxisoft.com`; it is not deployed
until FRONTEND's preflight returns an enabled model catalog. See
[Gateway](GATEWAY.md).

META_MODE=mock is deterministic and makes no HTTP call. Each mock result is
marked simulated.


Gallery publication analysis (2026-10-30) is a separate background workflow:
Muse identifies visible objects, then SAM localizes their instance boxes in a
single multi-object image request. Video uses decoder PTS on sampled/scene
frames; Query never queues grounding. Meta also compares new photos against
local visual-hash candidates before publication. Empty candidate sets always
request an explicit JSON verdict; a bare JSON null is accepted only for an
empty set. Invalid/uncertain comparisons with actual candidates remain failed
and require an explicit retry. Live checks covered exact-photo comparison,
a 13-object photo and a 13-object workshop video frame. This is not a claim of
perfect detection or physical-device validation.


El visor de Buscar traduce únicamente textos autorizados (títulos, notas y
etiquetas seleccionadas) mediante Muse Spark Responses con `store=false`.
El contrato JSON de `POST /v1/responses`, `instructions` e `input` se comprobó
contra la documentación oficial de
[Responses](https://dev.meta.ai/docs/protocols/responses) el 2026-10-30.
Se valida la correspondencia exacta de claves de traducción; una respuesta
incompleta queda como no disponible. No se envían imágenes para traducir ni se
vuelven a detectar objetos. Las traducciones no se persisten como evidencia.


Corrección de 2026-10-30: la preparación bilingüe se ejecuta al publicar o en
procesos explícitos de indexación/mantenimiento. Muse devuelve ambos mapas
`en`/`es` en una sola respuesta validada, que se persiste antes de completar una
publicación nueva. El endpoint de información ya no llama a Meta; solo lee la
base de datos. Los datos existentes se preparan mediante el script reanudable
`prepare_publication_languages.py`, independiente del visor y de Query.

Gallery SAM limit correction (2026-10-31): official
[box/point prompt limits](https://dev.meta.ai/docs/sam/segmenting) permit at most
16 prompted objects. Live reproduction returned
`invalid prompt: 28 objects exceed this model's limit of 16`. Gallery calls now
partition all candidates into groups of at most 16 and map each result to its
original candidate. HTTP 400 preserves the provider reason and is never retried
unchanged. Accepted incomplete SAM streams remain uncertain; explicit background
repair can resume completed frames.

Omitted objects receive an explicit visual review. Small/uncertain objects are
reviewed at source pixel detail; segmentation of small confirmed instances also
uses a source crop, with boxes transformed back to original image coordinates.
Full-size evidence retains the original image dimensions. Confirmation and SAM
confidence thresholds remain unchanged. A rejected prior object requires an
explicit high-confidence rejection; uncertainty cannot remove an active object.

Search processing recovery (2026-10-31): confirmed prior objects with weak box
segmentation receive a separate SAM concept request on a crop of their original
pixels. This uses one noun phrase per request, following the official
[concept prompt rules](https://dev.meta.ai/docs/sam/segmenting). Only nonempty
masks meeting the existing confidence threshold and overlapping the confirmed
instance by at least 0.5 IoU are accepted. A different nearby object cannot
satisfy this fallback. Visual and localization confidence stay separate.
Confident explicit rejections are retained instead of being overwritten by an
ambiguous crop. Accepted incomplete streams remain explicit errors; this is
not a blind replay of the same failed request.

## Respuestas de audio

Muse Voice Transcribe se mantiene exclusivamente como STT. La generación de
voz usa ElevenLabs desde RealityOS, independiente de la conexión Meta y sin
inferencias locales de síntesis. Ver [TTS](TTS.md).

## Direct connection and automatic fallback — 2026-11-01

An authenticated same-key comparison now succeeds from RealityOS egress:
Models returns nine models and Muse Spark Responses completes with `OK`.
The historical empty-catalog restriction above no longer applies. Explicit
`META_CONNECTION_MODE=direct|gateway` selects the primary route;
`META_GATEWAY_FALLBACK_ENABLED=true` keeps FRONTEND as standby. Shared transport
covers JSON, image SSE, ASR multipart, Files and video without replaying accepted
or ambiguous streams/uploads. See [connection settings](GATEWAY.md).
