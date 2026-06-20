# QUAD Runtime Integration Guide

QUAD Runtime is intended to be imported as a production-grade Python module. Host applications own their own API routes, workers, queues, databases, authentication, and UI. QUAD owns reasoning routing, provider calls, failure checks, scoring, and audit records.

## Basic Usage

```python
from quad import QuadRuntime, RuntimeRequest

runtime = QuadRuntime()
result = runtime.run(
    RuntimeRequest(
        query="Evaluate this agent architecture.",
        mode="auto",
        audit=True,
    )
)

print(result.answer)
print(result.mode)
print(result.score)
print(result.decision)
print(result.audit_path)
```

## Provider Setup

### OpenAI

```python
from quad import OpenAIResponsesClient, QuadRuntime

runtime = QuadRuntime(llm_client=OpenAIResponsesClient(model_name="gpt-5.1"))
```

Environment variables:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL`

### Claude

```python
from quad import AnthropicMessagesClient, QuadRuntime

runtime = QuadRuntime(llm_client=AnthropicMessagesClient(model_name="claude-fable-5"))
```

Environment variables:

- `ANTHROPIC_API_KEY`
- `ANTHROPIC_MODEL`
- `ANTHROPIC_BASE_URL`

### Gemini

```python
from quad import GeminiClient, QuadRuntime

runtime = QuadRuntime(llm_client=GeminiClient(model_name="gemini-3.5-pro"))
```

Environment variables:

- `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- `GEMINI_MODEL`
- `GEMINI_BASE_URL`

## Provider Health Checks

Use `check_provider()` before a host app accepts traffic:

```python
health = runtime.check_provider()

if not health.configured:
    raise RuntimeError(health.issues)
```

Health checks validate local configuration only. They do not send a live model request.

## Error Handling

Catch `QuadError` at the integration boundary:

```python
from quad import QuadError

try:
    result = runtime.run("Evaluate this decision.")
except QuadError as exc:
    log_failure(str(exc))
```

Provider failures raise `QuadModelError`. Audit write failures raise `QuadAuditLogError`.

## Audit Behavior

Audit logs are enabled by default and fail closed by default. If the host application wants generation to succeed when audit persistence fails:

```python
request = RuntimeRequest(
    query="Evaluate this decision.",
    audit=True,
    audit_required=False,
)
```

Every audit log includes:

- `audit_schema_version`
- run ID
- timestamp
- query
- routing decision
- model
- prompt hash
- failure checks
- score
- decision
- audit hash

## Redaction

Use explicit audit redactions for sensitive fields:

```python
request = RuntimeRequest(
    query="sensitive request",
    audit_redactions=["query", "answer"],
)
```

Redaction paths use dot notation for nested fields.

## Custom Model Client

```python
from quad import GenerationResult, ProviderHealth


class MyModelClient:
    model_name = "my-frontier-router"

    def validate_configuration(self):
        return ProviderHealth(provider="custom", model=self.model_name, configured=True)

    def generate(self, system_prompt, user_prompt, metadata):
        answer = call_my_gateway(system_prompt, user_prompt, metadata)
        return GenerationResult(answer=answer, model=self.model_name)
```

Then inject it:

```python
runtime = QuadRuntime(llm_client=MyModelClient())
```

## Current Best Integration Pattern

```text
Host app receives task
-> builds RuntimeRequest
-> checks provider configuration at startup
-> calls QuadRuntime.run()
-> handles QuadError
-> stores answer, score, decision, audit_path
-> uses audit log for traceability
```
