"""Publish only catalogued podcast copies; original backups never leave this PC."""

import argparse
import json
import shutil
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

from generate_people_in_history_feed import AUDIO_ROOT

ROOT = Path(__file__).resolve().parent
REPO = ROOT / ".tools" / "gitlab-audio"
REMOTE = "https://gitlab.com/chanlaze-group/Chanlaze-project.git"


def git(*args):
    return subprocess.check_output(
        ["git", "-C", str(REPO), *args], text=True, encoding="utf-8"
    ).strip()


def verify(episodes):
    for episode in episodes:
        path = str(episode["audio_path"])
        local = ROOT / path
        url = AUDIO_ROOT + "/" + urllib.parse.quote(path, safe="/")
        request = urllib.request.Request(url, headers={"Range": "bytes=0-31"})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read(32)
            if response.status != 206:
                raise RuntimeError(f"Range download unsupported: {path}")
            if response.headers.get("Content-Range") != f"bytes 0-31/{local.stat().st_size}":
                raise RuntimeError(f"Remote size mismatch: {path}")
            with local.open("rb") as source:
                if data != source.read(32):
                    raise RuntimeError(f"Remote audio header mismatch: {path}")
        print(f"Verified: {path}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    episodes = json.loads((ROOT / "rthk-2026-episodes.json").read_text(encoding="utf-8"))
    for episode in episodes:
        path = Path(episode["audio_path"])
        source = (ROOT / path).resolve()
        if not source.is_relative_to((ROOT / "audio").resolve()) or source.suffix != ".m4a":
            raise ValueError(f"Not a published audio path: {path}")
        if source.stat().st_size != int(episode["length"]) or source.stat().st_size == 0:
            raise ValueError(f"Invalid catalogued size: {path}")
    if not args.verify_only:
        if not (REPO / ".git").exists():
            REPO.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "clone", REMOTE, str(REPO)], check=True)
        if git("remote", "get-url", "origin") != REMOTE:
            raise RuntimeError("Unexpected audio repository remote")
        if git("status", "--porcelain"):
            raise RuntimeError("Audio repository has pending changes; inspect before publishing")
        git("pull", "--ff-only", "origin", "main")
        for episode in episodes:
            path = episode["audio_path"]
            target = REPO / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, target)
        git("add", "--", "audio")
        if git("diff", "--cached", "--name-only"):
            git("-c", "user.name=Chanlaze", "-c", "user.email=Chanlaze@users.noreply.github.com",
                "commit", "-m", "Update podcast audio")
        git("-c", "pack.window=0", "-c", "core.compression=0",
            "-c", "http.lowSpeedLimit=1024", "-c", "http.lowSpeedTime=120",
            "push", "origin", "main")
    verify(episodes)


if __name__ == "__main__":
    main()
