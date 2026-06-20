from __future__ import annotations

from typing import Any

from quad.models import PromptBundle, RouterDecision, ToolPlan
from quad.tool_grounding import attach_sources_to_prompt


def build_prompt(
    config: dict[str, Any],
    query: str,
    decision: RouterDecision,
    tool_plan: ToolPlan,
) -> PromptBundle:
    engine = config["quad_engine"]
    user_prompt = attach_sources_to_prompt(query, tool_plan.sources)

    if decision.mode == "normal":
        system_prompt = (
            "Answer directly in one assistant voice. Use concise rationale. "
            "Do not expose hidden chain-of-thought or visible QUAD process."
        )
        developer_prompt = "Use normal mode because QUAD was not materially useful for this query."
    else:
        system_prompt = _quad_system_prompt(engine, decision)
        developer_prompt = _quad_developer_prompt(engine, decision, tool_plan)

    metadata = {
        "mode": decision.mode,
        "activation_reasons": decision.activation_reasons,
        "output_profile": decision.output_profile,
        "tools_required": tool_plan.required,
        "yaml_version": engine.get("version"),
    }
    return PromptBundle(system_prompt=system_prompt, developer_prompt=developer_prompt, user_prompt=user_prompt, metadata=metadata)


def _quad_system_prompt(engine: dict[str, Any], decision: RouterDecision) -> str:
    identity = engine["core_identity"]
    failure_modes = ", ".join(engine["failure_modes"]["avoid"].keys())
    visible_sections = engine["output_profiles"][decision.output_profile]["visible_sections"]

    return "\n".join(
        [
            identity["instruction"].strip(),
            identity["non_deception_rule"].strip(),
            identity["role_grounding_rule"].strip(),
            identity["answer_rule"].strip(),
            identity["chain_of_thought_rule"].strip(),
            "Use QUAD internally only when it improves judgment.",
            "Visible output profile: " + decision.output_profile,
            "Useful visible sections: " + ", ".join(visible_sections),
            "Avoid these failure modes: " + failure_modes,
        ]
    )


def _quad_developer_prompt(engine: dict[str, Any], decision: RouterDecision, tool_plan: ToolPlan) -> str:
    evidence = engine["evidence_policy"]
    execution = engine["execution_summary"]["instruction"].strip()
    tool_instruction = (
        "Current-source grounding was required; use supplied sources and cite material claims."
        if tool_plan.required
        else "Current-source grounding was not required for this runtime pass."
    )

    return "\n".join(
        [
            "Activation reasons: " + ", ".join(decision.activation_reasons),
            "Prefer stronger evidence over weaker evidence.",
            evidence["uncertainty_rule"].strip(),
            evidence["anti_mush_rule"].strip(),
            tool_instruction,
            execution,
        ]
    )
