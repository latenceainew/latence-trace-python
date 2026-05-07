from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from latence.integrations import _trace
from latence.integrations.langgraph import score_groundedness_node
from latence.models import GroundednessResponse, GroundednessScores, RuntimeDecision


class _FakeGrounding:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def rag(self, **kwargs: Any) -> GroundednessResponse:
        self.calls.append(("rag", kwargs))
        return _response()

    def code(self, **kwargs: Any) -> GroundednessResponse:
        self.calls.append(("code", kwargs))
        return _response()


class _FakeTrace:
    def __init__(self) -> None:
        self.grounding = _FakeGrounding()


def _response() -> GroundednessResponse:
    return GroundednessResponse(
        risk_band="amber",
        scores=GroundednessScores(
            groundedness_v2=0.45,
            coverage_score_u=0.67,
            context_coverage_ratio=0.5,
        ),
        runtime_decision=RuntimeDecision(
            action="review",
            score=0.55,
            score_channel="groundedness",
            class_key="rag",
        ),
        request_id="req_phase5",
        raw={"future_runtime_field": {"kept": True}},
    )


def test_integration_helper_calls_rag_product_namespace() -> None:
    trace = _FakeTrace()

    response = _trace.score_rag(
        trace,
        query="Can we promise the refund?",
        response_text="Yes, within 48 hours.",
        raw_context=["Refunds require manual approval."],
        profile="quality",
        context_trust_enabled=False,
    )

    assert response.request_id == "req_phase5"
    assert trace.grounding.calls == [
        (
            "rag",
            {
                "query": "Can we promise the refund?",
                "response_text": "Yes, within 48 hours.",
                "raw_context": ["Refunds require manual approval."],
                "attribution_mode": "closed_book",
                "context_trust_enabled": False,
                "extra": {"profile": "quality"},
            },
        )
    ]


def test_integration_helper_metadata_preserves_future_fields() -> None:
    metadata = _trace.trace_metadata(_response())

    assert metadata["risk_band"] == "amber"
    assert metadata["trace_score"] == 0.45
    assert metadata["request_id"] == "req_phase5"
    assert metadata["runtime_decision"]["action"] == "review"
    assert metadata["raw"] == {"future_runtime_field": {"kept": True}}


def test_langgraph_node_can_route_to_code_product_namespace() -> None:
    trace = _FakeTrace()
    node = score_groundedness_node(trace, mode="code", profile="coding")

    state = node(
        {
            "question": "Does this patch add retries?",
            "answer": "It adds retries.",
            "raw_context": "def request_with_retry(): pass",
        }
    )

    assert state["trace_band"] == "amber"
    assert state["latence_trace"]["runtime_decision"]["action"] == "review"
    assert trace.grounding.calls[0][0] == "code"
    assert trace.grounding.calls[0][1]["extra"] == {"profile": "coding"}


def test_band_utils_prefers_calibration_risk_band_over_runtime_decision() -> None:
    from latence.integrations._band_utils import resolve_band, resolve_score

    response = GroundednessResponse(
        risk_band="red",
        scores=GroundednessScores(groundedness_v2=0.82, risk_band="red"),
        runtime_decision=RuntimeDecision(
            action="block",
            score=0.4,
            score_channel="head:claim_decomposer",
            class_key="rag.prose.multi_claim",
            band="red",
        ),
    )

    assert resolve_band(response) == "red"
    assert resolve_score(response) == 0.82


def test_band_utils_falls_back_to_runtime_decision_band_when_calibration_missing() -> None:
    from latence.integrations._band_utils import resolve_band

    class _Response:
        risk_band = None
        scores = None
        band = None

        class _RD:
            band = "amber"

        runtime_decision = _RD()

    assert resolve_band(_Response()) == "amber"


def test_phase5_n8n_workflows_target_product_paths() -> None:
    workflows_dir = Path(__file__).resolve().parents[1] / "examples/phase5/n8n"
    for workflow_path in workflows_dir.glob("*.json"):
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        urls = [
            node.get("parameters", {}).get("url", "")
            for node in workflow.get("nodes", [])
            if node.get("type") == "n8n-nodes-base.httpRequest"
        ]
        assert any(
            path in url
            for url in urls
            for path in (
                "/groundedness",
                "/v1/compliance/redact",
                "/v1/compression",
                "/v1/memory/update",
                "/groundedness/rollup",
            )
        ), workflow_path.name

