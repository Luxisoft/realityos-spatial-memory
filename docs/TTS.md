# Respuestas de voz con SeamlessM4T v2

Las respuestas escritas se muestran antes de solicitar el audio. Android/gafas,
panel web y Display web llaman a `POST /v1/tts` con `{text, language}` (`en` o
`es`). La respuesta es WAV PCM mono; no crea capturas, mensajes ni evidencias,
no busca datos de otros usuarios y no persiste el texto/audio sintetizado.
La autenticación admite una cuenta activa o un dispositivo vigente con una
asignación activa. No hay caché compartida entre cuentas ni URLs públicas.

El backend llama a la ruta fija `/v1/tts/synthesize` del gateway, autenticada
con su token existente. El gateway usa un token independiente para llamar al
servicio privado `seamless-tts:8091/synthesize`. Nunca envía allí la clave Meta
ni el token del gateway. El cuerpo no admite modelos, destinos o URLs arbitrarios.

Un fallo transitorio permite un único reintento desde el backend, con 500 ms de
espera y 30 segundos de presupuesto total. Las interfaces no repiten la petición:
si finalmente falta audio, reproducen la voz actual de Android/navegador y lo
indican. Un 401/403 de RealityOS no se reintenta ni reproduce texto privado con
otra sesión. Detener, cambiar de idioma, salir o iniciar otra respuesta invalida
la descarga/reproducción anterior.

## Servicio privado en FRONTEND

El modelo oficial es `facebook/seamless-m4t-v2-large`, revisión
`5f8cc790b19fc3f67a61c105133b20b34e3dcb76`. La clase dedicada
`SeamlessM4Tv2ForTextToSpeech` evita cargar componentes de entrada de audio.
Los idiomas de entrada y salida coinciden (`spa`/`eng`), con `speaker_id=0` y
generación sin muestreo. Las frases largas se dividen sin perder palabras.
Solo se ejecuta una inferencia simultánea; una segunda recibe 429. Una petición
HTTP vencida no libera el lock mientras el cálculo continúe en el servicio.
El deadline de generación se comprueba entre frases y tras generar; no es una
interrupción dura de kernels de PyTorch. Docker acota CPU y memoria.

Pesos bajo [CC-BY-NC-4.0](https://huggingface.co/facebook/seamless-m4t-v2-large),
separados de la licencia del código del proyecto. Firmas verificadas con la
[documentación oficial de Transformers](https://huggingface.co/docs/transformers/model_doc/seamless_m4t_v2).

1. Inspeccionar RAM libre, CPU y disco en FRONTEND. Requerir al menos 10 GiB de
   RAM disponible antes de probar el contenedor limitado a 8 GiB, dejando al
   menos 2 GiB para los servicios existentes. Si no alcanza, conservar la voz
   actual; no instalar el modelo en el host de RealityOS ni contratar recursos.
2. Construir con contexto del repositorio e imagen inmutable:
   `docker build -f infrastructure/tts/Dockerfile -t realityos-tts:seamless-v2-20261101 .`.
   No instalar PyTorch/Transformers en API o worker.
3. Crear `tts.env` privado (0600) con un nuevo `TTS_SERVICE_TOKEN` de al menos
   24 caracteres. Se comparte únicamente entre gateway y Seamless; conservar
   el archivo runtime actual del gateway. Fijar `REALITYOS_TTS_IMAGE` al tag construido.
4. Combinar el Compose del gateway con `infrastructure/tts/compose.yml` e iniciar
   solo `seamless-tts` antes de actualizar el gateway. El volumen `seamless_models`
   descarga los pesos una vez; no hay puerto público. Esperar salud ready.
5. Ejecutar `scripts/benchmark_tts.py` desde un entorno que alcance el servicio
   privado, con `PYTHONPATH=backend`, `httpx` no requerido y el token en entorno.
   Exigir seis muestras válidas EN/ES, todas por debajo de 15 segundos. Medir
   también el pico de memoria del contenedor y verificar el margen de 2 GiB
   del host bajo carga. Conservar resultados privados en `.runtime/`.
6. Solo si pasan los controles, actualizar el gateway con rollback a la imagen
   anterior y activar su overlay TTS. Verificar la ruta con token y rechazar
   tokens/rutas inválidos. Mantener sin cambios el forwarding multipart de Meta.
7. Desplegar API/worker con overlay de imagen y rollback, verificar salud,
   OpenAPI y Alembic. No hay migración nueva ni se requiere dump PostgreSQL.
   Publicar las webs mediante CI y reemplazar únicamente el APK Debug habitual.

## Estado de esta implementación

La integración incluye pruebas con audio/servicio sustituidos. El acceso remoto
a FRONTEND fue rechazado por la herramienta con «This operation requires
approval in an active chat»; recursos, carga del modelo, muestras reales y
activación del servicio/gateway siguen pendientes. No declarar Seamless activo
hasta completar los pasos anteriores. Un gateway anterior responde 404 para
TTS y las nuevas interfaces conservan el respaldo de voz actual.
