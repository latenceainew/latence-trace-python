<p align="center">
  <img src="https://raw.githubusercontent.com/latenceainew/latence-trace-python/main/docs/assets/latence-logo.svg" alt="Latence" width="180" />
</p>

<h1 align="center">Latence TRACE Python SDK</h1>

<p align="center">
  Stateless retrieval quality for knowledge agents. Groundedness verification,
  context compression, privacy redaction, and context utilization scoring
  — without replacing your stack.
</p>

<p align="center">
  <a href="https://pypi.org/project/latence/">PyPI</a>
  ·
  <a href="docs/quickstart.md">Quickstart</a>
  ·
  <a href="docs/integrations.md">Integrations</a>
  ·
  <a href="examples/">Examples</a>
  ·
  <a href="https://latence.ai">Website</a>
</p>

```bash
pip install latence
```

```python
from latence import Latence

trace = Latence(api_key="lat_...")

score = trace.grounding.rag(
    query="Can I promise this customer a refund?",
    response_text="Yes, the refund will arrive within 48 hours.",
    raw_context="Refunds require manual finance approval before timelines are promised.",
)

print(score.risk_band)
print(score.runtime_decision)
```

## Why This Exists

Knowledge agents are moving from demos into real workflows. That means private
data, unsupported answers, and wasted context are no longer abstract research
problems. They become support escalations, audit gaps, token waste, and user
trust issues.

TRACE is the retrieval quality layer that sits next to your RAG pipeline or
knowledge workflow. Your agent keeps running. TRACE checks the turn and returns
evidence plus a decision your application can route.

## What TRACE Does

TRACE is intentionally small at the SDK layer. The heavy work lives in your
TRACE runtime deployment; this package is the thin Python interface.

- **Groundedness** — verify RAG answers against retrieved context.
- **Compression** — reduce long context to what matters.
- **Privacy** — redact private data before it spreads through tools, logs, or prompts.
- **Context utilization** — score which retrieved chunks are actually used.

## Proof Points

These are runtime proof points from the TRACE freeze evidence, not SDK-only
microbenchmarks. See the linked artifacts for full context.

- Grounding: local managed-runtime 360 reported `1.00` AUROC for grounded vs.
  ungrounded RAG cases.
- Context utilization: held-out unused-context classification reported `1.00`
  precision and `1.00` recall.
- Latency: local concurrency burst reported about `368 ms` RAG p95 in the
  managed-runtime proof.
- Privacy: redaction returns labels, offsets, scores, redacted output, entity
  counts, and timings for logging-ready GDPR workflows.

Evidence:

