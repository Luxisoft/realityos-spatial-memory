# Producción del video demo de RealityOS

La edición en inglés dura **180 segundos para la hackathon** y **135 segundos para X**, a 1920×1080 y 30 fps. `RealityOS.tsx` contiene la composición propia; OpenMontage ejecuta el flujo `screen-demo` y la herramienta `video_compose` con Remotion en modo `atelier`. El renderizado y la exportación son locales. Estos scripts no despliegan la aplicación ni publican en X o en la plataforma del evento.

Las entregas canónicas, almacenadas mediante Git LFS, son `realityos-demo.mp4` (tres minutos) y `realityos-x.mp4` en la [carpeta de entrega](../../../demo-video/). Por petición expresa, **el usuario realizará la revisión visual final**. Las verificaciones actuales cubren metadatos técnicos y mediciones de audio; no certifican apariencia, colocación de subtítulos ni calidad narrativa.

Esta producción utiliza OpenMontage en el commit `d21f5d4eaa08422b09c7091757a05affcbabb35b`, Remotion/CLI `4.0.484`, Node `22.22.2`, Python `3.13`, FFmpeg/ffprobe y `/usr/bin/chromium`. La preparación de medios requiere ImageMagick (`convert` o `magick`); `prepare.py` espera las fuentes FreeSans de Linux en `/usr/share/fonts/truetype/freefont/`. Las dependencias exactas de Python y los hashes de origen quedan en `.runtime/video-production/project/pipeline/run-provenance.json`.

## Fuentes y procedencia

Los videos originales permanecen en `demo-video/`. Los cuatro archivos `intro_auth_*` / `search_with_*` son recorridos de Android grabados por el propietario. `policial_case.mp4`, `profile_found.mp4`, `nurse_case.mp4` y `memory.mp4` son ilustraciones creadas por el propietario con Higgsfield. El material conceptual se identifica como tal; el video de Meta Display muestra la vista previa simulada de la aplicación. El grupo social local no demuestra autenticación real con Facebook. La narración conserva la incertidumbre expresada en la respuesta de Police.

`demo-video/production/` incluye los MP3 de narración en inglés, el manifiesto de escenas, los subtítulos SRT y el texto de publicación para reproducir la edición sin otra solicitud a ElevenLabs. Después de clonar, ejecute `git lfs pull` para obtener los medios. Los scripts preparan estos recursos ignorados por Git:

- `media/*.mp4`: copias normalizadas a 30 fps sin el audio original; `media/*.jpg`: recortes de detalle sin alterar su contenido.
- `source-review.json`: hashes originales, duraciones, observaciones de edición y procedencia de recortes.
- `audio/*.mp3`: la narración en inglés suministrada; el manifiesto conserva los tiempos de subtítulos.
- `narration.json`: texto, duración, subtítulos y metadatos de voz que consume `prepare.py`.

La narración usa la voz del propietario en ElevenLabs **“Clon - Jose Marin Voz”**, ID `16swapJezO8OF8CQPKLM`, con `eleven_multilingual_v2`. El ajuste de tempo de FFmpeg conserva el tono y ralentiza ciertas secciones para la duración prevista. La alineación de subtítulos procede de ElevenLabs; no equivale a verificar una transcripción independiente. No se incluyen credenciales ni respuestas completas del proveedor. La reproducción reutiliza los MP3 suministrados; una narración distinta requiere la cuenta de voz autorizada del propietario.

## Preparación y renderizado

Ejecute desde la raíz del repositorio. En un espacio de producción nuevo, instale la herramienta de forma aislada:

```bash
mkdir -p .runtime/video-production
git clone https://github.com/calesthio/OpenMontage.git .runtime/video-production/openmontage
git -C .runtime/video-production/openmontage checkout d21f5d4eaa08422b09c7091757a05affcbabb35b
python3 -m venv .runtime/video-production/openmontage/.venv
.runtime/video-production/openmontage/.venv/bin/pip install pyyaml pydantic jsonschema python-dotenv pillow numpy requests websockets
npm --prefix .runtime/video-production/openmontage/remotion-composer ci --no-audit --no-fund
```

