# Antigravity handover

## Workspace and status

Use this existing folder: C:\Users\chanl\OneDrive\文件\RTHKPodcast

Migration prepared 2026-11-27. Codex automation update-rthk-podcast-daily is PAUSED at the user's request. No future monitoring is to run in Codex. Antigravity scheduling must be enabled and verified in Antigravity; the existence of this document is not proof that it is active.

The prepared automation is installed at C:\Users\chanl\.gemini\config\sidecars\rthk-podcast-daily\sidecar.json, in its default paused state. Its versioned source is antigravity/rthk-podcast-daily/sidecar.json. Do not create a duplicate. Select the existing workspace, review scoped permissions, perform an Antigravity test run and enable this automation in the Automations dashboard. No access grants were preapproved by this migration.

Migration checks completed: all 17 unit tests passed; GitHub master and GitLab main push dry runs succeeded. Existing audio, metadata and XML were not changed. UI activation failed twice with "failed to activate captured window", so the project selection, unattended permission setup and active next-run verification remain pending in Antigravity. Open this existing folder as an Antigravity project; no file move is necessary. This handover preserves the working instructions, not an imported copy of the historical Codex conversation.

Keep the same folder rather than cloning elsewhere: .tools/audio-originals contains irreplaceable local backups, .tools/gitlab-audio is the audio repository clone, and .tools contains the analysis dependencies and FFmpeg. The entire source repository and Git history remain here.

## Daily task

Check for newly available episodes of RTHK 古今風雲人物 every day. Use the project's existing downloader and RTHK's underlying episode metadata and media sources to determine availability; do not rely only on the visible programme-page message because it may lag behind the actual audio release. Work in C:\Users\chanl\OneDrive\文件\RTHKPodcast and compare discovered episodes with rthk-2026-episodes.json and people-in-history.xml. Before downloading or publishing, verify the complete Chinese title from the official episode metadata, including the subject, chapter number, and subtitle, and confirm that the topic is a regular programme chapter or a normal continuation of the current series rather than a promo, trailer, station announcement, placeholder, repeat, or unrelated/special item. Capture the official broadcast date. Capture the official full programme notes when available, but missing or generic notes alone must not block publication once the title, date, regular-topic status, audio, and trimming boundaries are confirmed. For each valid new episode, run the existing downloader. It must retain the untouched download in .tools/audio-originals as the backup and publish a separate podcast-ready copy under audio/2026 only after both boundaries are confirmed: remove everything before the approved recurring programme intro and everything from the closing six-tone signal onward. If the audio already starts at the approved intro, keep the start and trim only the tail. Never link an original or partially edited recording in the XML. If either boundary, the audio, title, date, or regular-topic status cannot be confirmed, report the issue in this dedicated monitoring chat and leave the feed unchanged. Update rthk-2026-episodes.json, then run python publish_gitlab_audio.py to upload the catalogued podcast-ready copies to https://gitlab.com/chanlaze-group/Chanlaze-project on main and verify public ranged downloads and file sizes. Original backups must never be uploaded. Stop without publishing the feed if audio upload or verification fails. Only after GitLab verification succeeds, regenerate people-in-history.xml. Validate that the XML parses, every new enclosure points to its edited GitLab copy, every new episode has its untouched local backup, existing episode GUIDs remain stable, and the item count increases only by the number of genuinely new episodes. Commit metadata, the complete XML feed and relevant source changes to GitHub master; do not commit new audio to GitHub. Preserve existing GitHub audio for cached old links. Verify the live GitHub Pages feed and new GitLab audio URL. If there is no new valid episode, make no files, commit, or push, and stay quiet unless there is a meaningful change, failure, or required user action. Preserve unrelated working-tree changes and never overwrite user work. Use only the official RTHK episode page and its underlying metadata for new episode titles, broadcast dates, and programme notes. The Wikipedia title backfill was a one-off exercise: do not visit Wikipedia or rerun import_wikipedia_titles.py during daily checks. Preserve the saved archive-episode-titles.json catalogue when rebuilding the feed, without refreshing it from Wikipedia.

