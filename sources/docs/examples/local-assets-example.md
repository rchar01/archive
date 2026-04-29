---
id: "20260429T120200"
title: "Local Assets Example"
nav_title: "Local Assets"
kind: "doc"
section: "examples"
status: "published"
tags:
  - "archive"
  - "assets"
  - "examples"
created: "2026-04-29"
updated: "2026-04-29"
summary: "Shows the sibling `.assets` folder pattern for page-local images without any path rewriting."
---

# Local Assets Example

## Overview

Canonical pages can keep local files in a sibling folder named after the source file stem.

## Details

This page lives beside `local-assets-example.assets/` and references its image with an ordinary relative Markdown path:

![Topology Example](./local-assets-example.assets/topology.svg)

The generated page keeps that relative path working because Archive copies the sibling asset directory beside the generated output. Compare this with [How Archive Works](/docs/examples/archive-pipeline) and the note [Welcome to Archive](/notes/examples/welcome-to-archive).

## References

- `scripts/tasks/build_content.py`
- `docs/authoring.md`
