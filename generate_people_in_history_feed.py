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
OUTPUT = Path("people-in-history.xml")

ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
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


def rfc2822(dt: datetime) -> str:
    return email.utils.format_datetime(dt)


def add_text(parent: ET.Element, tag: str, text: str) -> ET.Element:
    child = ET.SubElement(parent, tag)
    child.text = text
    return child


def build_feed(mp3_entries: list[dict[str, str]], branch: str) -> ET.ElementTree:
    now = datetime.now(timezone.utc)
    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
            "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
        },
    )
    channel = ET.SubElement(rss, "channel")
    add_text(channel, "title", "古今風雲人物 People In History")
    add_text(channel, "link", REPO_LINK)
    add_text(channel, "language", "zh-HK")
    add_text(channel, "copyright", "RTHK / archive source as hosted on GitLab")
    add_text(channel, "description", "RTHK 古今風雲人物 audio archive generated from the public GitLab MP3 repository.")
    add_text(channel, "lastBuildDate", rfc2822(now))
    add_text(channel, "pubDate", rfc2822(now))
    add_text(channel, "ttl", "1440")
    add_text(channel, "itunes:author", "RTHK")
    add_text(channel, "itunes:summary", "RTHK 古今風雲人物 audio archive.")
    add_text(channel, "itunes:explicit", "false")
    ET.SubElement(channel, "itunes:category", {"text": "History"})
    ET.SubElement(
        channel,
        "atom:link",
        {
            "href": "people-in-history.xml",
            "rel": "self",
            "type": "application/rss+xml",
        },
    )

    def sort_key(entry: dict[str, str]) -> tuple[str, str]:
        title = Path(entry["path"]).stem
        dt = parse_episode_date(title)
        return ((dt.isoformat() if dt else ""), entry["path"])

    for entry in sorted(mp3_entries, key=sort_key, reverse=True):
        path = entry["path"]
        title = Path(path).stem
        pub_date = parse_episode_date(title) or now
        encoded_path = "/".join(urllib.parse.quote(part) for part in path.split("/"))
        encoded_branch = urllib.parse.quote(branch, safe="")
        audio_url = f"https://gitlab.com/{PROJECT}/-/raw/{encoded_branch}/{encoded_path}"

        item = ET.SubElement(channel, "item")
        add_text(item, "title", title)
        add_text(item, "description", title)
        add_text(item, "pubDate", rfc2822(pub_date))
        add_text(item, "guid", audio_url).set("isPermaLink", "false")
        ET.SubElement(
            item,
            "enclosure",
            {
                "url": audio_url,
                "length": "0",
                "type": "audio/mpeg",
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
    feed = build_feed(mp3_entries, branch)
    feed.write(OUTPUT, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
