import tempfile
import unittest
from pathlib import Path
from anchors import heading_ids, missing_fragments

class AnchorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "target file.md").write_text(
            "# Hello World\n## Hello World\n## Hello World-1\n"
            "## Café\n<a name='legacy'></a>\n~~~md\n# Hidden\n~~~\n",
            encoding="utf-8",
        )

    def check(self, text):
        (self.root / "page.md").write_text(text, encoding="utf-8")
        return missing_fragments(self.root, "page.md")

    def test_headings_and_duplicates(self):
        self.assertEqual(heading_ids("# A\n# A\n# A-1\n# A\n"), {"a", "a-1", "a-1-1", "a-2"})

    def test_cross_file_and_local(self):
        self.assertEqual(self.check(
            "# Here\n[local](#here) [other](target%20file.md#hello-world-1) "
            "[encoded](target%20file.md#caf%C3%A9) [old](target%20file.md#legacy)"
        ), [])

    def test_missing_and_fenced(self):
        self.assertEqual(self.check(
            "[bad](target%20file.md#hidden) [missing](#absent)\n"
            "````md\n```\n[example](#ignore)\n```\n````\n"
            "~~~\n[example](#ignore-too)\n~~~\n"
            "`[example](#inline)`"
        ), ["target%20file.md#hidden", "#absent"])

    def test_external_nonmarkdown_and_missing_paths(self):
        self.assertEqual(self.check(
            "[web](https://example.com#x) [missing](missing.md#x) "
            "[escape](../outside.md#x) [pdf](a.pdf#page=2)"
        ), [])

    def test_explicit_and_punctuation(self):
        self.assertEqual(heading_ids(
            "## A & B ###\n<a id=\"custom\"></a>\n`<a id='example'>`\n"
        ), {"a--b", "custom"})

    def test_outside_document(self):
        with self.assertRaises(ValueError):
            missing_fragments(self.root, "../outside.md")
