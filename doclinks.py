"""Validate simple relative Markdown inline links within a checkout."""
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

LINK = re.compile(r"(?<!!)\]\(([^)\s]+)\)")

def broken_links(root, document):
    root = Path(root).resolve()
    document = (root / document).resolve()
    if not document.is_relative_to(root):
        raise ValueError("document must be inside root")
    errors = []
    # Scope is simple inline links, not a complete Markdown parser.
    source = document.read_text(encoding="utf-8")
    source = re.sub(r"(?ms)^\s*```[^\n]*\n.*?^\s*```\s*$", "", source)
    for link in LINK.findall(source):
        try:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (document.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(root) or not target.exists():
                errors.append(link)
        except (ValueError, OSError):
            errors.append(link)
    return errors
