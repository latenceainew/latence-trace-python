"""LangGraph-style coding-agent checkpoint demo.

The graph shape is deliberately tiny: generate a candidate answer, score it
with TRACE's code-grounding lane, then route to pass, review, or retry.
"""

from __future__ import annotations

from typing import Any

from latence import Latence
from latence.integrations.langgraph import score_groundedness_node

TASK = "Does this patch add retry handling for transient HTTP failures?"
CODE_CONTEXT = """
def fetch_with_retry(client, url, attempts=3):
    for attempt in range(attempts):
        try:
            return client.get(url)
        except TimeoutError:
            if attempt == attempts - 1:
                raise
"""
AGENT_ANSWER = "Yes. The patch retries transient timeouts up to three times."


def generate(_: dict[str, Any]) -> dict[str, Any]:
    return {
        "question": TASK,
        "answer": AGENT_ANSWER,
        "raw_context": CODE_CONTEXT,
    }


def route(state: dict[str, Any]) -> str:
    return {
        "green": "pass",
        "amber": "review",
        "red": "retry",
    }.get(str(state.get("trace_band")), "review")


def main() -> None:
    trace = Latence()
    score_node = score_groundedness_node(trace, mode="code", profile="coding")
    state = score_node(generate({}))
    print(
        {
            "route": route(state),
            "trace_band": state["trace_band"],
            "trace_score": state["trace_score"],
            "latence_trace": state["latence_trace"],
        }
    )


if __name__ == "__main__":
    main()

