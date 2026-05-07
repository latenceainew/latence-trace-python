"""Shared helpers for framework integration adapters.

The wire has three slightly different flat response shapes:

1. Public REST ``/groundedness`` returns a pydantic
   ``GroundednessResponse`` with ``risk_band`` and
   ``scores.groundedness_v2`` — this is the canonical shape and
   matches the per-class calibration verdict.
2. RunPod handler ``_compact_response`` emits a top-level ``band``
   key and ``groundedness`` scalar — same calibration verdict, just
   flattened.
3. ``runtime_decision.band`` — the runtime decision band. As of
   ``latence-trace`` >= 0.5.x this is *coerced to match the
   calibration band* (red on calibration → red runtime decision),
   so it is safe to read as a fallback when neither of the above
   is available.

Resolution order intentionally prefers calibration-derived bands over
runtime-decision bands so the SDK matches the user-visible verdict
(event log row, heatmap header, SDK ``risk_band`` field) even when
running against older backends that have not yet applied the
red-coercion.
"""

from __future__ import annotations

from typing import Any


def _normalize(value: Any) -> str | None:
    if value is None:
        return None
    inner = getattr(value, "value", None)
    candidate = inner if inner else value
    text = str(candidate).strip().lower()
    if not text:
        return None
    return {"low": "green", "medium": "amber", "high": "red"}.get(text, text)


def resolve_band(response: Any) -> str:
    """Return the lowercase band for ``response`` from any shape.

    Source priority:

    1. ``risk_band`` (REST canonical / typed SDK).
    2. ``scores.risk_band`` (REST canonical, pre-validator).
    3. ``band`` (RunPod compact).
    4. ``runtime_decision.band`` (only when calibration is missing —
       safe because the backend coerces this to the calibration
       band when calibration is red).
    """

    candidates: list[Any] = [
        getattr(response, "risk_band", None),
    ]
    scores = getattr(response, "scores", None)
    if scores is not None:
        candidates.append(getattr(scores, "risk_band", None))
    candidates.append(getattr(response, "band", None))
    runtime_decision = getattr(response, "runtime_decision", None)
    if runtime_decision is not None:
        candidates.append(getattr(runtime_decision, "band", None))
    for candidate in candidates:
        normalized = _normalize(candidate)
        if normalized:
            return normalized
    return "unknown"


def resolve_score(response: Any) -> float:
    """Return the headline groundedness scalar from any shape.

    Source priority:

    1. Top-level ``trace_score`` (RunPod compact, calibration view).
    2. Top-level ``groundedness`` / ``score`` (RunPod compact, head
       channel mirror).
    3. ``scores.groundedness_v2`` then ``scores.groundedness_v1``
       (REST canonical).

    ``trace_score`` is the per-class calibration score (the same
    number that drives the user-visible band); preferring it keeps
    the headline score and band consistent for callers that only
    use one of the two helpers.
    """

    for name in ("trace_score", "groundedness", "score"):
        direct = getattr(response, name, None)
        if direct is not None:
            try:
                return float(direct)
            except (TypeError, ValueError):
                continue
    scores = getattr(response, "scores", None)
    for name in ("groundedness_v2", "groundedness_v1", "primary_score"):
        val = getattr(scores, name, None) if scores is not None else None
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return 0.0
