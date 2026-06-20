# QUAD Runtime Handover

Last updated: 2026-06-19

## Project Goal

QUAD Runtime turns the QUAD v2.2 YAML reasoning contract into executable middleware for applications and agents.

The system should sit between a user/application/agent and an LLM. It decides whether a query needs normal answering or QUAD reasoning, builds the prompt from the YAML source of truth, determines whether tool grounding is required, calls a model, checks the answer, scores it, and writes an audit log.

## Current System Shape

```text
User query
-> QuadRuntime
-> config_loader
-> router
-> tool_grounding
-> prompt_builder
-> llm_client
-> failure_checks
-> scorer
-> audit_logger
-> RuntimeResult
```

## Current Files

- `config/quad_engine_v2_2.yaml`
  - Full QUAD v2.2 YAML source of truth.
- `quad/config_loader.py`
  - Loads YAML and validates required top-level sections.
- `quad/router.py`
  - Uses deterministic heuristics to route `normal` vs `quad`.
- `quad/tool_grounding.py`
  - Flags requests that may need current facts, sources, or citations.
- `quad/prompt_builder.py`
  - Builds normal or QUAD prompts from runtime decisions and YAML sections.
- `quad/llm_client.py`
  - Provides `echo` and Ollama clients behind a common interface.
- `quad/failure_checks.py`
  - Checks for fake panel language, mushy compromise, unsupported authority, stale current facts, visible chain-of-thought leakage, and over-formalization.
- `quad/scorer.py`
  - Converts check results into score and decision.
- `quad/audit_logger.py`
  - Writes JSON audit logs with prompt hash and audit hash.
- `quad/runtime.py`
  - Coordinates the end-to-end execution path.
- `quad/cli.py` and `main.py`
  - Provide command-line execution.
- `tests/`
  - Starter tests for config loading, routing, checks, scoring, and runtime.
- `README.md`
  - Explains the system and integration patterns.
- `docs/ARCHITECTURE.md`
  - Short architecture overview.
- `TODO.md`
  - Active backlog and next build order.

## Validation Performed

The current test suite passed:

```text
.venv\Scripts\python.exe -m pytest --basetemp .pytest-tmp
8 passed
```

The CLI smoke test passed with the deterministic `echo` model and wrote audit logs under:

```text
logs/audit_logs/
```

Known environment note: on this Windows environment, pytest may warn if it cannot write `.pytest_cache`. Use `--basetemp .pytest-tmp` to keep temporary test files inside the workspace.

## What Is Done

- MVP package structure exists.
- QUAD YAML is installed as config.
- Runtime routing exists.
- Prompt construction exists.
- Deterministic local model smoke test exists.
- Ollama adapter exists.
- Tool-grounding detection exists.
- Failure checks exist.
- Scoring exists.
- Audit logging exists.
- CLI exists.
- Starter tests exist.
- README and architecture docs exist.

## What Is Not Done Yet

- No production-grade typed error hierarchy yet.
- No retry/backoff behavior for model calls.
- No full YAML schema validation.
- No source retrieval provider.
- No real citation enforcement beyond basic checks.
- No regeneration loop.
- No OpenAI-compatible model client yet.
- No FastAPI service wrapper.
- No SQLite audit store.
- No UI.
- No lint/format tooling yet.
- No redaction policy for sensitive audit content.

## Recommended Next Step

Start with production-hardening before adding UI or more model providers.

The next implementation batch should be:

1. Add typed exceptions in a new `quad/errors.py`.
2. Update `llm_client.py`, `config_loader.py`, `audit_logger.py`, and `runtime.py` to use typed errors.
3. Add graceful CLI error handling in `quad/cli.py`.
4. Add tests for expected failure paths.
5. Add basic config schema validation for the YAML sections used at runtime.

This gives the system a stronger foundation before adding regeneration loops, web APIs, or external source retrieval.

## Production-Hardening Notes

Prioritize these engineering standards:

- External calls must have timeouts.
- External failures must produce clear typed errors.
- Runtime results should distinguish generated answers from partial failures.
- Audit writes should be explicit: either required and fail closed, or optional and return a warning.
- Config loading should fail early with actionable messages.
- CLI should return nonzero exit codes on runtime errors.
- Tests should cover both success and failure paths.
- Logs and audit records should avoid leaking secrets.
- Provider adapters should be replaceable without changing runtime orchestration.

## Integration Direction

For applications:

```text
App request
-> QuadRuntime.run()
-> return answer, mode, score, decision, audit_path
```

For agents:

```text
Agent plans action
-> QUAD evaluates reasoning and evidence requirements
-> score determines proceed, revise, or ask for more evidence
-> audit log records the decision path
```

For RAG:

```text
Query
-> tool plan
-> retrieve sources
-> attach sources to prompt
-> model answer
-> citation-aware checks
-> audit log
```

## Handover Warning

Do not treat QUAD as a prompt-only project. The value is the runtime boundary:

- policy in YAML
- deterministic routing
- provider abstraction
- tool-grounding decision
- quality checks
- score
- audit log

The next code should preserve that boundary instead of folding everything into one large prompt string.
