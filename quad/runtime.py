from __future__ import annotations

from pathlib import Path
from typing import overload

from quad.audit_logger import write_audit_log
from quad.config_loader import DEFAULT_CONFIG_PATH, return_config
from quad.errors import QuadAuditLogError, QuadRoutingError
from quad.failure_checks import run_failure_checks
from quad.llm_client import LLMClient, client_from_name
from quad.models import Mode, OutputProfile, RuntimeRequest, RuntimeResult
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

    @overload
    def run(
        self,
        query: str,
        mode: Mode = "auto",
        profile: OutputProfile | None = None,
        audit: bool = True,
    ) -> RuntimeResult:
        ...

    @overload
    def run(self, query: RuntimeRequest) -> RuntimeResult:
        ...

    def run(
        self,
        query: str | RuntimeRequest,
        mode: Mode = "auto",
        profile: OutputProfile | None = None,
        audit: bool = True,
    ) -> RuntimeResult:
        request = self._coerce_request(query, mode=mode, profile=profile, audit=audit)

        decision = route_query(
            query=request.query,
            mode=request.mode,
            profile=request.profile,
            explicit_quad_request="quad" in request.query.lower(),
        )
        if request.sources:
            tool_plan = build_tool_plan(request.query, self.config)
            tool_plan = type(tool_plan)(required=tool_plan.required, reasons=tool_plan.reasons, sources=request.sources)
        else:
            tool_plan = build_tool_plan(request.query, self.config)
        prompt = build_prompt(self.config, request.query, decision, tool_plan)

        metadata = dict(request.metadata)
        metadata.update(prompt.metadata)
        metadata["developer_prompt"] = prompt.developer_prompt
        generation = self.llm_client.generate(prompt.system_prompt, prompt.user_prompt, metadata)

        checks = run_failure_checks(generation.answer, tool_required=tool_plan.required)
        score = score_answer(checks)

        audit_path = None
        warnings: list[str] = []
        if request.audit:
            try:
                audit_path = str(write_audit_log(request.query, decision, tool_plan, prompt, generation, score))
            except QuadAuditLogError as exc:
                if request.audit_required:
                    raise
                warnings.append(str(exc))

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
            warnings=warnings,
        )

    def _coerce_request(
        self,
        query: str | RuntimeRequest,
        mode: Mode,
        profile: OutputProfile | None,
        audit: bool,
    ) -> RuntimeRequest:
        if isinstance(query, RuntimeRequest):
            self._validate_request(query)
            return query
        request = RuntimeRequest(query=query, mode=mode, profile=profile, audit=audit)
        self._validate_request(request)
        return request

    def _validate_request(self, request: RuntimeRequest) -> None:
        if not isinstance(request.query, str) or not request.query.strip():
            raise QuadRoutingError("RuntimeRequest.query must be a non-empty string.")
