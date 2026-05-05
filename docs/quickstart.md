# Quickstart

Install:

```bash
pip install latence
```

Score a RAG response:

```python
from latence import Latence

client = Latence(api_key="lat_...")
score = client.grounding.rag(
    query="Can this invoice be refunded?",
    response_text="Yes, it will be refunded within 48 hours.",
    raw_context="Refunds require manual finance approval.",
)
print(score.risk_band)
```

Use `AsyncLatence` for asyncio services. The async surface mirrors the sync client.
