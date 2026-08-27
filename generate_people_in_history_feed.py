#!/usr/bin/env python3
"""Generate a podcast RSS feed from the GitLab RTHK archive."""

from __future__ import annotations

import email.utils
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


PROJECT = "rthk-archive/people-in-history"
PROJECT_ENCODED = urllib.parse.quote(PROJECT, safe="")
API_ROOT = f"https://gitlab.com/api/v4/projects/{PROJECT_ENCODED}"
REPO_LINK = f"https://gitlab.com/{PROJECT}"
RTHK_PROGRAMME_URL = "https://www.rthk.hk/radio/radio1/programme/People"
OUTPUT = Path("people-in-history.xml")
OUTPUT_2026 = Path("people-in-history-2026.xml")
LOCAL_EPISODES = Path("rthk-2026-episodes.json")
SITE_ROOT = "https://chanlaze.github.io/RTHKPodcast"
ARTWORK_FILENAME = "people-in-history-cover.jpg"
ARTWORK_URL = f"{SITE_ROOT}/{ARTWORK_FILENAME}"

ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
ET.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
ET.register_namespace("itunes", "http://www.itunes.com/dtds/podcast-1.0.dtd")


def get_json(url: str) -> tuple[object, dict[str, str]]:
    request = urllib.request.Request(url, headers={"User-Agent": "podcast-feed-generator/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
        headers = {key.lower(): value for key, value in response.headers.items()}
    return data, headers


def fetch_tree() -> list[dict[str, str]]:
    page = 1
    items: list[dict[str, str]] = []
    while True:
        url = f"{API_ROOT}/repository/tree?recursive=true&per_page=100&page={page}"
        data, headers = get_json(url)
        items.extend(data)
        if not headers.get("x-next-page"):
            return items
        page += 1


def fetch_default_branch() -> str:
    data, _ = get_json(API_ROOT)
    return data.get("default_branch") or "master"


def parse_episode_date(title: str) -> datetime | None:
    match = re.search(r"\b(20\d{6})\b", title)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y%m%d").replace(tzinfo=timezone.utc)


def clean_episode_title(raw_title: str) -> str:
    """Return titles like 維多利亞女王(七), dropping show name/date/subtitle."""
    title = re.sub(r"^古今風雲人物\s+", "", raw_title).strip()
    title = re.sub(r"^20\d{6}\s+", "", title).strip()
    match = re.match(
        r"^(.*?)\s*[\(（]([一二三四五六七八九十百]+)[\)）](?:[︰:：].*)?$", title
    )
    if match:
        return f"{match.group(1).strip()}({match.group(2)})"
    parts = title.split()

    for index, part in enumerate(parts):
        if re.fullmatch(r"[一二三四五六七八九十百]+", part):
            subject = " ".join(parts[:index]).strip()
            if subject:
                return f"{subject}({part})"

    return title


def rfc2822(dt: datetime) -> str:
    return email.utils.format_datetime(dt)


def add_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    child = ET.SubElement(parent, tag)
    child.text = text
    return child


def load_local_episodes() -> list[dict[str, object]]:
    if not LOCAL_EPISODES.exists():
        return []
    return json.loads(LOCAL_EPISODES.read_text(encoding="utf-8"))


def build_feed(
    mp3_entries: list[dict[str, str]],
    branch: str,
    local_episodes: list[dict[str, object]],
    output: Path,
    channel_title: str,
    channel_description: str,
    include_archive: bool,
) -> ET.ElementTree:
    now = datetime.now(timezone.utc)
    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
            "xmlns:dc": "http://purl.org/dc/elements/1.1/",
            "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        },
    )
    channel = ET.SubElement(rss, "channel")
    add_text(channel, "title", channel_title)
    add_text(channel, "link", RTHK_PROGRAMME_URL)
    add_text(channel, "language", "zh-HK")
    add_text(channel, "copyright", "RTHK / archive sources hosted on GitHub and GitLab")
    add_text(
        channel,
        "description",
        channel_description,
    )
    add_text(channel, "lastBuildDate", rfc2822(now))
    add_text(channel, "pubDate", rfc2822(now))
    add_text(channel, "ttl", "1440")
    add_text(channel, "itunes:author", "RTHK")
    add_text(channel, "itunes:summary", channel_description)
    add_text(channel, "itunes:explicit", "false")
    ET.SubElement(channel, "itunes:category", {"text": "History"})
    ET.SubElement(channel, "itunes:image", {"href": ARTWORK_URL})
    image = ET.SubElement(channel, "image")
    add_text(image, "url", ARTWORK_URL)
    add_text(image, "title", channel_title)
    add_text(image, "link", SITE_ROOT)
    ET.SubElement(
        channel,
        "atom:link",
        {
            "href": f"{SITE_ROOT}/{output.name}",
            "rel": "self",
            "type": "application/rss+xml",
        },
    )

    items: list[dict[str, object]] = []
    local_dates = {str(episode["date"]).replace("-", "") for episode in local_episodes}
    for entry in mp3_entries if include_archive else []:
        path = entry["path"]
        raw_title = Path(path).stem
        pub_date = parse_episode_date(raw_title) or now
        if pub_date.strftime("%Y%m%d") in local_dates:
            continue
        encoded_path = "/".join(urllib.parse.quote(part) for part in path.split("/"))
        encoded_branch = urllib.parse.quote(branch, safe="")
        audio_url = f"https://gitlab.com/{PROJECT}/-/raw/{encoded_branch}/{encoded_path}"
        items.append(
            {
                "title": clean_episode_title(raw_title),
                "description": clean_episode_title(raw_title),
                "summary": clean_episode_title(raw_title),
                "date_iso": pub_date.date().isoformat(),
                "pub_date": pub_date,
                "audio_url": audio_url,
                "length": "0",
                "type": "audio/mpeg",
                "source_url": audio_url,
            }
        )

    for episode in local_episodes:
        pub_date = datetime.strptime(str(episode["date"]), "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        audio_path = "/".join(
            urllib.parse.quote(part) for part in str(episode["audio_path"]).split("/")
        )
        items.append(
            {
                "title": str(episode["title"]),
                "description": (
                    f"日期：{episode['date']}\n\n{episode.get('notes', '')}"
                ).strip(),
                "summary": str(episode.get("notes", "")),
                "date_iso": str(episode["date"]),
                "pub_date": pub_date,
                "audio_url": f"{SITE_ROOT}/{audio_path}",
                "length": str(episode.get("length", 0)),
                "type": "audio/mp4",
                "source_url": str(episode["source_page"]),
            }
        )

    for feed_item in sorted(items, key=lambda item: item["pub_date"], reverse=True):
        title = str(feed_item["title"])
        pub_date = feed_item["pub_date"]
        audio_url = str(feed_item["audio_url"])

        item = ET.SubElement(channel, "item")
        add_text(item, "title", title)
        add_text(item, "description", str(feed_item["description"]))
        add_text(item, "link", str(feed_item["source_url"]))
        add_text(item, "pubDate", rfc2822(pub_date))
        add_text(item, "dc:date", str(feed_item["date_iso"]))
        add_text(item, "itunes:title", title)
        add_text(item, "itunes:summary", str(feed_item["summary"]))
        add_text(item, "guid", audio_url).set("isPermaLink", "false")
        ET.SubElement(
            item,
            "enclosure",
            {
                "url": audio_url,
                "length": str(feed_item["length"]),
                "type": str(feed_item["type"]),
            },
        )

    ET.indent(rss, space="  ")
    return ET.ElementTree(rss)


def main() -> None:
    branch = fetch_default_branch()
    tree = fetch_tree()
    mp3_entries = [
        item for item in tree
        if item.get("type") == "blob" and item.get("path", "").lower().endswith(".mp3")
    ]
    if not mp3_entries:
        raise SystemExit("No MP3 files found in GitLab repository tree.")
    print(f"Found {len(mp3_entries)} MP3 files on branch {branch}")
    local_episodes = load_local_episodes()
    feed = build_feed(
        mp3_entries,
        branch,
        local_episodes,
        OUTPUT,
        "古今風雲人物 People In History",
        "RTHK 古今風雲人物 audio archive from the current RTHK programme and the public GitLab MP3 repository.",
        True,
    )
    feed.write(OUTPUT, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    print(f"Wrote {OUTPUT}")
    feed_2026 = build_feed(
        mp3_entries,
        branch,
        local_episodes,
        OUTPUT_2026,
        "古今風雲人物 2026",
        "RTHK 古今風雲人物 2026 episodes with full titles, broadcast dates, and programme notes.",
        False,
    )
    feed_2026.write(
        OUTPUT_2026, encoding="utf-8", xml_declaration=True, short_empty_elements=True
    )
    print(f"Wrote {OUTPUT_2026}")


if __name__ == "__main__":
    main()
