# Production Remediation Plan

This plan converts the production code review findings into concrete implementation work. The goal is to make QUAD Runtime safe to embed as a production Python module for applications, agents, and workflow engines.

## Review Summary

Current validation is healthy:

```text
ruff check .      passed
pytest            33 passed
python -m build   passed
```

The main production risks are not basic correctness failures. They are integration defaults and operational safety:

- audit logs default to a package-relative path that may not be writable after wheel install
- Gemini API keys are placed in the URL
- frontier model defaults can go stale or point at invalid provider slugs
- retry behavior does not handle transient HTTP failures
- audit payload redaction is opt-in while raw prompts and answers are persisted by default

## Sprint 1: Audit Storage Safety

Priority: P1

### Problem

The default audit path resolves relative to the package location. In an installed wheel, that can point inside `site-packages`, which is often read-only. Because audit is required by default, successful generations can fail during audit persistence.

### Implementation Tasks

- [ ] Add `audit_dir: str | Path | None` to `RuntimeRequest`.
- [ ] Route `RuntimeRequest.audit_dir` into `write_audit_log()`.
- [ ] Change the default audit location to a user/app-writable path.
  - Recommended default: platform cache/data directory or current working directory fallback.
  - Keep explicit `audit_dir` as the production-preferred path.
- [ ] Consider changing package default from `audit=True` to one of:
  - `audit=False` for library use
  - `audit=True, audit_required=False`
  - explicit audit store required for production mode
- [ ] Add tests for installed-package-like unwritable default paths.
- [ ] Update README and integration docs to require explicit audit configuration for production.

### Acceptance Criteria

- `QuadRuntime().run("...")` does not fail solely because the package install directory is read-only.
- Integrators can set audit output path per request.
- Audit failure behavior is documented and tested.

## Sprint 2: Credential-Safe Provider Requests

Priority: P1

### Problem

The Gemini client currently places the API key in the request URL. URLs are frequently logged by proxies, access logs, telemetry, exception reporters, and debugging tools.

### Implementation Tasks

- [ ] Prefer a header-based Gemini credential path if supported.
- [ ] If query-string auth remains necessary, ensure errors never include full credential-bearing URLs.
- [ ] Add a `_redact_url()` helper for provider diagnostics.
- [ ] Apply URL redaction in all provider error messages.
- [ ] Add tests proving API keys do not appear in raised `QuadModelError` messages.
- [ ] Review OpenAI and Anthropic error handling for accidental secret disclosure.

### Acceptance Criteria

- No provider exception includes API keys.
- Gemini tests prove the configured API key is not exposed in error strings.
- Docs note how credentials are loaded and how they are protected.

## Sprint 3: Provider Defaults And Model Selection

Priority: P2

### Problem

Hardcoded frontier defaults can become stale quickly. A package default that points to an unavailable or obsolete model creates avoidable first-run failures.

### Implementation Tasks

- [ ] Decide provider model policy:
  - Option A: require explicit model for frontier providers.
  - Option B: keep conservative documented defaults and update on release.
  - Option C: support named aliases controlled by package settings.
- [ ] Remove or reduce hardcoded claims such as "latest" from docs.
- [ ] Add provider health warnings when a model is defaulted rather than explicitly configured.
- [ ] Add tests for explicit model requirement or default warning behavior.
- [ ] Add `docs/MODEL_POLICY.md` documenting how model defaults are chosen.

### Acceptance Criteria

- New users get a clear error or warning when model selection is not explicit.
- Docs explain model freshness and provider-specific model IDs.
- Release checklist includes reviewing provider defaults.

## Sprint 4: Retry Semantics

Priority: P2

### Problem

`max_retries` does not currently retry HTTP failures. Rate limits and transient 5xx errors are common with frontier APIs.

### Implementation Tasks

- [ ] Retry only transient HTTP statuses:
  - 408
  - 409 if provider documents it as retryable
  - 429
  - 500
  - 502
  - 503
  - 504
- [ ] Do not retry deterministic client errors such as 400, 401, 403, and most 404s.
- [ ] Respect `Retry-After` when present.
- [ ] Add exponential backoff with jitter.
- [ ] Add `retry_count` to provider raw metadata or runtime metrics.
- [ ] Add mocked tests for retryable and non-retryable HTTP statuses.

### Acceptance Criteria

- `max_retries` behavior matches documentation.
- 429/5xx tests retry.
- 401/403 tests fail immediately.
- Errors include attempt count and redacted diagnostics.

## Sprint 5: Safe Audit Payload Defaults

Priority: P2

### Problem

Audit redaction exists, but it is opt-in. Raw queries and answers are persisted by default. Production users may accidentally log secrets, customer data, source excerpts, credentials, or proprietary code.

### Implementation Tasks

- [ ] Add `audit_payload_mode` to `RuntimeRequest`.
  - Suggested values: `metadata_only`, `redacted`, `full`.
- [ ] Default to `metadata_only` or `redacted` for package safety.
- [ ] Keep `full` available only when explicitly requested.
- [ ] Add structured redaction presets:
  - redact query
  - redact answer
  - redact prompt hash inputs
  - redact sources
  - redact metadata keys
- [ ] Add tests for every audit mode.
- [ ] Add `docs/AUDIT_LOGS.md` with schema, safety defaults, and examples.

### Acceptance Criteria

- Default audit logs do not persist full sensitive payloads unless explicitly configured.
- Integrators can opt into full logs intentionally.
- Audit schema docs explain retention and redaction behavior.

## Recommended Build Order

1. Audit storage safety.
2. Credential-safe provider requests.
3. Retry semantics.
4. Safe audit payload defaults.
5. Provider model policy.

This order reduces immediate production risk before adding larger features like `SourceProvider`, regeneration loops, or SQLite audit storage.

## Follow-Up Features After Remediation

After these review findings are resolved, continue with:

- `SourceProvider` protocol for host-owned retrieval
- CLI provider health command
- audit integrity verification command
- SQLite or pluggable audit store
- regeneration loop for low-scoring answers
- OpenAI-compatible custom endpoint client
