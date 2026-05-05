# Sessions

TRACE compute deployments are stateless. The Python SDK carries optional session state on the caller side so agent runs can preserve memory state, idempotency keys, events, and rollup inputs without requiring shared server storage.

```python
from latence import FileSessionStorage, Latence

client = Latence()
session = client.session(
    session_id="agent-run-1",
    storage=FileSessionStorage(".trace-sessions"),
)

session.event("tool", "loaded customer policy")
session.memory_step(turn_text="Keep the manual approval rule active.")
score = session.rag(
    query="Can we promise a refund?",
    response_text="The refund is guaranteed.",
    raw_context="Refunds require finance approval.",
)
session.save()
```

Use `InMemorySessionStorage` for tests and short-lived processes. Use `FileSessionStorage` for local agents and CLI workflows.
