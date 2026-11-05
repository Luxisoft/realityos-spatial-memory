# RealityOS demo production

The English edit targets **180 seconds for the hackathon** and **135 seconds for X**, at 1920×1080 and 30 fps. `RealityOS.tsx` is the bespoke composition; OpenMontage runs its `screen-demo` pipeline and `video_compose` tool in Remotion `atelier` mode. Rendering and exports are local. These scripts do not deploy the application or upload to X/the submission platform.

Canonical deliveries, stored through Git LFS: `realityos-demo.mp4` (three minutes) and `realityos-x.mp4` in the [delivery directory](../../../demo-video/). At the user's request, **the user will perform the final visual review**. Current delivery checks cover technical metadata and audio measurements; they do not certify appearance, caption placement or narrative quality.

The production run uses OpenMontage commit `d21f5d4eaa08422b09c7091757a05affcbabb35b`, Remotion/CLI `4.0.484`, Node `22.22.2`, Python `3.13`, FFmpeg/ffprobe and `/usr/bin/chromium`. Media preparation requires ImageMagick (`convert` or `magick`); `prepare.py` expects Linux FreeSans fonts under `/usr/share/fonts/truetype/freefont/`. Exact Python dependencies and source hashes are recorded in `.runtime/video-production/project/pipeline/run-provenance.json`.

## Inputs and provenance

Original videos remain in `demo-video/`. The four `intro_auth_*` / `search_with_*` files are owner-recorded Android walkthroughs. `policial_case.mp4`, `profile_found.mp4`, `nurse_case.mp4` and `memory.mp4` are owner-created Higgsfield illustrations. Concept footage is labelled; the Meta Display footage demonstrates the app's simulated preview. The local social workspace does not demonstrate live Facebook authentication. The Police response's uncertainty is preserved in the narration.

`demo-video/production/` supplies the English narration MP3 files, scene manifest, SRT subtitles and publication copy for reproduction without another ElevenLabs request. Run `git lfs pull` after cloning to retrieve repository media. Production scripts prepare these ignored runtime inputs:

- `media/*.mp4`: normalized 30 fps copies, with source audio removed; `media/*.jpg`: unaltered detail crops.
- `source-review.json`: source hashes, durations, editorial observations and crop provenance.
- `audio/*.mp3`: the supplied generated English narration; caption timing is in the manifest.
- `narration.json`: the scene text, durations, captions and voice metadata consumed by `prepare.py`.

Narration uses the owner's ElevenLabs voice **“Clon - Jose Marin Voz”**, ID `16swapJezO8OF8CQPKLM`, with `eleven_multilingual_v2`. Pitch-preserving FFmpeg tempo adjustment slows selected sections to fit the planned delivery. Caption alignment comes from ElevenLabs; it is not an independent transcription check. Credentials and raw provider responses are excluded. Reproduction reuses the supplied MP3 files; generating different narration requires the owner's authorized voice account.

## Prepare and render

Run from the repository root. On a fresh production workspace, install the isolated tool checkout:

```bash
mkdir -p .runtime/video-production
git clone https://github.com/calesthio/OpenMontage.git .runtime/video-production/openmontage
git -C .runtime/video-production/openmontage checkout d21f5d4eaa08422b09c7091757a05affcbabb35b
python3 -m venv .runtime/video-production/openmontage/.venv
.runtime/video-production/openmontage/.venv/bin/pip install pyyaml pydantic jsonschema python-dotenv pillow numpy requests websockets
npm --prefix .runtime/video-production/openmontage/remotion-composer ci --no-audit --no-fund
```

Create `remotion-composer/remotion.config.ts` inside that checkout with the configuration used for this run:

```ts
import {Config} from '@remotion/cli/config';
Config.setBrowserExecutable('/usr/bin/chromium');
Config.setConcurrency(2);
Config.setCodec('h264');
Config.setPixelFormat('yuv420p');
```

Prepare normalized source media first, then build the editorial inputs. `prepare.py` copies the supplied narration manifest and audio into runtime when absent:

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

Outputs are `.runtime/video-production/exports/realityos-main.mp4` and `realityos-x.mp4`. Renders run sequentially with concurrency 2. OpenMontage stages composition source files into its composer directory, resolves media through the project `public/` directory, and produces an automatic technical/frame/audio review.

`create_music_bed.py` creates the original 180-second, 48 kHz stereo procedural score in `audio/music-bed.wav`, using a fixed seed and no external samples. The composition embeds narration; `finalize_audio.py` mixes the score, measures two-pass loudness normalization, writes stereo AAC at 48 kHz and preserves the video stream. Do not regenerate assets while a render is using them.

```bash
.runtime/video-production/openmontage/.venv/bin/python scripts/demo-video/create_music_bed.py
python3 scripts/demo-video/finalize_audio.py \
  --input .runtime/video-production/exports/realityos-main.mp4 \
  --music .runtime/video-production/audio/music-bed.wav --duration 180 \
  --output demo-video/realityos-demo.mp4 \
  --report .runtime/video-production/exports/main-audio-report.json
```

Repeat the finishing command with input `.runtime/video-production/exports/realityos-x.mp4`, duration `135`, output `demo-video/realityos-x.mp4`, and a separate X audio report. Final targets are −16 LUFS and −1.5 dBTP; actual measurements are in the finishing report.

## Review and audit

```bash
.runtime/video-production/openmontage/.venv/bin/python scripts/demo-video/record_pipeline.py \
  --render-result main=.runtime/video-production/exports/main-result.json \
  --render-result x=.runtime/video-production/exports/x-result.json \
  --final-output main=demo-video/realityos-demo.mp4 \
  --final-output x=demo-video/realityos-x.mp4
ffprobe -v error -show_format -show_streams demo-video/realityos-demo.mp4
```

The pipeline writer validates real OpenMontage artifact schemas and checkpoints. `--final-output` records the separately mastered deliverable and probes that file, retaining the source render review as provenance. Final visual review stays pending for the user; no fabricated approval is generated. After the user actually reviews a delivery, `--review-evidence FILE` may record its per-variant `status: "pass"`, `reviewer: "user"`, `visual_review_completed: true`, notes and matching final `sha256`. Until then, compose/export checkpoints retain pending review status even when the downloadable file exists. It never claims an external upload. A changed master needs a new hash and review.
