"""Remove confirmed programme prefixes and closing signals; retain originals."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / '.tools'))
import numpy as np


INTRO_REFERENCE = Path('audio-reference/people-in-history-intro.m4a')
PREFIX_SEARCH_SECONDS = 600
PREFIX_SAMPLE_RATE = 2000
MIN_PREFIX_CORRELATION = 0.70


def decode_audio(
    ffmpeg: str, path: Path, duration: float, sample_rate: int = PREFIX_SAMPLE_RATE
) -> np.ndarray:
    raw = subprocess.run(
        [
            ffmpeg,
            '-v',
            'error',
            '-i',
            str(path),
            '-t',
            str(duration),
            '-ar',
            str(sample_rate),
            '-ac',
            '1',
            '-f',
            'f32le',
            '-',
        ],
        capture_output=True,
        check=True,
    ).stdout
    return np.frombuffer(raw, dtype='<f4').astype(float)


def find_reference_offset(search: np.ndarray, reference: np.ndarray) -> tuple[int, float]:
    if len(reference) == 0 or len(search) < len(reference):
        raise ValueError('Audio is shorter than the programme intro reference')

    centered_reference = reference - reference.mean()
    reference_energy = np.linalg.norm(centered_reference)
    if reference_energy == 0:
        raise ValueError('Programme intro reference is silent')

    fft_size = 1 << (len(search) + len(reference) - 1).bit_length()
    correlation = np.fft.irfft(
        np.fft.rfft(search, fft_size)
        * np.conj(np.fft.rfft(centered_reference, fft_size)),
        fft_size,
    )[: len(search) - len(reference) + 1]

    cumulative = np.r_[0.0, np.cumsum(search)]
    cumulative_squared = np.r_[0.0, np.cumsum(search * search)]
    window = len(reference)
    means = (cumulative[window:] - cumulative[:-window]) / window
    energies = (
        cumulative_squared[window:]
        - cumulative_squared[:-window]
        - window * means * means
    )
    scores = correlation / (
        np.sqrt(np.maximum(energies, 1e-12)) * reference_energy
    )
    index = int(np.argmax(scores))
    return index, float(scores[index])


def detect_prefix_cut(
    ffmpeg: str, path: Path, reference_path: Path = INTRO_REFERENCE
) -> float | None:
    if not reference_path.exists():
        raise FileNotFoundError(f'Missing programme intro reference: {reference_path}')
    reference = decode_audio(ffmpeg, reference_path, duration=30)
    search = decode_audio(ffmpeg, path, duration=PREFIX_SEARCH_SECONDS)
    offset, score = find_reference_offset(search, reference)
    if score < MIN_PREFIX_CORRELATION:
        return None
    offset_seconds = offset / PREFIX_SAMPLE_RATE
    # Sub-second offsets are encoder padding around an intro that already starts
    # at the beginning; preserve the first packet instead of clipping it.
    return 0.0 if offset_seconds < 1.0 else offset_seconds


def detect_tail_cut(ffmpeg: str, path: Path) -> float | None:
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


def detect_cut(ffmpeg: str, path: Path) -> float | None:
    """Backward-compatible alias for closing-signal detection."""
    return detect_tail_cut(ffmpeg, path)


def trim_audio(
    ffmpeg: str, path: Path, backup_name: str | None = None
) -> tuple[float, float]:
    backup = Path('.tools/audio-originals') / (backup_name or path.name)
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(path, backup)

    prefix_cut = detect_prefix_cut(ffmpeg, path)
    tail_cut = detect_tail_cut(ffmpeg, path)
    if prefix_cut is None:
        raise ValueError(f'Programme intro was not detected: {path}')
    if tail_cut is None:
        raise ValueError(f'Closing time signal was not detected: {path}')
    if tail_cut - prefix_cut < 600:
        raise ValueError(f'Edited programme would be unexpectedly short: {path}')

    temporary = path.with_name(path.stem + '.trim.part.m4a')
    try:
        subprocess.run(
            [
                ffmpeg,
                '-v',
                'error',
                '-ss',
                f'{prefix_cut:.3f}',
                '-i',
                str(path),
                '-t',
                f'{tail_cut - prefix_cut:.3f}',
                '-map',
                '0:a:0',
                '-c:a',
                'copy',
                '-movflags',
                '+faststart',
                '-y',
                str(temporary),
            ],
            check=True,
        )
        if temporary.stat().st_size == 0:
            raise ValueError('Empty edited audio')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return prefix_cut, tail_cut


if __name__ == '__main__':
    from download_rthk_2026 import find_ffmpeg, METADATA_PATH
    ffmpeg = find_ffmpeg()
    episodes = json.loads(METADATA_PATH.read_text(encoding='utf-8'))
    apply = '--apply' in sys.argv
    for episode in episodes:
        path = Path(episode['audio_path'])
        cuts = (
            trim_audio(ffmpeg, path)
            if apply
            else (detect_prefix_cut(ffmpeg, path), detect_tail_cut(ffmpeg, path))
        )
        print(episode['date'], 'cuts', cuts, flush=True)
        episode['length'] = path.stat().st_size
    if apply:
        METADATA_PATH.write_text(json.dumps(episodes, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
