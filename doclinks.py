"""Validate local Markdown inline/reference links and image targets in a checkout."""
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

FENCE = re.compile(r"^ {0,3}(\x60{3,}|~{3,})(.*)$")
INLINE_CODE = re.compile(r"(\x60+).*?\1", re.S)
INLINE_LINK = re.compile(r"(!?)\]\((<[^>\n]+>|[^)\s]+)(?:[ \t]+(?:\"[^\"]*\"|'[^']*'))?\)")
REFERENCE_DEFINITION = re.compile(
    r"""(?m)^ {0,3}\[([^\]\n]+)\]:[ \t]*(<[^>\n]+>|[^\s]+)(?:[ \t]+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?[ \t]*$"""
)
REFERENCE_USE = re.compile(r"(!?)\[([^\]\n]*)\]\[([^\]\n]*)\]")


def _prose(source):
    """Remove fenced blocks and inline-code spans from the supported syntax."""
    lines = []
    fence = None
    for line in source.splitlines():
        match = FENCE.match(line)
        if fence:
            if (match and match[1][0] == fence[0]
                    and len(match[1]) >= len(fence) and not match[2].strip()):
                fence = None
            continue
        if match:
            fence = match[1]
            continue
        lines.append(line)
    return INLINE_CODE.sub("", "\n".join(lines))


def _label(value):
    return " ".join(value.split()).casefold()


def _destination(raw):
    if raw.startswith("<") and raw.endswith(">"):
        return raw[1:-1]
    return raw


def _broken_target(root, document, raw):
    try:
        destination = _destination(raw)
        parsed = urlsplit(destination)
        if parsed.scheme or parsed.netloc or not parsed.path:
            return None
        target = (document.parent / unquote(parsed.path)).resolve()
        if not target.is_relative_to(root) or not target.exists():
            return raw
    except (ValueError, OSError, UnicodeError):
        return raw
    return None


def broken_links(root, document):
    """Return invalid local inline/reference links and image paths.

    Supports simple inline destinations, angle-bracket destinations, explicit
    reference uses ([label][id], [id][]) and matching definitions. Shortcut
    references, nested/escaped parentheses and renderer-specific syntax are
    outside this deliberately bounded parser. External URLs and fragment-only
    links are ignored. No network requests are made.
    """
    root = Path(root).resolve()
    document = (root / document).resolve()
    if not document.is_relative_to(root):
        raise ValueError("document must be inside root")
    source = _prose(document.read_text(encoding="utf-8"))

    definitions = {}
    for match in REFERENCE_DEFINITION.finditer(source):
        definitions.setdefault(_label(match.group(1)), match.group(2))

    errors = []
    matches = []
    for match in INLINE_LINK.finditer(source):
        matches.append((match.start(), match.group(2)))
    for match in REFERENCE_USE.finditer(source):
        label, reference = match.group(2), match.group(3)
        key = _label(reference or label)
        raw = definitions.get(key)
        if raw is None:
            errors.append((match.start(), f"[{label}][{reference}]"))
        else:
            matches.append((match.start(), raw))

    for position, raw in matches:
        error = _broken_target(root, document, raw)
        if error is not None:
            errors.append((position, error))
    return [error for _, error in sorted(errors, key=lambda item: item[0])]
