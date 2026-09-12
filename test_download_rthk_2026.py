import unittest

from download_rthk_2026 import merge_placeholder_episode_metadata


class PlaceholderMetadataTests(unittest.TestCase):
    def test_pairs_saturday_audio_with_titled_next_day_record(self):
        episodes = [
            {
                "id": "details",
                "date": "2026-09-13",
                "title": "漢武帝 (十四)︰太子之死",
                "source_page": "details-page",
                "stream_url": "missing-sunday-stream",
                "notes": "full notes",
            },
            {
                "id": "audio",
                "date": "2026-09-12",
                "title": "古今風雲人物",
                "source_page": "audio-page",
                "stream_url": "saturday-stream",
                "notes": "generic",
            },
        ]

        result = merge_placeholder_episode_metadata(episodes)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date"], "2026-09-12")
        self.assertEqual(result[0]["title"], "漢武帝 (十四)︰太子之死")
        self.assertEqual(result[0]["stream_url"], "saturday-stream")
        self.assertEqual(result[0]["source_page"], "details-page")
        self.assertEqual(result[0]["notes"], "full notes")

    def test_does_not_merge_incomplete_title(self):
        episodes = [
            {"date": "2026-09-12", "title": "古今風雲人物"},
            {"date": "2026-09-13", "title": "漢武帝"},
        ]

        self.assertEqual(len(merge_placeholder_episode_metadata(episodes)), 2)


if __name__ == "__main__":
    unittest.main()
