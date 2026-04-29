---
id: "20260429T120100"
title: "How Archive Works"
nav_title: "Archive Flow"
kind: "doc"
section: "examples"
slug: "archive-pipeline"
status: "published"
tags:
  - "archive"
  - "examples"
  - "workflow"
created: "2026-04-29"
updated: "2026-04-29"
summary: "A short end-to-end example of the canonical Archive pipeline with a built-in Mermaid diagram."
---

# How Archive Works

## Overview

Archive treats `sources/` as the editable source of truth, then rebuilds generated Markdown, navigation metadata, and the final VitePress site from that corpus.

## Details

Start with [Welcome to Archive](/notes/examples/welcome-to-archive), then compare this page with [Local Assets Example](/docs/examples/local-assets-example).

```mermaid
flowchart LR
  A[incoming] --> B[sources]
  B --> C[content]
  C --> D[VitePress]
  D --> E[site]
```

The public repo ships only this small `examples` corpus so the first build is useful without burying new users in demo content.

## References

- `README.md`
- `docs/authoring.md`
