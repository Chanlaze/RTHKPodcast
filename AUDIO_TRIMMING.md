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
python publish_gitlab_audio.py
python generate_people_in_history_feed.py
```

## Audio hosting

Podcast audio is published to the public GitLab repository
`https://gitlab.com/chanlaze-group/Chanlaze-project` on branch `main`.
The existing GitHub Pages feed URL and episode GUIDs remain unchanged.
Original downloads stay in `.tools/audio-originals/` and are never uploaded.

After downloading and validating a new edited episode, run
`python publish_gitlab_audio.py` before generating or publishing the feed.
This copies only catalogued files into `.tools/gitlab-audio`, commits and pushes
them, then checks public ranged downloads, file sizes, and audio headers.
Any failure must stop feed publication. Recheck without uploading with
`python publish_gitlab_audio.py --verify-only`.

Commit the metadata, feed, and source changes to GitHub, not new audio files.
Existing GitHub audio remains available for podcast apps with cached old URLs.
Do not delete or rewrite that history as part of a routine update.
