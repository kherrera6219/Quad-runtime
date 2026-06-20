# QUAD Runtime Architecture

QUAD Runtime turns the QUAD v2.2 YAML instruction graph into executable reasoning middleware.

```text
User query
-> Runtime router
-> YAML config
-> Activation decision
-> Output profile selection
-> Tool-grounding decision
-> Prompt builder
-> LLM client
-> Failure checks
-> Score and decision
-> Audit log
-> Final answer
```

## MVP Scope

The current foundation provides:

- YAML loading and required-section validation.
- Runtime routing for `normal` versus `quad` mode.
- Output profile selection for `quick`, `standard`, and `deep`.
- Compact prompt construction from the YAML source of truth.
- Deterministic `echo` LLM client for local tests.
- Ollama adapter for local model calls.
- Current-fact tool-grounding detection.
- Rule-based failure checks.
- Score bands for accept, caveat, revise, and reject decisions.
- Tamper-evident JSON audit logs.

## Next Build Steps

1. Add source retrieval behind `tool_grounding.py`.
2. Add regeneration and revision loops for low-scoring answers.
3. Add OpenAI-compatible local endpoint support.
4. Store audit logs in SQLite for querying.
5. Add a FastAPI web UI for local runtime inspection.
