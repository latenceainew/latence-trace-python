# Sessions

TRACE compute deployments are stateless. Session state belongs to the caller so
the same deployment can serve RunPod, VPC, on-prem, and local agent workflows
without shared server storage.

The SDK session facade carries:

- `session_id`
- event history
- current memory state
- metadata
- idempotency keys
- optional local persistence

```python
from latence import FileSessionStorage, Latence

trace = Latence()
session = trace.session(
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

Use `InMemorySessionStorage` for tests and short-lived services. Use
`FileSessionStorage` for local agents, CLIs, Cursor workflows, and long-running
developer tools.

## Idempotency

`memory_step(...)` automatically creates and stores an idempotency key. You can
provide your own key when replaying events or coordinating retries:

```python
session.memory_step(
    turn_text="User asked for a refund commitment.",
    idempotency_key="run-42-turn-7-memory",
)
```

## Snapshots

```python
snapshot = session.snapshot()
print(snapshot.memory_state)
print(snapshot.idempotency_keys)
```

Snapshots are JSON-serializable Pydantic models, so you can persist them in your
own database instead of using the included file storage adapter.
