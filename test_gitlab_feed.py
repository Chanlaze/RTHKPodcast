import unittest
import urllib.parse
from pathlib import Path

from generate_people_in_history_feed import AUDIO_ROOT, SITE_ROOT, build_feed, load_local_episodes


class GitLabFeedTests(unittest.TestCase):
    def test_migration_preserves_metadata_and_guids(self):
        episodes = load_local_episodes()
        tree = build_feed([], "master", episodes, Path("people-in-history.xml"), "Podcast", "Archive")
        items = tree.findall("./channel/item")
        self.assertEqual(len(items), len(episodes))
        by_title = {item.findtext("title"): item for item in items}
        for episode in episodes:
            item = by_title[episode["title"]]
            self.assertEqual(item.findtext("guid"),
                             f"{SITE_ROOT}/audio/2026/{episode['date'].replace('-', '')}.m4a")
            enclosure = item.find("enclosure")
            self.assertEqual(enclosure.get("url"),
                             AUDIO_ROOT + "/" + urllib.parse.quote(episode["audio_path"], safe="/"))
            self.assertEqual(enclosure.get("length"), str(episode["length"]))
            self.assertIn(episode["notes"], item.findtext("description"))
            self.assertIsNotNone(item.findtext("pubDate"))


if __name__ == "__main__":
    unittest.main()