## Operation sequence

1. Read GEMINI.md and AUDIO_TRIMMING.md. Inspect Git status in the main repo and .tools/gitlab-audio. Preserve unrelated changes; do not run concurrent publishers.
2. Discover RTHK candidates without writing metadata first. The downloader exposes fetch_episodes(). Compare dates and official complete titles against the existing catalogue. Check the HLS media rather than trusting a stale page availability message.
3. Reject future episodes, generic placeholders, promos, repeats and unrelated items. Do not run the downloader blindly if discovery contains any invalid candidate.
4. Download only confirmed new regular episodes with the existing download_episode/find_ffmpeg helpers. Verify original backup, edited output and confirmed trimming boundaries. Preserve existing catalogue records instead of replacing the catalogue with an incomplete upstream listing.
5. Update catalogue only for validated episodes. Run python publish_gitlab_audio.py. Abort feed publishing on failure.
6. Run python generate_people_in_history_feed.py. Verify XML, new enclosure URLs and lengths, original backups, unchanged old GUIDs/dates/enclosures and expected item count.
7. Stage only the intended metadata, XML and relevant source changes. Commit and push to GitHub master. Never use git add . for routine publishing.
8. Verify the live GitHub Pages feed and public GitLab range downloads, allowing for Pages deployment delay. Report failures truthfully.
9. Maintain one local results log at .tools/antigravity-daily-results.jsonl for meaningful updates and failures, with Hong Kong timestamp, episode/date, outcome and commit references. No credentials. Keep this log out of Git.

## Validation before activating the replacement

- In this workspace run: python -m unittest discover -p "test_*.py"
- Verify the intro reference, local original backups, NumPy and FFmpeg are accessible.
- Test GitHub and GitLab authentication with push --dry-run to the existing branches; this does not publish changes.
- Have Antigravity perform a read-only discovery/test and configure narrowly scoped permissions through its supported setup. Do not grant unrestricted access as a migration shortcut.
- Create one persistent daily automation at 06:00 Asia/Hong_Kong, using the Daily task above and this existing folder. Check for duplicates first.
- Antigravity persistent automations create fresh conversations. The user accepted moving everything there despite that difference; keep the shared results log.
- Verify the automation is enabled and its next run is 06:00 Hong Kong time. Do not mistake a session-only /schedule timer for persistent automation.
- Keep Codex paused even if Antigravity needs manual permission approval, and clearly report any setup still pending.

## Known limitation

The downloader YEAR, metadata filename, audio directory and legacy GUID construction currently reference 2026. Before processing 2027 episodes, implement and test year rollover without changing existing GUIDs or dropping historical entries. Do not silently reset or replace the 2026 catalogue.

## Files

- download_rthk_2026.py: official discovery, HLS download and trim integration.
- trim_time_signal.py and audio-reference/people-in-history-intro.m4a: approved boundary detection.
- publish_gitlab_audio.py: edited audio upload and public verification.
- generate_people_in_history_feed.py: complete feed generation.
- rthk-2026-episodes.json: current episode metadata and audio lengths.
- archive-episode-titles.json: static historical title backfill.
- people-in-history-cover.jpg: artwork; preserve it.
- test_*.py: regression checks.

## Setup prompt for Antigravity

Take over this existing RTHKPodcast project. Read GEMINI.md and ANTIGRAVITY_HANDOVER.md. Codex monitoring has already been paused; do not use Codex again for this task. Validate the local project and Git credentials without publishing test changes, then create and enable exactly one persistent daily automation at 06:00 Asia/Hong_Kong following the Daily task instructions. Retain GitHub for the feed and GitLab for edited audio. Check for duplicates, use one shared local results log, and report the active automation and next run. Ask the user directly for any required authentication or permission approval rather than bypassing it.

## Antigravity references

- Rules: https://antigravity.google/docs/rules/
- Persistent automation: https://antigravity.google/docs/commands/automation

