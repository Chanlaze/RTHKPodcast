#!/usr/bin/env python3
"""Download available 2026 RTHK People episodes as podcast-ready M4A files."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path


YEAR = 2026
PROGRAMME_URL = "https://www.rthk.hk/radio/radio1/programme/People"
ARCHIVE_API = "https://www.rthk.hk/radio/catchUpByMonth"
MEDIA_ROOT = "https://rthkaod2022.akamaized.net/m4a/radio/archive/radio1/People/m4a"
OUTPUT_DIR = Path("audio") / str(YEAR)
METADATA_PATH = Path(f"rthk-{YEAR}-episodes.json")


def get_json(url: str) -> dict[str, object]:
    request = urllib.request.Request(url, headers={"User-Agent": "RTHKPodcast/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def get_bytes(url: str, attempts: int = 3) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "RTHKPodcast/1.0"})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(attempt)
    raise AssertionError("unreachable")


def resolve_segments(master_url: str) -> list[str]:
    master = get_bytes(master_url).decode("utf-8-sig")
    variant_name = next(
        line.strip() for line in master.splitlines() if line.strip() and not line.startswith("#")
    )
    variant_url = urllib.parse.urljoin(master_url, variant_name)
    playlist = get_bytes(variant_url).decode("utf-8-sig")
    return [
        urllib.parse.urljoin(variant_url, line.strip())
        for line in playlist.splitlines()
        if line.strip() and not line.startswith("#")
    ]


def fetch_episodes() -> list[dict[str, object]]:
    last_month = min(date.today().month, 12) if date.today().year == YEAR else 12
    episodes: list[dict[str, object]] = []
    for month in range(1, last_month + 1):
        query = urllib.parse.urlencode(
            {"c": "radio1", "p": "People", "m": f"{YEAR}{month:02d}"}
        )
        payload = get_json(f"{ARCHIVE_API}?{query}")
        if payload.get("status") == "1":
            episodes.extend(payload.get("content", []))

    normalized: list[dict[str, object]] = []
    for episode in episodes:
        episode_date = datetime.strptime(str(episode["date"]), "%d/%m/%Y").date()
        date_key = episode_date.strftime("%Y%m%d")
        normalized.append(
            {
                "id": str(episode["id"]),
                "date": episode_date.isoformat(),
                "title": str(episode["title"]).strip(),
                "source_page": f"{PROGRAMME_URL}/episode/{episode['id']}",
                "stream_url": f"{MEDIA_ROOT}/{date_key}.m4a/master.m3u8",
                "audio_path": (OUTPUT_DIR / f"{date_key}.m4a").as_posix(),
            }
        )
    return sorted(normalized, key=lambda item: str(item["date"]))


def find_ffmpeg() -> str:
    executable = shutil.which("ffmpeg")
    if executable:
        return executable

    binaries = sorted(Path(".tools").glob("imageio_ffmpeg/binaries/ffmpeg-*.exe"))
    if binaries:
        return str(binaries[-1].resolve())

    raise SystemExit(
        "ffmpeg was not found. Install the local helper with: "
        "python -m pip install imageio-ffmpeg --target .tools"
    )


def download_episode(ffmpeg: str, episode: dict[str, object], force: bool) -> None:
    output = Path(str(episode["audio_path"]))
    if output.exists() and output.stat().st_size > 0 and not force:
        print(f"Skip {output.name} ({episode['title']})")
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".part.m4a")
    transport_stream = output.with_suffix(".part.ts")
    temporary.unlink(missing_ok=True)
    transport_stream.unlink(missing_ok=True)
    print(f"Download {output.name} ({episode['title']})", flush=True)
    segment_urls = resolve_segments(str(episode["stream_url"]))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        segments = executor.map(get_bytes, segment_urls)
        with transport_stream.open("wb") as combined:
            for segment in segments:
                combined.write(segment)

    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(transport_stream),
        "-vn",
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        "-y",
        str(temporary),
    ]
    try:
        subprocess.run(command, check=True)
        temporary.replace(output)
    finally:
        transport_stream.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="redownload existing files")
    parser.add_argument(
        "--metadata-only", action="store_true", help="refresh episode metadata only"
    )
    args = parser.parse_args()

    episodes = fetch_episodes()
    print(f"Found {len(episodes)} available {YEAR} episodes")
    if not args.metadata_only:
        ffmpeg = find_ffmpeg()
        for episode in episodes:
            download_episode(ffmpeg, episode, args.force)

    for episode in episodes:
        audio_path = Path(str(episode["audio_path"]))
        episode["length"] = audio_path.stat().st_size if audio_path.exists() else 0

    METADATA_PATH.write_text(
        json.dumps(episodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {METADATA_PATH}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("Download cancelled")
