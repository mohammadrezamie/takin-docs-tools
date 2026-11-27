"""Opt-in validation for simple Markdown heading links, without network I/O.

This intentionally supports a bounded syntax: ATX headings, explicit HTML
id/name attributes, fenced code, and ordinary inline links. It is not a
complete CommonMark or GitHub rendering engine.
"""
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^ {0,3}#{1,6}[ \t]+(.+?)\s*$")
EXPLICIT = re.compile(r"<[a-zA-Z][^>]*?\b(?:id|name)\s*=\s*(['\"])(.*?)\1", re.I)
LINK = re.compile(r"(?<!!)\]\(([^)\s]+)\)")
INLINE_CODE = re.compile(r"(`+).*?\1")

def prose_lines(source):
    fence = None
    for line in source.splitlines():
        match = FENCE.match(line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence) and not match[2].strip():
                fence = None
            continue
        if match:
            fence = match[1]
            continue
        yield line

def heading_ids(source):
    used = set()
    explicit = set()
    for line in prose_lines(source):
        # Explicit anchors in inline code are examples, not navigation.
        explicit.update(m[2] for m in EXPLICIT.finditer(INLINE_CODE.sub("", line)))
        match = HEADING.match(line)
        if not match:
            continue
        heading = re.sub(r"[ \t]+#+[ \t]*$", "", match[1])
        # A conservative slug for plain headings; inline markup beyond
        # simple emphasis/backticks is outside the supported syntax.
        heading = re.sub(r"[^\w\s-]", "", heading.lower(), flags=re.UNICODE)
        base = re.sub(r"\s", "-", heading.strip())
        slug = base
        suffix = 1
        while slug in used:
            slug = f"{base}-{suffix}"
            suffix += 1
        used.add(slug)
    return used | explicit

def missing_fragments(root, document):
    """Return missing local Markdown fragments; path checks are separate.

    Non-Markdown targets, external URLs and links inside fenced/inline code
    are intentionally ignored. Missing/escaping paths remain doclinks'
    responsibility. Input files and output stay on the caller's machine.
    """
    root = Path(root).resolve()
    source = (root / document).resolve()
    if not source.is_relative_to(root):
        raise ValueError("document must be inside root")
    cache = {}
    errors = []
    for line in prose_lines(source.read_text(encoding="utf-8")):
        for link in LINK.findall(INLINE_CODE.sub("", line)):
            try:
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.fragment:
                    continue
                target = (source.parent / unquote(parsed.path)).resolve() if parsed.path else source
                if not target.is_relative_to(root) or target.suffix.lower() != ".md" or not target.is_file():
                    continue
                if target not in cache:
                    cache[target] = heading_ids(target.read_text(encoding="utf-8"))
                if unquote(parsed.fragment) not in cache[target]:
                    errors.append(link)
            except (ValueError, OSError, UnicodeError):
                errors.append(link)
    return errors
