# Integrations

The core SDK has only `httpx` and `pydantic` runtime dependencies.

Optional integration helpers live under `latence.integrations` and are activated through extras:

```bash
pip install "latence[langchain]"
pip install "latence[llama_index]"
pip install "latence[openai]"
```

The recommended baseline for frameworks such as LangChain, LangGraph, LlamaIndex, n8n, Cursor, Claude Code, and Codex is to call the explicit product methods directly:

```python
from latence import Latence

trace = Latence()
decision = trace.grounding.rag(
    query=user_question,
    response_text=agent_answer,
    raw_context=retrieved_context,
)
```

This keeps the integration thin and makes TRACE decisions easy to log, replay, and route.
