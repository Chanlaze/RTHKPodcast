# Podcast-ready audio editing

New downloads are matched against the approved programme-intro reference in
`audio-reference/people-in-history-intro.m4a`. Everything before that match is
removed. The final seven minutes are also scanned for six approximately 1050 Hz
tones, each 0.12-0.30 seconds long and spaced one second apart. Everything from
the confirmed closing signal onward is removed.

Both boundaries must be detected before an edited episode is published. The
edit uses AAC stream copy, so packet boundaries limit precision to approximately
one audio packet and the audio is not re-encoded.

Unmatched files are preserved for manual review. Every untouched recording is
backed up in `.tools/audio-originals/`, which is ignored by Git. Podcast feeds
link only to the edited copy under `audio/2026/`.
Feed episode IDs and filenames stay stable; previously downloaded copies
in podcast apps need to be downloaded again to receive the trimmed audio.

Install analysis dependencies on a new machine:

```powershell
python -m pip install numpy imageio-ffmpeg --target .tools
```

Scan existing files without changing them:

```powershell
python trim_time_signal.py
```

Trim confirmed matches and update enclosure lengths in the metadata:

```powershell
python trim_time_signal.py --apply
python generate_people_in_history_feed.py
```
