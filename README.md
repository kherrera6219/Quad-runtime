# QUAD Runtime

QUAD Runtime is a YAML-driven reasoning middleware prototype. It turns the QUAD v2.2 instruction graph into a runnable Python system that can sit between an application, agent, or CLI and an LLM.

The goal is not to make a bigger prompt. The goal is to make reasoning behavior explicit, configurable, testable, and auditable.

## What It Does

QUAD Runtime takes a user query and decides how much reasoning structure is actually needed.

For simple requests, it uses normal single-voice answering. For complex requests, it activates QUAD mode, builds a compact prompt from the YAML source of truth, decides whether current-source grounding is needed, calls a model, checks the answer for known failure modes, scores the result, and saves an audit log.

```text
User query
-> Python runtime / router
-> Load QUAD YAML
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

## Why This Exists

Large prompts are hard to govern once they are copied across apps, agents, and workflows. QUAD Runtime keeps the reasoning policy in one YAML file and gives the application a small runtime that can enforce it.

This provides several practical benefits:

- **Config-driven behavior:** `config/quad_engine_v2_2.yaml` is the source of truth for activation policy, evidence policy, tool policy, role policy, output profiles, and failure modes.
- **Selective complexity:** QUAD does not run for every task. The router activates it only when multi-lens reasoning is likely to improve the answer.
- **Non-deceptive role use:** Professional roles are analytical lenses, not fake experts, agents, panels, or people.
- **Tool awareness:** The runtime can flag requests that need current sources, citations, or verification.
- **Quality checks:** The scorer looks for failure modes such as fake-panel language, mushy compromise, unsupported authority, stale current facts, over-formalization, and chain-of-thought leakage.
- **Auditability:** Each run can produce a tamper-evident JSON audit log with mode, activation reasons, profile, model, prompt hash, checks, score, decision, and answer.

## Core Concepts

### QUAD YAML

The YAML file defines the reasoning contract. It is not just prompt text. It describes:

- when QUAD should activate
- what evidence standards to prefer
- when tools or citations are required
- how professional lenses should be used
- what output profiles are available
- what failure modes must be avoided

Runtime code reads this file and turns those policies into model instructions, routing decisions, checks, and audit metadata.

### Router

`quad/router.py` decides whether a query should run in `normal` or `quad` mode.

The current MVP uses deterministic heuristics such as high-stakes terms, architecture/design language, tradeoff language, implementation intent, long draft size, and multiple-standard conflicts. This is intentionally simple and testable. A future version can add model-based classification.

### Prompt Builder

`quad/prompt_builder.py` builds different prompts depending on the route.

Normal mode gets a lightweight direct-answer instruction. QUAD mode gets a compact runtime prompt assembled from the YAML sections that matter for the selected profile.

### LLM Client

`quad/llm_client.py` provides a small adapter boundary.

Current clients:

- `echo`: deterministic local smoke-test client
- `ollama`: local Ollama `/api/generate` client

The same interface can be extended for OpenAI-compatible local endpoints, OpenAI, Claude, Gemini, DeepSeek, or application-owned model gateways.

### Tool Grounding

`quad/tool_grounding.py` decides whether a query likely needs current facts or cited sources.

The MVP detects terms such as `latest`, `current`, `price`, `law`, `regulation`, `API`, `version`, `benchmark`, `medical`, `legal`, `financial`, `security`, `citation`, `source`, and `verify`.

Today this creates a tool plan. A later integration can attach real search, retrieval, database, or documentation sources to the prompt.

### Failure Checks And Scoring

`quad/failure_checks.py` and `quad/scorer.py` turn QUAD into more than prompt formatting.

Each answer is checked for known failure modes. The scorer starts from 100 and applies penalties. The decision bands are:

- `85-100`: accept
- `70-84`: accept with caveats
- `50-69`: revise
- below `50`: reject

This creates a foundation for a future regeneration loop.

### Audit Logs

`quad/audit_logger.py` writes JSON audit records to `logs/audit_logs/`.

Each audit log includes:

- run ID and timestamp
- query
- mode
- activation reasons
- output profile
- tool requirement
- model
- prompt hash
- YAML version
- answer
- failure checks
- score
- decision
- audit hash

This lets an application explain why QUAD activated and how the answer passed or failed runtime checks.

## Quick Start

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Run the deterministic local smoke-test model:

```bash
.venv\Scripts\python.exe main.py --query "Design a framework for evaluating multi-agent reliability"
```

Run with Ollama:

```bash
.venv\Scripts\python.exe main.py --query "Design a framework for evaluating multi-agent reliability" --model ollama --ollama-model llama3.1
```

## CLI Usage

```bash
.venv\Scripts\python.exe main.py --query "..." --mode auto
.venv\Scripts\python.exe main.py --query "..." --mode normal
.venv\Scripts\python.exe main.py --query "..." --mode quad
.venv\Scripts\python.exe main.py --query "..." --profile deep
.venv\Scripts\python.exe main.py --query "..." --model ollama
.venv\Scripts\python.exe main.py --query "..." --no-audit
```

Example output:

```text
Mode: QUAD
Profile: deep
Model: echo
Tools required: false
Score: 100
Decision: accept
Audit log saved: C:\software\Quad-runtime\logs\audit_logs\quad_20260620_060742_b01309e6.json
```

## Python Integration

Applications can use the runtime directly:

```python
from quad.runtime import QuadRuntime

