from __future__ import annotations

from typing import Any

from quad.models import ToolPlan

CURRENT_FACT_TERMS = {
    "latest",
    "current",
    "today",
    "yesterday",
    "recent",
    "price",
    "law",
    "regulation",
    "api",
    "version",
    "benchmark",
    "medical",
    "legal",
    "financial",
    "security",
    "safety",
    "citation",
    "source",
    "verify",
}


def needs_tools(query: str) -> bool:
    text = query.lower()
    return any(term in text for term in CURRENT_FACT_TERMS)


def build_tool_plan(query: str, config: dict[str, Any] | None = None) -> ToolPlan:
    text = query.lower()
    reasons = [term for term in sorted(CURRENT_FACT_TERMS) if term in text]
    return ToolPlan(required=bool(reasons), reasons=reasons)


def attach_sources_to_prompt(query: str, sources: list[dict[str, Any]]) -> str:
    if not sources:
        return query

    source_lines = ["\n\nSource material for grounding:"]
    for idx, source in enumerate(sources, start=1):
        title = source.get("title", f"Source {idx}")
        url = source.get("url", "")
        excerpt = source.get("excerpt", "")
        source_lines.append(f"[{idx}] {title} {url}\n{excerpt}".strip())
    return query + "\n".join(source_lines)
