# Phase 5 Integration Checkpoint

## Freeze Seal

The runtime and SDK are treated as feature-frozen for integration work. Phase 5
may consume product paths, but it may not invent product paths.

Preflight commands:

```bash
cd /workspace/latence-trace
python scripts/trace_feature_inventory.py --check
LATENCE_TRACE_SDK_REPO=/workspace/latence-trace-python python scripts/trace_core_contract_check.py

cd /workspace/latence-trace-python
LATENCE_TRACE_RUNTIME_REPO=/workspace/latence-trace python scripts/check_contract.py --json
```

Current freeze-seal result:

- Feature inventory: no route, RunPod action, manifest, SDK, or example drift.
- Runtime contract check: passed.
- SDK manifest contract check: passed.
- Package line: `latence==0.1.4`, `latence.__version__ == "0.1.4"`,
  user agent `latence/0.1.4`.

## Inheritance Strategy

All integrations inherit runtime and SDK changes through one route:

```text
TRACE runtime manifest
  -> latence SDK product methods
  -> shared integration helpers
  -> framework adapters and demos
```

Adapters must call the public SDK product namespaces:

- `client.grounding.rag(...)`
- `client.grounding.code(...)`
- `client.privacy.redact(...)`
- `client.compression.text(...)`
- `client.compression.messages(...)`
- `client.memory.step(...)`
- `client.rollup(...)`
- `client.session(...)`

Adapters must not implement scoring, thresholds, retries, redaction semantics,
memory rules, or policy decisions. Those stay in the runtime and SDK.

Shared adapter behavior lives in `latence.integrations._trace`:

- context normalization for common framework shapes
- RAG and code dispatch through product namespaces
- stable metadata extraction with future fields preserved in `raw`

## Demo Strategy

The checkpoint contains free, reproducible demos under `examples/phase5/`:

- Native SDK demo paths for RAG, coding, privacy, memory, and rollup.
- RAG comparison across native SDK, LangChain callback shape, and LlamaIndex
  postprocessor shape.
- LangGraph-style coding-agent routing into pass, review, or retry.
- n8n importable HTTP workflows for RAG, coding, privacy, memory, and rollup.
- LibreChat/OpenRouter proxy prototype with the OpenRouter key kept server-side.

## Acceptance Gate

Phase 5 is complete when:

- `python -m pytest` and `python -m ruff check .` pass in the SDK repo.
- `python scripts/prove_phase5_integrations.py` passes against a real TRACE
  endpoint.
- `python scripts/prove_phase5_integrations.py --require-frameworks` passes in
  an environment with the optional LangChain and LlamaIndex extras installed.
- n8n workflows import and execute against the same TRACE endpoint used by the
  native SDK demos.

Cursor, Claude Code, Codex, OpenCode, and other coding harnesses remain deferred
until this checkpoint proves the SDK/framework integration strategy.

