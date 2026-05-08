"""Contract-first helpers shared by integration adapters.

Adapters should stay as thin as possible: extract framework-native
inputs, call these helpers, and attach the resulting metadata back to
the framework object. Scoring, retries, typed responses, and future
runtime fields remain owned by the SDK client.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Literal

from latence.integrations import _band_utils
from latence.models import AttributionMode, GroundednessResponse

TraceMode = Literal["rag", "code"]


def coerce_context(value: Any) -> list[str] | None:
    """Normalize common framework context shapes into text chunks."""

    if value is None:
        return None
    if isinstance(value, str):
        return [value] if value else None
    if isinstance(value, Mapping):
        for key in ("page_content", "content", "text"):
            item = value.get(key)
            if isinstance(item, str) and item:
                return [item]
        return None
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        chunks: list[str] = []
        for item in value:
            if isinstance(item, str) and item:
                chunks.append(item)
            elif isinstance(item, Mapping):
                for key in ("page_content", "content", "text"):
                    text = item.get(key)
                    if isinstance(text, str) and text:
                        chunks.append(text)
                        break
            elif hasattr(item, "page_content"):
                text = getattr(item, "page_content", None)
                if isinstance(text, str) and text:
                    chunks.append(text)
            elif hasattr(item, "get_content"):
                text = item.get_content()
                if isinstance(text, str) and text:
                    chunks.append(text)
        return chunks or None
    if hasattr(value, "page_content"):
        text = getattr(value, "page_content", None)
        return [text] if isinstance(text, str) and text else None
    return None


def score_rag(
    trace: Any,
    *,
    query: str | None,
    response_text: str,
    raw_context: Any,
    profile: str | None = "standard",
    attribution_mode: AttributionMode = AttributionMode.CLOSED_BOOK,
    context_trust_enabled: bool = True,
    extra: Mapping[str, Any] | None = None,
) -> GroundednessResponse:
    """Score a RAG response through the SDK product namespace."""

    return _score(
        trace,
        mode="rag",
        query=query,
        response_text=response_text,
        raw_context=raw_context,
        profile=profile,
        attribution_mode=attribution_mode,
        context_trust_enabled=context_trust_enabled,
        extra=extra,
    )


def score_code(
    trace: Any,
    *,
    query: str | None,
    response_text: str,
    raw_context: Any,
    profile: str | None = "standard",
    attribution_mode: AttributionMode = AttributionMode.CLOSED_BOOK,
    context_trust_enabled: bool = True,
    extra: Mapping[str, Any] | None = None,
) -> GroundednessResponse:
    """Removed in retrieval-only pivot."""
    raise NotImplementedError("Code scoring is not available.")


def score(
    trace: Any,
    *,
    mode: TraceMode,
    query: str | None,
    response_text: str,
    raw_context: Any,
    profile: str | None = "standard",
    attribution_mode: AttributionMode = AttributionMode.CLOSED_BOOK,
    context_trust_enabled: bool = True,
    extra: Mapping[str, Any] | None = None,
) -> GroundednessResponse:
    """Dispatch to the correct product path for a framework adapter."""

    if mode == "code":
        raise NotImplementedError("Code scoring removed.")
    return score_rag(
        trace,
        query=query,
        response_text=response_text,
        raw_context=raw_context,
        profile=profile,
        attribution_mode=attribution_mode,
        context_trust_enabled=context_trust_enabled,
        extra=extra,
    )


def trace_metadata(response: GroundednessResponse) -> dict[str, Any]:
    """Return stable adapter metadata while preserving raw future fields."""

    runtime_decision = getattr(response, "runtime_decision", None)
    scores = getattr(response, "scores", None)
    payload = {
        "risk_band": _band_utils.resolve_band(response),
        "trace_score": _band_utils.resolve_score(response),
        "groundedness_v2": getattr(scores, "groundedness_v2", None),
        "coverage_score_u": getattr(scores, "coverage_score_u", None),
        "context_coverage_ratio": getattr(scores, "context_coverage_ratio", None),
        "request_id": getattr(response, "request_id", None),
        "runtime_decision": (
            runtime_decision.model_dump(mode="json", exclude_none=True)
            if hasattr(runtime_decision, "model_dump")
            else runtime_decision
        ),
        "scores": (
            scores.model_dump(mode="json", exclude_none=True)
            if hasattr(scores, "model_dump")
            else None
        ),
        "context_trust_diagnostics": getattr(
            response,
            "context_trust_diagnostics",
            None,
        ),
        "raw": getattr(response, "raw", None),
    }
    return {key: value for key, value in payload.items() if value is not None}


def _score(
    trace: Any,
    *,
    mode: TraceMode,
    query: str | None,
    response_text: str,
    raw_context: Any,
    profile: str | None,
    attribution_mode: AttributionMode,
    context_trust_enabled: bool,
    extra: Mapping[str, Any] | None,
) -> GroundednessResponse:
    chunks = coerce_context(raw_context)
    merged_extra = dict(extra or {})
    if profile:
        merged_extra.setdefault("profile", profile)
    kwargs = {
        "query": query,
        "response_text": response_text,
        "raw_context": chunks,
        "attribution_mode": attribution_mode,
        "context_trust_enabled": context_trust_enabled,
        "extra": merged_extra or None,
    }
    if hasattr(trace, "grounding"):
        product = getattr(trace.grounding, mode)
        return product(**kwargs)
    product = getattr(trace, mode)
    return product(**kwargs)

