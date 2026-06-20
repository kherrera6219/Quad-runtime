# QUAD Runtime TODO

This file tracks the buildout from the current MVP into a production-grade reasoning middleware system.

## Current MVP Status

- [x] Store QUAD v2.2 YAML as the source-of-truth config.
- [x] Load and validate required YAML sections.
- [x] Route requests between `normal` and `quad` mode.
- [x] Select output profiles: `quick`, `standard`, and `deep`.
- [x] Build compact prompts from the YAML contract.
- [x] Provide deterministic `echo` model client for local smoke tests.
- [x] Provide basic Ollama client.
- [x] Detect when current-source/tool grounding may be required.
- [x] Run rule-based failure checks.
- [x] Score responses and return accept/revise/reject decisions.
- [x] Write tamper-evident JSON audit logs.
- [x] Add starter tests for config, routing, checks, scoring, and runtime.
- [x] Document architecture and integration paths.

## Next Sprint: Production Hardening

- [ ] Add structured runtime exceptions:
  - `QuadConfigError`
  - `QuadRoutingError`
  - `QuadPromptError`
  - `QuadModelError`
  - `QuadToolGroundingError`
  - `QuadAuditLogError`
- [ ] Replace broad `RuntimeError` usage in model clients with typed errors.
- [ ] Add timeout, retry, and clear connection diagnostics for Ollama calls.
- [ ] Validate CLI inputs before runtime execution.
- [ ] Add graceful CLI error output with nonzero exit codes.
- [ ] Add audit-log write failure handling so answer generation can fail closed or return a clear partial result.
- [ ] Add config schema validation beyond required-section presence.
- [ ] Add tests for malformed YAML, missing config, bad model client, and audit write failures.
- [ ] Add `ruff` or equivalent linting and formatting config.
- [ ] Add GitHub Actions steps for lint plus tests.

## Runtime Behavior Improvements

- [ ] Add model-based router classification as an optional layer after deterministic heuristics.
- [ ] Make activation thresholds configurable from YAML or runtime settings.
- [ ] Add output-profile override rules with validation.
- [ ] Add regeneration loop:
  - accept clean answers
  - accept with caveats for medium scores
  - revise low-scoring answers
  - reject and regenerate severe failures
- [ ] Add structured revision prompts based on failed checks.
- [ ] Track every generation attempt in the audit log.
- [ ] Add support for max attempts and loop termination reasons.

## Tool Grounding And Citations

- [ ] Create a `SourceProvider` interface.
- [ ] Add manual source injection for applications that already have retrieval.
- [ ] Add web/search provider later if needed.
- [ ] Add local documentation retrieval provider.
- [ ] Add source metadata normalization:
  - title
  - URL or record ID
  - timestamp
  - excerpt
  - source type
- [ ] Add citation checks when `tools_required` is true.
- [ ] Add tests for source attachment and citation enforcement.

## Model Provider Layer

- [ ] Add OpenAI-compatible local endpoint client.
- [ ] Add OpenAI client behind optional dependency/config.
- [ ] Add provider configuration through environment variables.
- [ ] Add request/response redaction controls for audit logs.
- [ ] Add token/latency metadata where providers expose it.
- [ ] Add provider health check command.
- [ ] Add integration tests using mocked provider responses.

## Audit And Observability

- [ ] Add JSONL audit option for append-only logs.
- [ ] Add SQLite audit store for querying runs.
- [ ] Add audit log version field.
- [ ] Add redaction policy for sensitive inputs.
- [ ] Add correlation IDs for application/agent integration.
- [ ] Add runtime metrics:
  - route mode
  - model latency
  - score
  - decision
  - tool requirement
  - retry count
- [ ] Add audit integrity verification command.

## Application And Agent Integration

- [ ] Add FastAPI service wrapper.
- [ ] Add `/run` endpoint for app integration.
- [ ] Add `/health` endpoint.
- [ ] Add `/audit/{run_id}` endpoint.
- [ ] Add typed request/response schemas.
- [ ] Add examples:
  - CLI usage
  - Python library usage
  - web API usage
  - agent pre-action reasoning gate
  - RAG/source-grounded answer flow
- [ ] Add a minimal local UI for inspecting runs.

## Documentation

- [ ] Add `docs/CONFIG.md` explaining the YAML sections.
- [ ] Add `docs/INTEGRATION.md` with concrete integration examples.
- [ ] Add `docs/PRODUCTION_HARDENING.md` for deployment standards.
- [ ] Add `docs/AUDIT_LOGS.md` with schema examples.
- [ ] Add troubleshooting notes for Windows, Ollama, and dependency installs.
- [ ] Add a changelog once the first commit is made.

## Suggested Build Order

1. Typed error handling and CLI error behavior.
2. Config schema validation.
3. Ollama timeout/retry hardening.
4. Audit logging failure handling and audit schema versioning.
5. Regeneration loop.
6. Source provider interface and manual source injection.
7. OpenAI-compatible endpoint client.
8. FastAPI wrapper.
9. SQLite audit store.
10. Local UI.

## Quality Bar

Before calling the system production-ready:

- all runtime branches have tests
- all external calls have timeouts
- all provider failures return typed errors
- audit logs are schema-versioned
- sensitive values can be redacted
- config is schema-validated
- CI runs lint and tests
- docs include integration examples and operational limits
