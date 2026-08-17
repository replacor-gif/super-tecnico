import json
import re
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UpdatesFeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.feed = json.loads((ROOT / "data" / "updates" / "feed.json").read_text(encoding="utf-8"))

    def test_feed_has_unique_reverse_chronological_entries(self):
        entries = self.feed["entries"]
        self.assertGreaterEqual(len(entries), 8)
        self.assertEqual(len({entry["id"] for entry in entries}), len(entries))
        dates = [date.fromisoformat(entry["date"]) for entry in entries]
        self.assertEqual(dates, sorted(dates, reverse=True))
        for entry in entries:
            self.assertTrue(entry["title"])
            self.assertTrue(entry["summary"])
            self.assertTrue(entry["areas"])
            self.assertIn(entry["author"]["type"], {"maintainer", "community", "anonymous"})
            self.assertTrue(entry["author"]["label"])

    def test_author_policy_matches_the_public_labels(self):
        policy = self.feed["author_policy"]
        self.assertEqual(policy["maintainer"], "Administrador")
        self.assertEqual(policy["missing_contributor_name"], "Usuario anónimo")
        maintainer_entries = [entry for entry in self.feed["entries"] if entry["author"]["type"] == "maintainer"]
        self.assertTrue(maintainer_entries)
        self.assertTrue(all(entry["author"]["label"] == "Administrador" for entry in maintainer_entries))

    def test_home_and_full_page_use_the_same_feed(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        page = (ROOT / "actualizaciones.html").read_text(encoding="utf-8")
        script = (ROOT / "assets" / "updates.js").read_text(encoding="utf-8")
        shell = (ROOT / "assets" / "app-shell.js").read_text(encoding="utf-8")
        self.assertIn("data-st-updates-preview", home)
        self.assertIn('data-limit="3"', home)
        self.assertIn("data-st-updates-list", page)
        self.assertIn("data/updates/feed.json", script)
        self.assertIn("actualizaciones.html", shell)
        self.assertIn("Proponer una mejora", page)

    def test_nickname_is_optional_and_server_has_anonymous_fallback(self):
        html = (ROOT / "feedback.html").read_text(encoding="utf-8")
        script = (ROOT / "assets" / "feedback.js").read_text(encoding="utf-8")
        backend = (ROOT / "api" / "index.php").read_text(encoding="utf-8")
        nickname_input = re.search(r'<input id="feedbackNickname"[^>]*>', html)
        self.assertIsNotNone(nickname_input)
        self.assertNotIn("required", nickname_input.group(0))
        self.assertIn("Usuario anónimo", script)
        self.assertIn("$body['nickname'] = 'Usuario anónimo'", backend)


if __name__ == "__main__":
    unittest.main()
