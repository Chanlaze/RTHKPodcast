# Closing time signal

New downloads are scanned for six approximately 1050 Hz tones, each 0.12-0.30
seconds long and spaced one second apart, within the final seven minutes.
Only a single unambiguous sequence is accepted. The file is trimmed just
before the first tone using AAC stream copy (no re-encoding). AAC packet
boundaries limit the cut precision to approximately one audio packet.

Unmatched files are preserved for manual review. Original recordings are
backed up in `.tools/audio-originals/`, which is ignored by Git.
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
