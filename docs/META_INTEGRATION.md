# Meta Model API integration

The Live provider is isolated in backend/app/meta.py. It applies Bearer
authentication, explicit timeout, exponential retry for transient errors,
Pydantic validation and client-safe failures. API keys never reach a browser or
Android project.

- Muse Spark 1.3 uses the Responses API with image data URLs for visual analysis.
- SAM 3.1 is used only by an explicit, authorized refinement job. RealityOS
  sends the selected image plus Muse Spark's existing box as an official box
  prompt, requests SSE with `mask_encoding=one_bit`, decodes it with Meta's
  `meta-sam-parser` Python package and stores the mask as a related PNG BYTEA.
  Query endpoints never enqueue this job or write the cache.
- Muse Voice Transcribe uses the ASR transcription endpoint with multipart
  request JSON and WAV audio in PUSH_TO_TALK mode.

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
