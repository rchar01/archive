from __future__ import annotations

import re

from scripts.core.paths import trim


SUMMARY_MAX_CHARS = 160


def plain_text_summary_line(line: str) -> str:
    line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
    line = re.sub(r"`([^`]*)`", r"\1", line)
    line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
    line = re.sub(r"__([^_]+)__", r"\1", line)
    line = re.sub(r"\*([^*]+)\*", r"\1", line)
    line = re.sub(r"_([^_]+)_", r"\1", line)
    line = re.sub(r"~~([^~]+)~~", r"\1", line)
    line = re.sub(r"^[\-*+]\s+", "", line)
    return trim(line)


def truncate_summary(text: str, limit: int = SUMMARY_MAX_CHARS) -> str:
    if len(text) <= limit:
        return text
    cutoff = text[: max(limit - 3, 1)].rstrip()
    word_boundary = cutoff.rfind(" ")
    if word_boundary > 0:
        cutoff = cutoff[:word_boundary].rstrip()
    return f"{cutoff}..."


def first_sentence(text: str) -> str:
    match = re.match(r"^(.+?[.!?])(?=\s|$)", text)
    return match.group(1) if match else ""


def summary_from_body(body: str) -> str:
    in_code = False
    paragraph_lines: list[str] = []

    def finish_paragraph() -> str:
        paragraph = trim(" ".join(paragraph_lines))
        if not paragraph:
            return ""
        sentence = first_sentence(paragraph)
        if sentence and len(sentence) <= SUMMARY_MAX_CHARS:
            return sentence
        return truncate_summary(paragraph)

    for line in body.splitlines():
        line = line.strip()
        if line.startswith("```"):
            if paragraph_lines:
                return finish_paragraph()
            in_code = not in_code
            continue
        if in_code or line.startswith("#") or line.startswith("<!--") or line.startswith(">"):
            if paragraph_lines:
                return finish_paragraph()
            continue
        if not line:
            if paragraph_lines:
                return finish_paragraph()
            continue
        plain_line = plain_text_summary_line(line)
        if plain_line:
            paragraph_lines.append(plain_line)
    return finish_paragraph()
