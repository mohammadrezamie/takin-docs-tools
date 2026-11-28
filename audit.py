"""Audit an explicitly selected collection of local Markdown documents.

No network, automatic discovery, Git dependency or source modification.
"""
import argparse
import json
from pathlib import Path
import sys

from anchors import missing_fragments
from doclinks import broken_links


def audit(root, documents, *, fragments=False):
    """Return deterministic diagnostics for all selected documents.

    Documents must be unique relative paths to existing Markdown files
    within root. Symlink escapes and aliases are rejected. An empty or
    unreadable selection is an input error, never a passing audit.
    """
    if isinstance(documents, (str, bytes, dict)) or type(fragments) is not bool:
        raise ValueError("invalid document collection or fragment option")
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be a directory")
    selected = {}
    for raw in documents:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("document paths must be nonempty strings")
        path = Path(raw)
        if path.is_absolute():
            raise ValueError("document paths must be relative to root")
        target = (root / path).resolve(strict=True)
        if not target.is_relative_to(root) or not target.is_file() or target.suffix.lower() != ".md":
            raise ValueError("document must be a Markdown file inside root")
        if target in selected:
            raise ValueError("duplicate document or resolved alias")
        selected[target] = target.relative_to(root).as_posix()
    if not selected:
        raise ValueError("at least one document is required")
    rows = []
    for target, name in sorted(selected.items(), key=lambda pair: pair[1]):
        paths = broken_links(root, name)
        anchors = missing_fragments(root, name) if fragments else []
        rows.append({"document": name, "paths": paths, "fragments": anchors})
    issues = sum(len(row["paths"]) + len(row["fragments"]) for row in rows)
    return {"ok": issues == 0, "checked": len(rows), "issues": issues,
            "fragment_checks": fragments, "documents": rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Local directory containing the selected documents")
    parser.add_argument("--fragments", action="store_true", help="Also check supported local heading fragments")
    parser.add_argument("documents", nargs="+", help="Explicit root-relative Markdown files")
    args = parser.parse_args(argv)
    try:
        report = audit(args.root, args.documents, fragments=args.fragments)
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0 if report["ok"] else 1
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        # No source content, absolute paths or raw exception messages in this
        # summary. The caller may invoke the API to inspect local exceptions.
        print(json.dumps({"ok": False, "blocked": True, "error": type(exc).__name__}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
