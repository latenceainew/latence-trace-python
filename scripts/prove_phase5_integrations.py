"""Phase 5 integration proof against a real TRACE endpoint.

This script is intentionally endpoint-driven. It does not mock TRACE responses;
set LATENCE_TRACE_URL and LATENCE_TRACE_API_KEY before running it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from latence import Latence  # noqa: E402
from latence.integrations import _band_utils  # noqa: E402
from latence.integrations.langgraph import score_groundedness_node  # noqa: E402

QUESTION = "Can I promise this customer a refund within 48 hours?"
CONTEXT = "Refunds require manual finance approval before timelines are promised."
ANSWER = "Yes. The refund will arrive within 48 hours."
CODE_CONTEXT = "def fetch_with_retry(client, url, attempts=3):\n    ..."
CODE_ANSWER = "The patch retries transient timeouts up to three times."


class Check:
    def __init__(self) -> None:
        self.results: list[dict[str, Any]] = []

    def record(self, name: str, ok: bool, note: str = "", skipped: bool = False) -> None:
        self.results.append({"name": name, "ok": ok, "note": note, "skipped": skipped})
        status = "SKIP" if skipped else "PASS" if ok else "FAIL"
        print(f"[{status}] {name} :: {note}")

    def exit_code(self, *, require_frameworks: bool) -> int:
        failures = [
            item
            for item in self.results
            if not item["ok"] and (require_frameworks or not item["skipped"])
        ]
        return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-frameworks", action="store_true")
    parser.add_argument(
        "--json-output",
        type=Path,
        default=ROOT / "docs/phase5_integration_proof.json",
    )
    parser.add_argument(
        "--sdk-only",
        action="store_true",
        help="Skip raw HTTP/n8n checks; prove only SDK-backed native/framework paths.",
    )
    args = parser.parse_args(argv)

    checks = Check()
    trace = Latence(timeout=float(os.environ.get("LATENCE_TRACE_TIMEOUT", "600")))

    check_native(trace, checks)
    check_langgraph(trace, checks)
    check_langchain(trace, checks)
    check_llamaindex(trace, checks)
    if args.sdk_only:
        checks.record("n8n HTTP workflows", True, "skipped by --sdk-only", skipped=True)
    else:
        check_n8n_http(checks)

    payload = {
        "run_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": os.environ.get("LATENCE_TRACE_URL"),
        "checks": checks.results,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.json_output}")
    return checks.exit_code(require_frameworks=args.require_frameworks)


def check_native(trace: Latence, checks: Check) -> None:
    rag = trace.grounding.rag(query=QUESTION, response_text=ANSWER, raw_context=CONTEXT)
    code = trace.grounding.code(
        query="Does this patch add retry handling?",
        response_text=CODE_ANSWER,
        raw_context=CODE_CONTEXT,
    )
    redacted = trace.privacy.redact(
        text="Contact jane@example.com about account DE89370400440532013000.",
        include_original_text=False,
    )
    memory = trace.memory.step(
        turn_text="Keep manual refund approval as required context.",
        prior_memory_state=None,
    )
    rollup = trace.rollup(
        [
            {
                "risk_band": _band_utils.resolve_band(rag),
                "runtime_decision": (
                    rag.runtime_decision.model_dump(mode="json", exclude_none=True)
                    if rag.runtime_decision
                    else None
                ),
            }
        ]
    )
    checks.record("native SDK RAG", _band_utils.resolve_band(rag) != "unknown")
    checks.record("native SDK code", _band_utils.resolve_band(code) != "unknown")
    checks.record("native SDK privacy", bool(redacted.redacted_text))
    checks.record("native SDK memory", bool(memory.next_memory_state))
    checks.record("native SDK rollup", isinstance(rollup, dict))


def check_langgraph(trace: Latence, checks: Check) -> None:
    node = score_groundedness_node(trace, mode="code", profile="coding")
    state = node(
        {
            "question": "Does this patch add retry handling?",
            "answer": CODE_ANSWER,
            "raw_context": CODE_CONTEXT,
        }
    )
    checks.record(
        "LangGraph code node",
        state.get("trace_band") in {"green", "amber", "red", "unknown"},
        f"band={state.get('trace_band')}",
    )


def check_langchain(trace: Latence, checks: Check) -> None:
    try:
        from latence.integrations.langchain import LatenceTraceCallback
    except ImportError as exc:
        checks.record("LangChain RAG callback", False, str(exc), skipped=True)
        return
    callback = LatenceTraceCallback(client=trace)
    outputs = {"answer": ANSWER}
    run_id = "phase5-langchain"
    callback.on_chain_start({}, {"question": QUESTION, "context": CONTEXT}, run_id=run_id)
    callback.on_chain_end(outputs, run_id=run_id)
    metadata = outputs.get("metadata", {}).get("latence_trace", {})
    checks.record("LangChain RAG callback", bool(metadata), f"band={metadata.get('risk_band')}")


def check_llamaindex(trace: Latence, checks: Check) -> None:
    try:
        from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode

        from latence.integrations.llama_index import LatenceTracePostProcessor
    except ImportError as exc:
        checks.record("LlamaIndex postprocessor", False, str(exc), skipped=True)
        return
    nodes = [NodeWithScore(node=TextNode(text=CONTEXT), score=1.0)]
    processed = LatenceTracePostProcessor(trace)._postprocess_nodes(
        nodes,
        QueryBundle(query_str=QUESTION),
    )
    metadata = processed[0].node.metadata.get("latence_trace", {})
    checks.record("LlamaIndex postprocessor", bool(metadata), f"band={metadata.get('risk_band')}")


def check_n8n_http(checks: Check) -> None:
    base_url = os.environ.get("LATENCE_TRACE_URL")
    if not base_url:
        checks.record("n8n HTTP workflows", False, "LATENCE_TRACE_URL missing", skipped=True)
        return
    headers = {"content-type": "application/json"}
    if api_key := os.environ.get("LATENCE_TRACE_API_KEY"):
        headers["authorization"] = f"Bearer {api_key}"
    workflow_dir = ROOT / "examples/phase5/n8n"
    count = 0
    with httpx.Client(base_url=base_url.rstrip("/"), headers=headers, timeout=60.0) as http:
        for workflow_path in sorted(workflow_dir.glob("*.json")):
            workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
            for node in workflow.get("nodes", []):
                params = node.get("parameters", {})
                if node.get("type") != "n8n-nodes-base.httpRequest":
                    continue
                path = str(params.get("url", "")).split("}}", 1)[-1]
                body = json.loads(str(params.get("jsonBody", "{}")).lstrip("="))
                response = http.post(path, json=body)
                response.raise_for_status()
                count += 1
    checks.record("n8n HTTP workflows", count > 0, f"{count} HTTP nodes exercised")


if __name__ == "__main__":
    raise SystemExit(main())

