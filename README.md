<p align="center">
  <img src="https://raw.githubusercontent.com/latenceainew/latence-trace-python/main/docs/assets/latence-logo.svg" alt="Latence" width="180" />
</p>

<h1 align="center">Latence TRACE Python SDK</h1>

<p align="center">
  Real-time safety for knowledge agents. Groundedness verification,
  privacy redaction, and context compression — without replacing your stack.
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

## What TRACE Does

- **Groundedness** — verify RAG answers against retrieved context.
- **Compression** — reduce long context to what matters.
- **Privacy** — redact private data before it spreads through tools, logs, or prompts.

## Getting Started

```bash
export LATENCE_TRACE_API_KEY="lat_..."
```

```python
from latence import Latence

trace = Latence()
```

The SDK connects to `https://api.latence.ai` by default. Override with `base_url` or `LATENCE_TRACE_URL`.

## API Surface

```python
# Groundedness scoring
score = trace.grounding.rag(query=..., response_text=..., raw_context=...)

# Privacy redaction
redacted = trace.privacy.redact(text=...)

# Context compression
compressed = trace.compression.text(text=..., compression_rate=0.4)
```

`Latence` is synchronous. `AsyncLatence` exposes the same surface for asyncio services.

Base dependencies are only `httpx` and `pydantic`.

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

## More

- [Quickstart](docs/quickstart.md)
- [Integrations](docs/integrations.md)
- [Errors](docs/errors.md)
- [Publishing](docs/publishing.md)
- [Examples](examples/)
- [Website](https://latence.ai)
