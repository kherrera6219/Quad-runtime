from __future__ import annotations

from pathlib import Path

from quad.audit_logger import write_audit_log
from quad.config_loader import DEFAULT_CONFIG_PATH, return_config
from quad.failure_checks import run_failure_checks
from quad.llm_client import LLMClient, client_from_name
from quad.models import Mode, OutputProfile, RuntimeResult
from quad.prompt_builder import build_prompt
from quad.router import route_query
from quad.scorer import score_answer
from quad.tool_grounding import build_tool_plan


class QuadRuntime:
    def __init__(
        self,
        config_path: str | Path = DEFAULT_CONFIG_PATH,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.config = return_config(config_path)
        self.llm_client = llm_client or client_from_name("echo")

    def run(
        self,
        query: str,
        mode: Mode = "auto",
        profile: OutputProfile | None = None,
        audit: bool = True,
    ) -> RuntimeResult:
        decision = route_query(query=query, mode=mode, profile=profile, explicit_quad_request="quad" in query.lower())
        tool_plan = build_tool_plan(query, self.config)
        prompt = build_prompt(self.config, query, decision, tool_plan)

        metadata = dict(prompt.metadata)
        metadata["developer_prompt"] = prompt.developer_prompt
        generation = self.llm_client.generate(prompt.system_prompt, prompt.user_prompt, metadata)

        checks = run_failure_checks(generation.answer, tool_required=tool_plan.required)
        score = score_answer(checks)

        audit_path = None
        if audit:
            audit_path = str(write_audit_log(query, decision, tool_plan, prompt, generation, score))

        return RuntimeResult(
            answer=generation.answer,
            mode=decision.mode,
            activation_reasons=decision.activation_reasons,
            output_profile=decision.output_profile,
            tools_required=tool_plan.required,
            score=score.score,
            decision=score.decision,
            audit_path=audit_path,
            model=generation.model,
        )
