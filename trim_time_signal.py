"""Trim confirmed six-tone closing signals; retain originals locally."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / '.tools'))
import numpy as np


def detect_cut(ffmpeg: str, path: Path) -> float | None:
    probe = subprocess.run([ffmpeg, '-hide_banner', '-i', str(path)], capture_output=True)
    match = re.search(rb'Duration: (\d+):(\d+):(\d+\.\d+)', probe.stderr)
    if not match:
        raise ValueError(f'Cannot determine duration: {path}')
    hours, minutes, seconds = map(float, match.groups())
    duration = hours*3600 + minutes*60 + seconds
    tail = min(duration, 420)
    raw = subprocess.run([ffmpeg, '-v', 'error', '-sseof', str(-tail), '-i', str(path),
                          '-ar', '8000', '-ac', '1', '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    samples = np.frombuffer(raw, dtype='<i2').astype(float)
    frames = samples[:len(samples)//160*160].reshape(-1, 160)
    spectrum = abs(np.fft.rfft(frames))**2
    purity = spectrum[:, 21] / np.maximum(spectrum.sum(axis=1), 1)
    indices = np.where((purity > .5) & (np.mean(frames**2, axis=1) > 100**2))[0]
    groups = np.split(indices, np.where(np.diff(indices) > 2)[0]+1)
    pulses = [(g[0]*.02, (g[-1]+1)*.02) for g in groups if len(g) >= 3]
    candidates = []
    for i in range(len(pulses)-5):
        six = pulses[i:i+6]
        if all(.12 <= end-start <= .30 for start, end in six) and all(
            abs(six[j+1][0]-six[j][0]-1) <= .06 for j in range(5)
        ):
            candidates.append(duration-tail+six[0][0]-.06)
    return float(candidates[0]) if len(candidates) == 1 and candidates[0] > 600 else None


def trim_audio(ffmpeg: str, path: Path, backup_name: str | None = None) -> float | None:
    cut = detect_cut(ffmpeg, path)
    if cut is None:
        return None
    backup = Path('.tools/audio-originals') / (backup_name or path.name)
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(path, backup)
    temporary = path.with_name(path.stem + '.trim.part.m4a')
    try:
        subprocess.run([ffmpeg, '-v', 'error', '-i', str(path), '-t', f'{cut:.3f}',
                        '-map', '0:a:0', '-c:a', 'copy', '-movflags', '+faststart',
                        '-y', str(temporary)], check=True)
        if temporary.stat().st_size == 0:
            raise ValueError('Empty trimmed audio')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return cut


if __name__ == '__main__':
    from download_rthk_2026 import find_ffmpeg, METADATA_PATH
    ffmpeg = find_ffmpeg()
    episodes = json.loads(METADATA_PATH.read_text(encoding='utf-8'))
    apply = '--apply' in sys.argv
    for episode in episodes:
        path = Path(episode['audio_path'])
        cut = trim_audio(ffmpeg, path) if apply else detect_cut(ffmpeg, path)
        print(episode['date'], 'cut', cut, flush=True)
        episode['length'] = path.stat().st_size
    if apply:
        METADATA_PATH.write_text(json.dumps(episodes, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