Dentro de esa copia, cree `remotion-composer/remotion.config.ts` con la configuración utilizada:

```ts
import {Config} from '@remotion/cli/config';
Config.setBrowserExecutable('/usr/bin/chromium');
Config.setConcurrency(2);
Config.setCodec('h264');
Config.setPixelFormat('yuv420p');
```

Primero prepare los medios normalizados y después los recursos de edición. `prepare.py` copia el manifiesto y el audio suministrados cuando no existen en runtime:

```bash
python3 scripts/demo-video/prepare_media.py
python3 scripts/demo-video/prepare.py
.runtime/video-production/openmontage/.venv/bin/python scripts/demo-video/record_pipeline.py
.runtime/video-production/openmontage/.venv/bin/python - <<'PY'
import json, sys
from dataclasses import asdict
from pathlib import Path
work = Path('.runtime/video-production').resolve()
sys.path.insert(0, str(work / 'openmontage'))
from tools.video.video_compose import VideoCompose
for variant in ('main', 'x'):
    inputs = json.loads((work / 'project' / f'{variant}-inputs.json').read_text())
    result = VideoCompose().execute(inputs)
    (work / 'exports' / f'{variant}-result.json').write_text(json.dumps(asdict(result), indent=2))
    if not result.success:
        raise SystemExit(result.error)
PY
```

Los resultados iniciales son `.runtime/video-production/exports/realityos-main.mp4` y `realityos-x.mp4`. Se renderizan secuencialmente con concurrencia 2. OpenMontage copia las fuentes de la composición a su compositor, obtiene los medios mediante `public/` y produce una revisión automática de metadatos, cuadros y audio.

`create_music_bed.py` crea una pieza musical original de 180 segundos, estéreo a 48 kHz, en `audio/music-bed.wav`, con semilla fija y sin muestras externas. La composición incorpora la narración; `finalize_audio.py` mezcla la música, mide la normalización de sonoridad en dos pasadas, genera AAC estéreo a 48 kHz y conserva el video. No regenere recursos mientras un render los esté usando.

```bash
.runtime/video-production/openmontage/.venv/bin/python scripts/demo-video/create_music_bed.py
python3 scripts/demo-video/finalize_audio.py \
  --input .runtime/video-production/exports/realityos-main.mp4 \
  --music .runtime/video-production/audio/music-bed.wav --duration 180 \
  --output demo-video/realityos-demo.mp4 \
  --report .runtime/video-production/exports/main-audio-report.json
```

Repita el comando de acabado con entrada `.runtime/video-production/exports/realityos-x.mp4`, duración `135`, salida `demo-video/realityos-x.mp4` y un informe de audio independiente. Los objetivos son −16 LUFS y −1.5 dBTP; las mediciones reales quedan en el informe.

## Revisión y trazabilidad

```bash
.runtime/video-production/openmontage/.venv/bin/python scripts/demo-video/record_pipeline.py \
  --render-result main=.runtime/video-production/exports/main-result.json \
  --render-result x=.runtime/video-production/exports/x-result.json \
  --final-output main=demo-video/realityos-demo.mp4 \
  --final-output x=demo-video/realityos-x.mp4
ffprobe -v error -show_format -show_streams demo-video/realityos-demo.mp4
```

El registro valida los esquemas y checkpoints reales de OpenMontage. `--final-output` registra el archivo final masterizado y consulta sus metadatos, conservando la revisión del render original como procedencia. La revisión visual queda pendiente del usuario; no se genera una aprobación ficticia. Después de que el usuario revise realmente una entrega, `--review-evidence FILE` puede registrar por variante `status: "pass"`, `reviewer: "user"`, `visual_review_completed: true`, las notas y el `sha256` coincidente. Hasta entonces, los checkpoints de composición y exportación mantienen la revisión pendiente aunque exista el archivo descargable. Nunca se declara una publicación externa. Un master modificado requiere un nuevo hash y una nueva revisión.
