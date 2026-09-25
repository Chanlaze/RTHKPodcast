"""Build reviewed archive title metadata from a saved Wikipedia HTML page.

One-time import dependency: beautifulsoup4. Feed generation needs only the JSON.
"""
import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

from generate_people_in_history_feed import clean_episode_title

SOURCE = "https://zh.wikipedia.org/wiki/古今風雲人物"


def expand_topic(text):
    match = re.search(r"[（(]([上中下](?:、[上中下])+)[）)]", text)
    if not match:
        return [text]
    return [text[:match.start()] + f"（{part}）" + text[match.end():]
            for part in match[1].split("、")]


def normalize(text):
    text = text.replace("汉", "漢").replace("彼德", "彼得")
    text = re.sub(r"[\s·．、—]+", "", text)
    return text.removeprefix("喬治") if text.endswith("華盛頓") else text


def number(text):
    digits = "零一二三四五六七八九"
    if "十" in text:
        tens, units = text.split("十")
        return (digits.index(tens) if tens else 1) * 10 + (digits.index(units) if units else 0)
    return digits.index(text)


def import_titles(html, feed):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("sup, .noprint"):
        node.decompose()
    series = {}
    skipped = []
    for row in soup.select("table.wikitable tr"):
        cells = row.find_all("td", recursive=False)
        if len(cells) != 6:
            continue
        subject = cells[0].get_text("", strip=True)
        count = re.fullmatch(r"(\d+)集", cells[2].get_text(strip=True))
        topics = [topic for li in cells[5].select("li")
                  for topic in expand_topic(li.get_text("", strip=True).replace("\u200b", ""))]
        if not count or len(topics) != int(count[1]):
            skipped.append({"subject": subject, "declared": cells[2].get_text(strip=True),
                            "topics": len(topics)})
            continue
        series.setdefault(normalize(subject), []).append((int(cells[1].get_text(strip=True)[-4:]), topics))

    titles = {}
    counts = {"wikipedia": 0, "filename": 0, "unchanged": 0}
    for item in feed.findall("./channel/item"):
        url = item.find("enclosure").get("url")
        prefix = "https://gitlab.com/rthk-archive/people-in-history/-/raw/"
        if not url.startswith(prefix):
            continue
        path = unquote(url[len(prefix):].split("/", 1)[1])
        raw = Path(path).stem
        base = clean_episode_title(raw)
        match = re.fullmatch(r"(.+)\(([一二三四五六七八九十]+)\)", base)
        date = re.search(r"\b(20\d{6})\b", raw)
        topic = None
        origin = "filename"
        if match and date:
            candidates = [(year, topics) for year, topics in series.get(normalize(match[1]), [])
                          if 0 <= int(date[1][:4]) - year <= 1]
            if len(candidates) == 1:
                topics = candidates[0][1]
                index = number(match[2]) - 1
                if 0 <= index < len(topics):
                    topic, origin = topics[index], "wikipedia"
            if topic is None:
                suffix = re.search(r"\s" + match[2] + r"\s+(.+)$", raw)
                if suffix:
                    topic = suffix[1].strip()
        if topic:
            titles[path] = {"title": f"{base}︰{topic}", "source": SOURCE if origin == "wikipedia" else url}
            counts[origin] += 1
        else:
            counts["unchanged"] += 1
    return {"source": SOURCE, "titles": titles, "skipped_series": skipped}, counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path)
    args = parser.parse_args()
    data, counts = import_titles(args.html.read_text(encoding="utf-8"), ET.parse("people-in-history.xml"))
    Path("archive-episode-titles.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(counts)
    print(json.dumps(data["skipped_series"], ensure_ascii=False))
