from __future__ import annotations

import re
from typing import Any

from scripts.core.content_links import normalize_content_link


def title_tokens(title: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", title.lower()) if len(token) > 2}


def section_score(current: str, candidate: str) -> int:
    if current == candidate:
        return 2
    current_parts = [part for part in current.split("/") if part]
    candidate_parts = [part for part in candidate.split("/") if part]
    shared_prefix = 0
    for current_part, candidate_part in zip(current_parts, candidate_parts):
        if current_part != candidate_part:
            break
        shared_prefix += 1
    return 1 if shared_prefix > 0 else 0


def score_candidate(
    page_link: str,
    page: dict[str, Any],
    candidate_link: str,
    candidate: dict[str, Any],
    linkgraph: dict[str, dict[str, list[str]]],
) -> int:
    page_tags = set(str(tag).strip().lower() for tag in page.get("tags", []) if str(tag).strip())
    candidate_tags = set(str(tag).strip().lower() for tag in candidate.get("tags", []) if str(tag).strip())
    shared_tags = len(page_tags & candidate_tags)

    page_outbound = set(linkgraph.get(page_link, {}).get("outbound", []))
    candidate_outbound = set(linkgraph.get(candidate_link, {}).get("outbound", []))
    shared_outbound = len(page_outbound & candidate_outbound)

    page_backlinks = set(linkgraph.get(page_link, {}).get("backlinks", []))
    candidate_backlinks = set(linkgraph.get(candidate_link, {}).get("backlinks", []))
    shared_backlinks = len(page_backlinks & candidate_backlinks)

    directly_linked = candidate_link in page_outbound or page_link in candidate_outbound
    if shared_tags == 0 and shared_outbound == 0 and shared_backlinks == 0 and not directly_linked:
        return 0

    score = shared_tags * 4

    if str(page.get("kind") or "") == str(candidate.get("kind") or ""):
        score += 2

    score += section_score(str(page.get("section") or ""), str(candidate.get("section") or ""))
    score += shared_outbound * 2
    score += shared_backlinks * 2

    if directly_linked:
        score += 3

    score += len(title_tokens(str(page.get("title") or "")) & title_tokens(str(candidate.get("title") or "")))
    return score


def build_related_index(
    pages_by_link: dict[str, dict[str, Any]],
    linkgraph: dict[str, dict[str, list[str]]],
    *,
    limit: int = 5,
) -> dict[str, dict[str, list[str]]]:
    related_index: dict[str, dict[str, list[str]]] = {}

    for link, page in sorted(pages_by_link.items()):
        manual_links = {
            normalize_content_link(str(target))
            for target in page.get("related_manual", [])
            if str(target).strip()
        }
        ranked: list[tuple[int, str, str]] = []
        for candidate_link, candidate in pages_by_link.items():
            if candidate_link == link or candidate_link in manual_links:
                continue
            score = score_candidate(link, page, candidate_link, candidate, linkgraph)
            if score <= 0:
                continue
            ranked.append((score, str(candidate.get("title") or "").lower(), candidate_link))

        ranked.sort(key=lambda value: (-value[0], value[1], value[2]))
        related_index[link] = {"related": [candidate_link for _, _, candidate_link in ranked[:limit]]}

    return related_index
