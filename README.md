# takin-docs-tools

Local Markdown link, image and fragment diagnostics. All checks run against files in the caller's checkout; the tool makes no network requests.

## Path/link checks

`doclinks.broken_links(root, document)` checks simple relative inline links, angle-bracket destinations, explicit reference links (`[label][id]` and `[id][]`) and local image targets. It detects missing paths, root escapes and unresolved reference labels. External URLs and fragment-only links are intentionally ignored. It is a bounded parser, not a complete CommonMark implementation: shortcut references, nested/escaped parentheses, complex multiline syntax and renderer-specific edge cases require a full Markdown parser.

## Optional fragment checks

`anchors.missing_fragments(root, document)` checks ordinary local Markdown fragments against plain ATX headings (including duplicate suffixes) and explicit HTML id/name anchors. It ignores fenced code, simple inline-code examples, external URLs and non-Markdown targets. Use together with `doclinks.broken_links` for path checks. Complex inline heading markup and renderer-specific slugs need separate review.

## Run locally

```sh
python3 -m unittest discover -v
```

Uses standard-library dependencies only. CI runs this repository's own code and synthetic tests on two standard Linux runner images in parallel. Failed jobs remain visible; no private checkout, cross-repository tokens, deployment, production data or private test artifacts are used.

## Integration boundary

This is an independently useful public utility, not a mirror or remote runner for a private application. Consumers should pin a reviewed version and run their own integration checks. A green public CI run certifies only this utility at its tested commit, not any consuming application.

## Status

Initial implementation; not a stable release. Licensing terms are pending owner selection; public visibility alone is not a license to redistribute or modify.
