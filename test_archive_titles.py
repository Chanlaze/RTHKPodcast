import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

import generate_people_in_history_feed as feed
from import_wikipedia_titles import expand_topic, normalize, number


class ArchiveTitleTests(unittest.TestCase):
    def test_multipart_titles(self):
        self.assertEqual(expand_topic("身世考究（上、下）"), ["身世考究（上）", "身世考究（下）"])
        self.assertEqual(expand_topic("南北戰爭（上、中、下）"), ["南北戰爭（上）", "南北戰爭（中）", "南北戰爭（下）"])
        self.assertEqual(expand_topic("征服者（上）——圍攻"), ["征服者（上）——圍攻"])

    def test_identity(self):
        self.assertEqual(normalize("彼德大帝"), normalize("彼得大帝"))
        self.assertEqual(normalize("宋太祖 宋太宗"), normalize("宋太祖、宋太宗"))
        self.assertEqual([number(n) for n in ["一", "十", "十二", "二十"]], [1, 10, 12, 20])

    def test_catalogue(self):
        data = json.loads(feed.ARCHIVE_TITLES.read_text(encoding="utf-8"))
        titles = [v["title"] for v in data["titles"].values()]
        self.assertIn("岳飛(一)︰身世考究（上）", titles)
        self.assertIn("岳飛(二)︰身世考究（下）", titles)
        self.assertFalse(any(t.startswith("希特拉(") for t in titles))

    def test_rebuild_preserves_downloads_and_dates(self):
        old = ET.parse("people-in-history.xml")
        prefix = f"https://gitlab.com/{feed.PROJECT}/-/raw/master/"
        entries = [{"path": unquote(i.find("enclosure").get("url")[len(prefix):])}
                   for i in old.findall("./channel/item")
                   if i.find("enclosure").get("url").startswith(prefix)]
        new = feed.build_feed(entries, "master", feed.load_local_episodes(), Path("people-in-history.xml"), "Test", "Test")
        before = {i.findtext("guid"): (i.findtext("pubDate"), i.find("enclosure").attrib)
                  for i in old.findall("./channel/item")}
        after = {i.findtext("guid"): (i.findtext("pubDate"), i.find("enclosure").attrib)
                 for i in new.findall("./channel/item")}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
