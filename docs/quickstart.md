# Quickstart

Install the SDK:

```bash
pip install latence
```

Configure the endpoint:

```bash
export LATENCE_TRACE_API_KEY="lat_..."
```

## 1. Score A RAG Answer

```python
from latence import Latence

trace = Latence()

score = trace.grounding.rag(
    query="Can this invoice be refunded?",
    response_text="Yes, it will be refunded within 48 hours.",
    raw_context="Refunds require manual finance approval before a timeline is promised.",
)

print(score.risk_band)
print(score.runtime_decision)
```


## 2. Redact Private Data

```python
redacted = trace.privacy.redact(
    text="Contact jane@example.com and charge IBAN DE89370400440532013000.",
)

print(redacted.redacted_text)
print(redacted.unique_labels)
```

## 3. Compress Context

```python
compressed = trace.compression.text(
    "Long retrieved context...",
    compression_rate=0.4,
)

print(compressed.compressed_text)
```

## 4. Async Services

```python
from latence import AsyncLatence

async with AsyncLatence() as trace:
    score = await trace.grounding.rag(
        query="What changed?",
        response_text="The policy now allows refunds.",
        raw_context="The policy still requires manual approval.",
    )
```
