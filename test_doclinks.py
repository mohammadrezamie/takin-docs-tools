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
        (self.root / "assets").mkdir()
        (self.root / "assets" / "diagram.svg").write_text("<svg/>", encoding="utf-8")

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
        fence = chr(96) * 3
        self.assertEqual(self.check(fence + "md\n[example](not-real.md)\n" + fence + "\n"), [])

    def test_reference_and_collapsed_reference(self):
        text = ("[ok][Read Me] [Read Me][]\n"
                "[read me]: <../read me.md> \"A title\"\n")
        self.assertEqual(self.check(text), [])

    def test_missing_reference_definition(self):
        self.assertEqual(self.check("[bad][unknown]"), ["[bad][unknown]"])

    def test_reference_to_missing_target(self):
        self.assertEqual(self.check("[bad][missing]\n[missing]: missing.md\n"),
                         ["missing.md"])

    def test_local_images_are_checked(self):
        self.assertEqual(self.check("![ok](../assets/diagram.svg) ![bad](../assets/missing.svg)"),
                         ["../assets/missing.svg"])

    def test_reference_images_are_checked(self):
        text = "![diagram][asset]\n[asset]: ../assets/diagram.svg\n"
        self.assertEqual(self.check(text), [])

    def test_angle_destination_with_spaces_and_title(self):
        self.assertEqual(self.check("[ok](<../read me.md> \"title\")"), [])

    def test_code_and_external_reference_are_ignored(self):
        fence = chr(96) * 3
        tick = chr(96)
        text = (tick + "[inline](no.md)" + tick + "\n"
                + fence + "md\n![example](missing.svg)\n[bad][missing]\n"
                + fence + "\n[web][external]\n[external]: https://example.com\n")
        self.assertEqual(self.check(text), [])


if __name__ == "__main__":
    unittest.main()
