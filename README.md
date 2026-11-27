# takin-docs-tools

A small local relative Markdown inline-link checker. Checks existence and root containment, not external URL availability, fragments or full Markdown syntax.

## Optional fragment checks

`anchors.missing_fragments(root, document)` checks ordinary local Markdown fragments against plain ATX headings (including duplicate suffixes) and explicit HTML id/name anchors. It ignores fenced code, simple inline-code examples, external URLs and non-Markdown targets. Use together with `doclinks.broken_links` for path checks. It is not a complete Markdown parser; complex inline heading markup, reference links and renderer-specific slugs need separate review. All files and results stay in the caller's checkout.

## Run locally

```sh
python3 -m unittest discover -v
```

Uses standard-library dependencies only. CI runs this repository's own code and synthetic tests on two standard Linux runner images in parallel. Failed jobs remain visible; no private checkout, cross-repository tokens, deployment, production data or private test artifacts are used.

## Integration boundary

This is an independently useful public utility, not a mirror or remote runner for a private application. Consumers should pin a reviewed version and run their own integration checks. A green public CI run certifies only this utility at its tested commit, not any consuming application.

## Status

Initial implementation; not a stable release. Licensing terms are pending owner selection; public visibility alone is not a license to redistribute or modify.
