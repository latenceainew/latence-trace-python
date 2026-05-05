"""Apples-to-apples RAG demo for native SDK, LangChain, and LlamaIndex.

All three paths use the same fixture and the same TRACE endpoint. Optional
framework imports are skipped when the extra is not installed, but the native
SDK path always runs.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from latence import Latence

QUESTION = "Can I promise this customer a refund within 48 hours?"
CONTEXT = [
    "Refunds require manual finance approval before any timeline is promised.",
    "Support agents may say that the case has been escalated for review.",
]
ANSWER = "Yes. The refund will arrive within 48 hours."


def main() -> None:
    trace = Latence()
    print("native:", _native(trace))
    print("langchain:", _langchain(trace))
    print("llamaindex:", _llamaindex(trace))


def _native(trace: Latence) -> dict[str, Any]:
    score = trace.grounding.rag(
        query=QUESTION,
        response_text=ANSWER,
        raw_context=CONTEXT,
    )
    return score.model_dump(mode="json", exclude_none=True)


def _langchain(trace: Latence) -> dict[str, Any] | str:
    try:
        from latence.integrations.langchain import LatenceTraceCallback
    except ImportError as exc:
        return f"skipped: {exc}"

    callback = LatenceTraceCallback(client=trace)
    run_id = uuid4()
    outputs = {"answer": ANSWER}
    callback.on_chain_start(
        {},
        {"question": QUESTION, "context": CONTEXT},
        run_id=run_id,
    )
    callback.on_chain_end(outputs, run_id=run_id)
    return outputs.get("metadata", {}).get("latence_trace", {})


def _llamaindex(trace: Latence) -> dict[str, Any] | str:
    try:
        from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode

        from latence.integrations.llama_index import LatenceTracePostProcessor
    except ImportError as exc:
        return f"skipped: {exc}"

    nodes = [
        NodeWithScore(node=TextNode(text=context), score=1.0)
        for context in CONTEXT
    ]
    processor = LatenceTracePostProcessor(trace)
    processed = processor._postprocess_nodes(nodes, QueryBundle(query_str=QUESTION))
    metadata = getattr(processed[0].node, "metadata", {}) if processed else {}
    return metadata.get("latence_trace", {})


if __name__ == "__main__":
    main()

