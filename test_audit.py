import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from audit import audit, main


class AuditTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.parent = Path(tmp.name)
        self.root = self.parent / "project"
        self.root.mkdir()
        self.write("a.md", "# Intro\n[guide](b.md#guide)\n")
        self.write("b.md", "# Guide\n")

    def write(self, name, text):
        (self.root / name).write_text(text, encoding="utf-8")

    def invoke(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = main(["--root", str(self.root), *args])
        return status, json.loads(out.getvalue())

    def test_all_selected_documents_pass_in_sorted_order(self):
        result = audit(self.root, ["b.md", "a.md"], fragments=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["checked"], 2)
        self.assertEqual([row["document"] for row in result["documents"]], ["a.md", "b.md"])
        self.assertEqual(result["issues"], 0)

    def test_reports_paths_and_fragments_separately(self):
        self.write("a.md", "[missing](lost.md)\n[anchor](b.md#absent)\n")
        result = audit(self.root, ["a.md", "b.md"], fragments=True)
        self.assertFalse(result["ok"])
        self.assertEqual(result["issues"], 2)
        self.assertEqual(result["documents"][0], {
            "document": "a.md", "paths": ["lost.md"], "fragments": ["b.md#absent"]
        })

    def test_fragments_are_explicitly_opt_in(self):
        self.write("a.md", "[anchor](b.md#absent)\n")
        result = audit(self.root, ["a.md"])
        self.assertTrue(result["ok"])
        self.assertFalse(result["fragment_checks"])
        self.assertFalse(audit(self.root, ["a.md"], fragments=True)["ok"])

    def test_cli_exit_codes(self):
        self.assertEqual(self.invoke("--fragments", "a.md")[0], 0)
        self.write("a.md", "[bad](missing.md)")
        code, report = self.invoke("a.md")
        self.assertEqual(code, 1)
        self.assertEqual(report["issues"], 1)
        code, report = self.invoke("missing.md")
        self.assertEqual(code, 2)
        self.assertTrue(report["blocked"])

    def test_empty_duplicate_and_normalized_aliases_rejected(self):
        for docs in ([], ["a.md", "a.md"], ["a.md", "./a.md"], "a.md", {"a.md": 1}):
            with self.subTest(docs=docs), self.assertRaises(ValueError):
                audit(self.root, docs)

    def test_missing_nonmarkdown_directory_and_absolute_paths_blocked(self):
        self.write("read.txt", "example")
        (self.root / "dir.md").mkdir()
        for name in ("missing.md", "read.txt", "dir.md", str(self.root / "a.md")):
            with self.subTest(name=name):
                code, result = self.invoke(name)
                self.assertEqual(code, 2)
                self.assertTrue(result["blocked"])

    def test_root_escape_and_symlink_aliases_rejected(self):
        outside = self.parent / "outside.md"
        outside.write_text("# Outside", encoding="utf-8")
        (self.root / "escape.md").symlink_to(outside)
        (self.root / "alias.md").symlink_to(self.root / "a.md")
        for docs in (["../outside.md"], ["escape.md"], ["a.md", "alias.md"]):
            with self.subTest(docs=docs), self.assertRaises(ValueError):
                audit(self.root, docs)

    def test_invalid_utf8_cannot_pass_or_leak_raw_source(self):
        (self.root / "a.md").write_bytes(b"\xffsecret-synthetic-text")
        code, report = self.invoke("a.md")
        self.assertEqual(code, 2)
        self.assertTrue(report["blocked"])
        self.assertNotIn("secret-synthetic-text", str(report))
        self.assertNotIn(str(self.root), str(report))

    def test_non_directory_root_is_rejected(self):
        with self.assertRaises(ValueError):
            audit(self.root / "a.md", ["b.md"])

    def test_unicode_and_spaces_in_document_names(self):
        self.write("café guide.MD", "# Guide\n")
        result = audit(self.root, ["café guide.MD"])
        self.assertTrue(result["ok"])
        self.assertEqual(result["documents"][0]["document"], "café guide.MD")


if __name__ == "__main__":
    unittest.main()