runtime = QuadRuntime()
result = runtime.run(
    query="Design a secure architecture for an agent workflow.",
    mode="auto",
    profile=None,
    audit=True,
)

print(result.answer)
print(result.mode)
print(result.score)
print(result.audit_path)
```

To use another model backend, implement the `LLMClient` protocol from `quad/llm_client.py`:

```python
from quad.models import GenerationResult


class MyModelClient:
    model_name = "my-model-gateway"

    def generate(self, system_prompt, user_prompt, metadata):
        answer = call_my_model_gateway(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            metadata=metadata,
        )
        return GenerationResult(answer=answer, model=self.model_name)
```

Then inject it:

```python
runtime = QuadRuntime(llm_client=MyModelClient())
result = runtime.run("Compare two implementation paths for this agent.")
```

## Application Integration Patterns

### Web Apps

A web application can call QUAD Runtime from an API route:

```text
Frontend chat input
-> Backend API route
-> QuadRuntime.run()
-> Store answer and audit_path
-> Return answer, score, mode, and decision to UI
```

Useful UI fields:

- answer
- mode: `normal` or `quad`
- output profile
- activation reasons
- tools required
- score
- decision
- audit log link

### Agent Systems

An agent can use QUAD Runtime as a reasoning gate before major actions:

```text
Agent receives task
-> QUAD routes and frames the reasoning
-> Tool grounding plan says whether retrieval is needed
-> Model produces answer or action plan
-> Failure checks score the output
-> Agent proceeds, revises, or asks for more evidence
```

This is most useful before actions with practical cost:

- code generation plans
- deployment decisions
- security or compliance judgments
- tool-use plans
- multi-agent coordination
- architecture choices
- research synthesis

### Retrieval-Augmented Generation

The current `ToolPlan` can be extended so retrieval runs before the final model call:

```text
Query
-> build_tool_plan()
-> retrieve docs/search/database records if required
-> attach_sources_to_prompt()
-> model call
-> citation-aware failure checks
```

This lets QUAD enforce the difference between stable reasoning tasks and tasks that need current or source-grounded evidence.

### Workflow Orchestrators

QUAD Runtime can be placed inside a larger workflow engine as a quality-control step:

```text
Draft answer
-> QUAD failure checks
-> score below threshold?
-> revise or regenerate
-> save audit trail
-> publish final output
```

This makes it useful as middleware for agent platforms, internal assistants, support workflows, research tools, or coding copilots.

## Repository Layout

```text
config/
  quad_engine_v2_2.yaml      # Source-of-truth QUAD policy
quad/
  audit_logger.py            # JSON audit logs with hashes
  cli.py                     # Command-line interface
  config_loader.py           # YAML loading and validation
  failure_checks.py          # Rule-based output checks
  llm_client.py              # Echo and Ollama model adapters
  models.py                  # Runtime dataclasses
  prompt_builder.py          # YAML-driven prompt assembly
  router.py                  # Normal vs QUAD routing
  runtime.py                 # End-to-end orchestration
  scorer.py                  # Score and decision bands
  tool_grounding.py          # Current-source detection
tests/                       # MVP unit tests
docs/ARCHITECTURE.md         # Architecture notes
logs/audit_logs/             # Local audit output
```

## Testing

Run:

```bash
.venv\Scripts\python.exe -m pytest --basetemp .pytest-tmp
```

The `--basetemp` option keeps pytest temp files inside the workspace, which is useful on locked-down Windows environments.

## Current Status

This repo is an MVP foundation. It proves the core path:

```text
Load QUAD YAML
-> route query
-> select profile
-> build prompt
-> call model adapter
-> run failure checks
-> score answer
-> save audit log
```

Next implementation steps:

1. Add real source retrieval behind `tool_grounding.py`.
2. Add revision and regeneration loops for low-scoring answers.
3. Add OpenAI-compatible endpoint support.
4. Store audit logs in SQLite for querying.
5. Add a local FastAPI or web UI for inspecting runs.
