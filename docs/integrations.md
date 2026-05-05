# Integrations

The core SDK has only `httpx` and `pydantic` runtime dependencies. That is the
recommended integration path: call explicit product methods from your agent
framework and route on TRACE's decision.

```python
from latence import Latence

trace = Latence()
decision = trace.grounding.rag(
    query=user_question,
    response_text=agent_answer,
    raw_context=retrieved_context,
)
```

This direct shape works cleanly in LangGraph nodes, LangChain callbacks,
LlamaIndex postprocessors, n8n HTTP nodes, Cursor tools, Claude Code hooks,
Codex workflows, and custom pipelines.

## Integration Principle

Integrations are inheritance layers over the SDK, not separate products.

Every adapter must extract framework-native inputs, call one of the shared SDK
product paths, and attach TRACE metadata back to the framework object. Adapters
must not implement scoring, thresholds, retries, redaction semantics, memory
rules, or policy decisions.

Shared adapter behavior lives in `latence.integrations._trace` so framework
wrappers automatically inherit new runtime fields, SDK fixes, and response
metadata as the core product evolves.

## Optional Helpers

Optional adapter modules live under `latence.integrations`:

| Framework | Module | Install |
| --- | --- | --- |
| LangChain | `latence.integrations.langchain` | `pip install "latence[langchain]"` |
| LangGraph | `latence.integrations.langgraph` | `pip install "latence[langgraph]"` |
| LlamaIndex | `latence.integrations.llama_index` | `pip install "latence[llama_index]"` |
| OpenAI | `latence.integrations.openai` | `pip install "latence[openai]"` |
| Haystack | `latence.integrations.haystack` | `pip install "latence[haystack]"` |
| CrewAI | `latence.integrations.crewai` | `pip install "latence[crewai]"` |
| AutoGen | `latence.integrations.autogen` | `pip install "latence[autogen]"` |
| Pydantic AI | `latence.integrations.pydantic_ai` | `pip install "latence[pydantic_ai]"` |

Install everything only for integration development:

```bash
pip install "latence[all]"
```

## Integration Contract

Every adapter should do the same four things:

1. Extract the user query or task.
2. Extract the candidate model response.
3. Extract retrieved context, code context, or tool evidence.
4. Call `client.grounding.rag(...)` or `client.grounding.code(...)` through the shared integration helper.

Keep TRACE decisions explicit in your app state. That makes routing, logs,
reviews, retries, and replay tests straightforward.

## Phase 5 Demos

The free checkpoint demos live in `examples/phase5/`:

- LibreChat/OpenRouter proxy prototype.
- Native SDK, LangChain, and LlamaIndex RAG comparison.
- LangGraph coding-agent review/retry/pass route.
- Importable n8n HTTP-node workflows.

See [Phase 5 Integration Checkpoint](phase5_integration_checkpoint.md).
