# Voz Seamless local y respaldo por FRONTEND

RealityOS ejecuta `facebook/seamless-m4t-v2-large`, revisión
`5f8cc790b19fc3f67a61c105133b20b34e3dcb76`, en este servidor. FRONTEND no
aloja el modelo: conserva únicamente el gateway de respaldo.

## Contratos y configuración

Android, panel y Display conservan `POST /v1/tts` autenticado por usuario o
dispositivo: `{text, language}` (`en`/`es`) devuelve WAV PCM mono. El texto se
muestra antes de solicitar audio. La síntesis no crea capturas, evidencia,
mensajes, cachés compartidas ni audio persistido. Detener, cambiar idioma o
sesión invalida la reproducción anterior.

La conexión se selecciona con `META_CONNECTION_MODE=direct|gateway` y
`META_GATEWAY_FALLBACK_ENABLED=true|false` en `.env`, igual que las consultas
Meta. En directo, el backend utiliza:

```dotenv
TTS_SERVICE_URL=https://realityos.luxisoft.com/tts/synthesize
TTS_SERVICE_TOKEN=<separate server-only token, at least 24 characters>
TTS_TIMEOUT_SECONDS=30
TTS_LOCAL_ENABLED=true
```

`/tts/synthesize` es un endpoint HTTPS público autenticado con Bearer token,
limitado por IP a 30 peticiones/minuto y 32 KiB de entrada. Nginx conecta
directamente al contenedor local, ligado exclusivamente a `127.0.0.1:8091`.
Los clientes siguen usando `/v1/tts`; nunca reciben ese token.

El gateway de FRONTEND conserva `/v1/tts/synthesize` y su token independiente.
Su `TTS_SERVICE_URL` apunta al endpoint público de RealityOS y utiliza el token
de voz. No hay bucle: `/tts/synthesize` termina directamente en Seamless.
Esta ruta alternativa comparte el motor local; no ofrece una segunda réplica
si el modelo cae. Si ambas rutas fallan, continúa la voz de Android/navegador.

## Runtime y activación

Combinar el Compose de RealityOS con `infrastructure/tts/compose.realityos.yml`
y activar el perfil `speech`. El contenedor tiene 4 GiB de RAM, sin swap, dos
CPU, una sola inferencia simultánea, raíz de solo lectura y volumen persistente
para pesos. Las dependencias pesadas no entran en API/worker. El modelo usa
BF16; generación EN/ES sin muestreo y `speaker_id=0`.

La salud ready exige el modelo cargado. Una segunda inferencia recibe 429 y
el lock se mantiene mientras el cálculo siga en curso. El presupuesto HTTP
total es 30 segundos, con como máximo dos intentos entre directo y respaldo.
La generación comprueba su límite de 13 segundos entre frases y al terminar;
no interrumpe kernels de PyTorch a mitad del cálculo.

Antes de activar, descargar pesos en el volumen y ejecutar
`scripts/benchmark_tts.py`: seis WAV válidos EN/ES, cada uno por debajo de
15 segundos, sin OOM ni degradación del API. Si falla, detener el contenedor,
poner `TTS_LOCAL_ENABLED=false` y conservar la voz del dispositivo. No ampliar
recursos ni cambiar de modelo automáticamente.

El preflight real del 2026-11-01 en RealityOS cargó el modelo y produjo seis
muestras válidas entre 2,22 y 3,01 segundos, sin OOM. El informe privado queda
en `.runtime/direct-tts-20261101-benchmark.json`.

El modelo mantiene su licencia [CC-BY-NC-4.0](https://huggingface.co/facebook/seamless-m4t-v2-large),
separada de la licencia del proyecto. Referencia de implementación:
[Transformers SeamlessM4T v2](https://huggingface.co/docs/transformers/model_doc/seamless_m4t_v2).
