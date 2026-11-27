# RTHKPodcast project instructions

This project is now maintained in Google Antigravity. The Codex daily automation was paused at the user's request on 2026-11-27. Do not recreate or reactivate a Codex schedule.

Read ANTIGRAVITY_HANDOVER.md before running the daily workflow. Use the existing local workspace, including its ignored .tools directory; a fresh clone does not include the original audio backups, dependencies or GitLab audio clone.

## Invariants

- Source new titles, dates and notes only from the official RTHK programme and episode metadata. Wikipedia was a one-time archive backfill; preserve archive-episode-titles.json without refreshing it.
- Keep one complete people-in-history.xml feed at https://chanlaze.github.io/RTHKPodcast/people-in-history.xml. Never recreate a separate 2026 feed.
- GitHub Chanlaze/RTHKPodcast, branch master: scripts, metadata, artwork and XML only. Do not upload new audio there.
- GitLab chanlaze-group/Chanlaze-project, branch main: edited audio. Use publish_gitlab_audio.py; verify uploads before publishing XML.
- Untouched downloads stay in .tools/audio-originals as local backups only. Keep both original and edited copies.
- Trim before the approved intro and from the confirmed closing six-tone signal onward. Preserve the intro when audio already starts there. Never guess uncertain boundaries or publish a partially edited recording.
- Filenames retain the date followed by the complete title. Keep existing GUIDs and subscription URL stable.
- Missing or generic notes alone are not a blocker when title, date, regular programme topic, audio and both boundaries are verified. Do not invent notes.
- Preserve unrelated changes and historical audio links. Do not bulk-stage audio, remove backups or rewrite Git history.
- Never print, copy into documents, or commit credentials. Existing Git credentials may work, but Antigravity permissions must be verified independently.
- Daily schedule: 06:00 Asia/Hong_Kong. When no new valid episode is found, do not write or push the feed. Notify on errors/action needed, not routine no-change checks.
- Only one publishing run at a time. A failed GitLab upload or verification must prevent feed publication.