- [SDK runtime freeze audit](https://github.com/latenceainew/latence-trace/blob/main/docs/core_freeze/sdk_runtime_freeze_audit.md)
- [Local 360 proof JSON](https://github.com/latenceainew/latence-trace/blob/main/docs/core_freeze/local_sdk_runtime_freeze_360.json)
- [Endpoint observability audit](https://github.com/latenceainew/latence-trace/blob/main/docs/core_freeze/endpoint_observability_360.md)

## How It Works

1. Deploy or access a TRACE runtime: RunPod, FastAPI, VPC, or on-prem.
2. Install `latence`.
3. Send the agent turn to the product path that matches the workflow.
4. Route on `risk_band`, `runtime_decision`, scores, spans, and evidence.
5. Store only the audit evidence your policy allows.

```python
from latence import Latence

trace = Latence(
    api_key="lat_...",
    base_url="https://your-trace-endpoint.example.com",
)
```

Environment variables are supported:

```bash
export LATENCE_TRACE_API_KEY="lat_..."
export LATENCE_TRACE_URL="https://your-trace-endpoint.example.com"
```

## The SDK Surface

The SDK mirrors the TRACE product API directly:

- RAG grounding: `client.grounding.rag(...)`
- Text compression: `client.compression.text(...)`
- Message compression: `client.compression.messages(...)`
- Privacy: `client.privacy.redact(...)`

`Latence` is synchronous. `AsyncLatence` exposes the same surface for asyncio
services.

```python
from latence import AsyncLatence, Latence
```

Base dependencies are only `httpx` and `pydantic`. Runtime and model packages
such as `torch`, `transformers`, `triton`, FastAPI, and vLLM are not SDK
dependencies.

## Start With The Path You Need

### RAG Agents

Use TRACE when your answer must be grounded in retrieved context.

```python
score = trace.grounding.rag(
    query="What is the refund policy?",
    response_text=agent_answer,
    raw_context=retrieved_context,
)

if score.risk_band.value != "green":
    send_to_review(score)
```

Example: [RAG grounding with guard checks](examples/rag_grounding_guard.py)

### Privacy

Use TRACE before customer data enters prompts, tools, traces, or logs.

```python
redacted = trace.privacy.redact(
    text="Email jane@example.com and charge IBAN DE89370400440532013000.",
)

print(redacted.redacted_text)
print(redacted.unique_labels)
```

Example: [Privacy redaction](examples/privacy_redact.py)

### Compression

Use TRACE when long-running workflows start dragging dead context forward.

```python
compressed = trace.compression.text(
    "Long retrieved context...",
    compression_rate=0.4,
)
```

Example: [Compression](examples/compression.py)

## For Whom

TRACE is for teams building or operating:

- RAG products where unsupported answers are expensive.
- Knowledge agents that touch customer records and policies.
- Legal, finance, healthcare, or regulated workflows that need evidence.
- Internal platforms where observability, retries, and human review matter.

It is also useful for framework authors and platform teams that need one
consistent protection API across LangGraph, LangChain, LlamaIndex, n8n, Cursor,
Claude Code, Codex, and custom agent runners.

## Integrations

Direct calls are the recommended path. Optional helpers live under
`latence.integrations`.

```bash
pip install "latence[langchain]"
pip install "latence[llama_index]"
pip install "latence[openai]"
pip install "latence[haystack]"
```

Docs: [Integrations](docs/integrations.md)  
Example: [Async batch](examples/async_batch.py)

Phase 5 demos: [LibreChat/OpenRouter, native SDK, LangChain, LlamaIndex,
LangGraph, and n8n](examples/phase5/)

## Async

```python
from latence import AsyncLatence

async with AsyncLatence() as trace:
    score = await trace.grounding.rag(
        query="What changed?",
        response_text="The policy now allows refunds.",
        raw_context="The policy still requires manual approval.",
    )
```

## Now What

If you are integrating TRACE into a knowledge agent:

1. Run the [quickstart](docs/quickstart.md).
2. Pick one product path: groundedness, compression, privacy, or context utilization.
3. Add one route in your app for `green`, `amber`, and `red`.
4. Log request ID, risk band, runtime decision, and redacted evidence.
5. Replay a few real failures and tune your thresholds.

If you are publishing or validating this SDK:

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python scripts/check_contract.py --manifest ../latence-trace/docs/core_freeze/api_surface_manifest.json
python -m build
python -m twine check dist/*
```

Clean-wheel smoke testing should run outside the repo root:

```bash
python -m venv /tmp/latence-sdk-smoke
/tmp/latence-sdk-smoke/bin/pip install dist/*.whl
cd /tmp && /tmp/latence-sdk-smoke/bin/python - <<'PY'
from importlib.metadata import distribution
from latence import Latence

requires = distribution("latence").requires or []
for forbidden in ("torch", "transformers", "triton", "fastapi", "vllm"):
    assert not any(req.lower().startswith(forbidden) for req in requires), requires

assert Latence(base_url="http://localhost:8090")
print("latence SDK smoke passed")
PY
```

## Migration

Primary imports:

```python
from latence import Latence, AsyncLatence
```

Preview aliases remain available so existing TRACE preview code can move first
and clean up names later:

```python
from latence import LatenceTraceClient, AsyncLatenceTraceClient
```

## More

- [Quickstart](docs/quickstart.md)
- [Integrations](docs/integrations.md)
- [Phase 5 Integration Checkpoint](docs/phase5_integration_checkpoint.md)
- [Errors](docs/errors.md)
- [Publishing](docs/publishing.md)
- [Examples](examples/)
- [TRACE runtime repo](https://github.com/latenceainew/latence-trace)
- [Website](https://latence.ai)
