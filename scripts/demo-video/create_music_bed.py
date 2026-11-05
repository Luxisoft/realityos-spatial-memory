"""Original procedural score for RealityOS, no samples or external melodies.
A quiet suspended-pad progression with sparse original chime accents.
Reproduce: .runtime/video-production/openmontage/.venv/bin/python scripts/demo-video/create_music_bed.py
"""

import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2] / ".runtime/video-production/audio"
ROOT.mkdir(parents=True, exist_ok=True)
SR = 48000
DURATION = 180
N = SR * DURATION
left = np.zeros(N, dtype=np.float32)
right = np.zeros(N, dtype=np.float32)
rng = np.random.default_rng(20261104)
# Original arrangement: open voicings, slowly crossfaded, no borrowed tune.
chords = [[50, 57, 60, 64], [46, 53, 57, 60], [53, 60, 65, 67], [48, 55, 60, 62]]


def hz(midi):
    return 440 * 2 ** ((midi - 69) / 12)


for index in range(8):
    start = max(0, index * 22.5 - 2.5)
    stop = min(DURATION, (index + 1) * 22.5 + 2.5)
    a, b = int(start * SR), int(stop * SR)
    t = np.arange(b - a, dtype=np.float32) / SR
    envelope = np.minimum(1, t / 3) * np.minimum(1, (stop - start - t) / 4)
    envelope = np.clip(envelope, 0, 1) ** 2
    for ni, note in enumerate(chords[index % 4]):
        f = hz(note)
        phase = float(rng.uniform(0, 6.28))
        pan = 0.22 + 0.18 * ni
        wavelet = (
            np.sin(2 * np.pi * f * t + phase)
            + 0.12 * np.sin(2 * np.pi * 2 * f * t + phase / 2)
            + 0.025 * np.sin(2 * np.pi * 3 * f * t)
        ) * envelope
        trem = 0.97 + 0.03 * np.sin(2 * np.pi * 0.08 * t + ni)
        left[a:b] += 0.055 * np.cos(pan * np.pi / 2) * wavelet * trem
        right[a:b] += 0.055 * np.sin(pan * np.pi / 2) * wavelet * trem
# Sparse gentle pulses: every six seconds, never a dramatic heartbeat.
for second in np.arange(4, 176, 6):
    a = int(second * SR)
    count = int(1.4 * SR)
    t = np.arange(count, dtype=np.float32) / SR
    pulse = (
        0.018 * np.sin(2 * np.pi * hz(38) * t) * np.exp(-4 * t) * (1 - np.exp(-20 * t))
    )
    left[a : a + count] += pulse
    right[a : a + count] += pulse
# Original four-note chime motif at section boundaries.
for i, second in enumerate([10, 36, 68, 99, 132, 161]):
    note = [76, 72, 79, 74, 76, 72][i]
    a = int(second * SR)
    count = min(int(3 * SR), N - a)
    t = np.arange(count, dtype=np.float32) / SR
    chime = (
        0.012
        * (
            np.sin(2 * np.pi * hz(note) * t)
            + 0.14 * np.sin(2 * np.pi * hz(note) * 2 * t)
        )
        * np.exp(-1.6 * t)
        * (1 - np.exp(-100 * t))
    )
    left[a : a + count] += chime * 0.8
    right[a : a + count] += chime
fade_in = np.linspace(0, 1, 2 * SR, dtype=np.float32) ** 2
fade_out = np.linspace(1, 0, 4 * SR, dtype=np.float32) ** 2
left[: len(fade_in)] *= fade_in
right[: len(fade_in)] *= fade_in
left[-len(fade_out) :] *= fade_out
right[-len(fade_out) :] *= fade_out
stereo = np.column_stack([left, right])
peak = np.max(np.abs(stereo))
stereo *= 0.08 / max(peak, 1e-6)
raw = ROOT / "music-bed-source.wav"
with wave.open(str(raw), "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes((np.clip(stereo, -1, 1) * 32767).astype("<i2").tobytes())
subprocess.run(
    [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        str(raw),
        "-af",
        "loudnorm=I=-34:TP=-9:LRA=7",
        "-ar",
        "48000",
        "-c:a",
        "pcm_s16le",
        str(ROOT / "music-bed.wav"),
    ],
    check=True,
)
print("Original procedural music-bed.wav created, 180 seconds, stereo 48kHz.")
