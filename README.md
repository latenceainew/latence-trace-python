# Latence Python SDK

Thin Python SDK for Latence TRACE.

```bash
pip install latence
```

```python
from latence import Latence

client = Latence(api_key="lat_...")

result = client.grounding.rag(
    query="When will this customer be refunded?",
    response_text="The customer will be refunded within 48 hours.",
    raw_context="Refunds are reviewed manually after finance approval.",
)

print(result.risk_band)
```

## Surface

The SDK maps 1:1 to the TRACE product API:

- `client.privacy.redact(...)`
- `client.grounding.rag(...)`
- `client.grounding.code(...)`
- `client.compression.text(...)`
- `client.compression.messages(...)`
- `client.memory.step(...)`
- `client.rollup(...)`
- `client.session(...)`

`Latence` is the sync client. `AsyncLatence` exposes the same product namespaces for asyncio apps.

## Sessions

TRACE deployments are stateless by default. The SDK owns caller-carried session state for agent workflows that need memory continuity, rollups, idempotency, and local persistence.

```python
from latence import FileSessionStorage, Latence

client = Latence(api_key="lat_...")
session = client.session(
    session_id="support-run-42",
    storage=FileSessionStorage(".trace-sessions"),
)

session.event("tool", "loaded refund policy")
session.memory_step(turn_text="Keep finance approval as required context.")
score = session.rag(
    query="Can I promise the refund?",
    response_text="Yes, the refund is guaranteed in 48 hours.",
    raw_context="Refunds require manual finance approval.",
)
session.save()
```

## Compatibility

The primary import is:

```python
from latence import Latence, AsyncLatence
```

For migration from the TRACE preview SDK, `LatenceTraceClient` and `AsyncLatenceTraceClient` remain aliases.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
python -m build
python -m twine check dist/*
```

Set `LATENCE_TRACE_RUNTIME_REPO=/path/to/latence-trace` when running contract tests from a non-sibling checkout.
