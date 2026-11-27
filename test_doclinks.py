import tempfile
import unittest
from pathlib import Path
from doclinks import broken_links

class LinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "guide").mkdir()
        (self.root / "read me.md").write_text("# Guide", encoding="utf-8")
    def check(self, text):
        (self.root / "guide" / "page.md").write_text(text, encoding="utf-8")
        return broken_links(self.root, "guide/page.md")
    def test_relative_and_external(self):
        self.assertEqual(self.check("[ok](../read%20me.md) [web](https://example.com) [local](#top)"), [])
    def test_missing(self):
        self.assertEqual(self.check("[bad](missing.md)"), ["missing.md"])
    def test_escape(self):
        self.assertEqual(self.check("[bad](../../outside.md)"), ["../../outside.md"])
        with self.assertRaises(ValueError):
            broken_links(self.root, "../outside.md")
    def test_fenced_example(self):
        self.assertEqual(self.check("```md\n[example](not-real.md)\n```\n"), [])
