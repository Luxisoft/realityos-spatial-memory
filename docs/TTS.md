# Voz por ElevenLabs y transcripción por Meta

Producción conserva Muse Voice Transcribe para audio → texto, Muse Spark para
interpretación/respuestas y SAM 3.1 para segmentación. Solo texto → voz pasa a
ElevenLabs, sin pesos de síntesis residentes en este servidor.

## Contrato y configuración

Android, panel y Display conservan `POST /v1/tts` autenticado por usuario o
dispositivo: `{text, language}` (`en`/`es`) devuelve WAV PCM mono a 24 kHz.
La síntesis no crea capturas, evidencia, mensajes, cachés de audio ni medios
persistidos. La alternativa de voz de Android/navegador permanece disponible
ante indisponibilidad del proveedor.

```dotenv
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb
ELEVENLABS_MODEL_ID=eleven_flash_v2_5
TTS_TIMEOUT_SECONDS=30
```

La credencial `ELEVENLABS_API_KEY` vive únicamente en `.env.elevenlabs`, archivo
privado modo 0600 inyectado en el API mediante Compose de producción. No se
versiona ni se envía a clientes o al gateway. Se reutiliza la cuenta de Luxisoft
por instrucción del propietario. CI preserva ese archivo y toma la selección
del proveedor de `.env`.

Cada solicitud autorizada llama directamente a
`https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_24000`,
con `xi-api-key`, texto, idioma y modelo. La biblioteca estándar añade la
cabecera WAV; no se cargan modelos, PyTorch ni conversores locales para voz.
Esta selección no depende de `META_CONNECTION_MODE` ni altera el respaldo Meta.

Se permiten dos generaciones simultáneas por proceso, sin cola de espera,
un presupuesto HTTP total de 30 segundos, hasta 300 segundos de audio y una
respuesta WAV de hasta 16 MiB. No hay reintentos automáticos de generación,
incluidos los fallos ambiguos, para evitar cobros duplicados. Los errores se
traducen a indisponibilidad sin exponer texto, secretos o respuestas internas.
Los logs incluyen proveedor, tiempo, identificador y character-cost disponible.

Nginx limita `/v1/tts` a 30 peticiones/minuto por IP con ráfaga de cuatro.
El antiguo `/tts/synthesize` con token de servicio se retira con HTTP 410;
producción ya no depende de 8091 ni del circuito de voz por FRONTEND que
regresaba al mismo motor local. El gateway Meta para visión/STT se conserva.

## Ejecución

La síntesis usa exclusivamente ElevenLabs tanto en producción como en la
instalación Windows. Esta última solicita una clave propia en `.env.local`;
no copia credenciales del servidor. No hay contenedor, pesos, dependencias de
inferencia, perfil Compose ni compilaciones de un modelo de voz local.

El 2026-11-02 el propietario solicitó eliminar por completo Seamless después
de verificar ElevenLabs y Muse Voice Transcribe. Se retiraron el código,
contenedor, imagen y volumen de pesos, además de los trabajos de CI y opciones
locales. Las menciones antiguas en el historial de implementación describen
releases retirados y no son instrucciones vigentes.

Referencias: [ElevenLabs Create speech](https://elevenlabs.io/docs/api-reference/text-to-speech/convert)
y [Meta Model API](https://dev.meta.ai/docs/overview).
