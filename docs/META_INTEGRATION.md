# Meta Model API integration

The Live provider is isolated in backend/app/meta.py. It applies Bearer
authentication, explicit timeout, exponential retry for transient errors,
Pydantic validation and client-safe failures. API keys never reach a browser or
Android project.

- Muse Spark 1.3 uses the Responses API with image data URLs for visual analysis.
- SAM 3.1 uses Responses with a noun phrase and input image. Box parsing is
  implemented; binary SAM-mask decoding/persistence remains a worker extension.
- Muse Voice Transcribe uses the ASR transcription endpoint with multipart
  request JSON and WAV audio in PUSH_TO_TALK mode.

The model IDs and endpoint contracts were checked against official Meta
[overview](https://dev.meta.ai/docs/overview),
[SAM guide](https://dev.meta.ai/docs/sam/overview) and
[voice reference](https://dev.meta.ai/docs/api-reference/voice/transcribe) on
2026-10-26. A deployment-time credential check reached Models successfully, but
its model list was empty and a Muse Spark 1.3 request returned model_not_found.
The local key is retained outside Git, while runtime remains Mock until Meta
enables the required models for that account.

META_MODE=mock is deterministic and makes no HTTP call. Each mock result is
marked simulated.
