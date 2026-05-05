# Phase 5 Integration Checkpoint

These demos are intentionally thin. Every path uses the public `latence` SDK
and a real TRACE endpoint; framework adapters do not implement scoring logic.

## Freeze Rule

Phase 5 integrations may consume product paths. They may not invent product
paths. New runtime fields flow through typed SDK models and `raw` payloads.

## Demos

- `librechat_openrouter_proxy.py` exposes an OpenAI-compatible proxy for a
  LibreChat-style demo. OpenRouter stays server-side; TRACE scores the
  assistant turn before the response is returned.
- `rag_native_langchain_llamaindex.py` runs the same RAG fixture through the
  native SDK, LangChain callback shape, and LlamaIndex postprocessor shape.
- `coding_langgraph.py` shows a coding-agent graph that routes `green`,
  `amber`, and `red` TRACE outcomes into pass, review, or retry.
- `n8n/*.json` contains importable HTTP-node workflows for RAG, coding, and
  privacy/compression/memory paths.

## Required Environment

```bash
export LATENCE_TRACE_URL="https://your-trace-endpoint.example.com"
export LATENCE_TRACE_API_KEY="lat_..."
```

For the LibreChat/OpenRouter proxy:

```bash
export OPENROUTER_API_KEY="sk-or-..."
export OPENROUTER_MODEL="meta-llama/llama-3.1-8b-instruct:free"
python -m pip install fastapi uvicorn httpx
uvicorn examples.phase5.librechat_openrouter_proxy:app --host 0.0.0.0 --port 8787
```

Point LibreChat at `http://localhost:8787/v1` as an OpenAI-compatible endpoint.

## Checkpoint Gate

Run the proof script against a real TRACE endpoint:

```bash
python scripts/prove_phase5_integrations.py
```

Optional framework extras can be installed as needed:

```bash
pip install "latence[langchain]" "latence[llama_index]" "latence[langgraph]"
```

