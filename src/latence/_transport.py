"""Shared retry / backoff / envelope-decoding helpers.

The sync and async clients differ only in how they perform the HTTP
call. The retry policy, backoff schedule, OTel propagation, and error
decoding live here so the two implementations stay byte-for-byte
identical in observable behaviour.
"""

from __future__ import annotations

import math
import os
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from latence.errors import (
    LatenceTraceAPIError,
    LatenceTraceAuthError,
    LatenceTraceRateLimited,
    LatenceTraceServerError,
    LatenceTraceValidationError,
    _Envelope,
)

DEFAULT_USER_AGENT = "latence/0.1.6"
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 4
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
RUNPOD_PRODUCT_ACTIONS = {
    "/groundedness": "score",
    "/v1/compliance/redact": "redact",
    "/v1/compression": "compress",
    "/v1/memory/update": "memory.update",
    "/groundedness/rollup": "rollup",
}


@dataclass(frozen=True)
class RetryPolicy:
    """Capped exponential backoff with full jitter.

    Sleep on attempt ``k`` is ``random.uniform(0, min(cap, base * 2**k))``
    seconds, plus the server-supplied ``Retry-After`` header when the
    response is a 429. ``base`` defaults to 0.25 s; ``cap`` to 8 s.
    """

    max_retries: int = DEFAULT_MAX_RETRIES
    base_seconds: float = 0.25
    cap_seconds: float = 8.0

    def sleep_for(self, attempt: int, retry_after_header: float | None) -> float:
        if retry_after_header is not None:
            return max(0.0, retry_after_header)
        backoff = min(self.cap_seconds, self.base_seconds * math.pow(2, attempt))
        return random.uniform(0.0, backoff)


def default_headers(api_key: str | None, extra: Mapping[str, str] | None = None) -> dict:
    """Compose request headers with bearer auth + UA + W3C trace context."""

    headers: dict = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": DEFAULT_USER_AGENT,
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    inject_trace_context(headers)
    if extra:
        headers.update(extra)
    return headers


def inject_trace_context(headers: dict) -> None:
    """Best-effort W3C traceparent injection.

    When the OTel SDK is configured the current span context is encoded
    into ``traceparent`` so the server log lines / spans correlate to
    the caller's trace. When the SDK is missing or no span is active
    this is a no-op and the SDK still works.
    """

    try:
        from opentelemetry import trace
        from opentelemetry.propagate import inject

        span = trace.get_current_span()
        ctx = span.get_span_context() if span else None
        if ctx and ctx.is_valid:
            inject(headers)
    except Exception:  # pragma: no cover - OTel optional
        pass


def parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def decode_error(status: int, body: Any, request_id: str | None) -> LatenceTraceAPIError:
    envelope = _envelope_from_body(body)
    if envelope and envelope.message:
        message = envelope.message
    elif status == 422 and isinstance(body, Mapping) and isinstance(body.get("detail"), list):
        # FastAPI validator errors — the detail is a list of error dicts.
        # Surface a useful message instead of the generic ``HTTP 422``.
        details = body["detail"]
        head = details[0] if details else None
        if isinstance(head, Mapping):
            loc = head.get("loc")
            msg = head.get("msg") or "validation error"
            location = ".".join(str(item) for item in loc) if isinstance(loc, list) else None
            message = (
                f"validation error at {location}: {msg}" if location else f"validation error: {msg}"
            )
        else:
            message = f"validation error: {details!r}"
    else:
        message = f"HTTP {status}"
    if status in (401, 402, 403):
        return LatenceTraceAuthError(
            message,
            status=status,
            envelope=envelope,
            request_id=request_id,
        )
    if status == 422:
        return LatenceTraceValidationError(
            message,
            status=status,
            envelope=envelope,
            request_id=request_id,
        )
    if status == 429:
        return LatenceTraceRateLimited(
            message,
            status=status,
            envelope=envelope,
            request_id=request_id,
        )
    if 500 <= status < 600:
        return LatenceTraceServerError(
            message,
            status=status,
            envelope=envelope,
            request_id=request_id,
        )
    return LatenceTraceAPIError(message, status=status, envelope=envelope, request_id=request_id)


_ERROR_ENVELOPE_RESERVED = frozenset(
    {"code", "message", "hint", "docs_url", "error_code", "error", "status_code"}
)


def _envelope_from_body(body: Any) -> _Envelope | None:
    """Coerce a server error body into a structured :class:`_Envelope`.

    Recognises three wire shapes:

    1. FastAPI ``{"detail": {"code": ..., "message": ..., "hint": ...}}``
       — the canonical REST error envelope.
    2. RunPod handler ``{"success": false, "error_code": ..., "error":
       ..., "hint": ..., "status_code": ..., "docs_url": ...}`` —
       emitted by ``runpod/handler.py::_service_error_payload`` when a
       job fails. The handler does not use ``code``/``message``;
       prior SDK versions would silently fall through to the
       ``HTTP {status}`` placeholder.
    3. FastAPI ``{"detail": "<plain string>"}`` — degraded path; we
       keep ``code=None`` and stuff the string into ``message`` so
       callers still get a useful description.
    """

    if not isinstance(body, Mapping):
        return None
    detail = body.get("detail")
    if isinstance(detail, Mapping):
        body = detail
    elif isinstance(detail, str) and detail:
        return _Envelope(code="error", message=detail, hint=None, docs_url=None, extra={})
    if not isinstance(body, Mapping):
        return None

    # Accept either ``code`` (REST) or ``error_code`` (RunPod handler).
    code_value = body.get("code")
    if not isinstance(code_value, str):
        code_value = body.get("error_code")
    # Accept either ``message`` (REST) or ``error`` (RunPod handler).
    message_value = body.get("message")
    if not isinstance(message_value, str) or not message_value:
        message_value = body.get("error")

    # Bail when neither code nor message is present — there is no
    # structured envelope to surface.
    if not isinstance(code_value, str) and not isinstance(message_value, str):
        return None

    return _Envelope(
        code=str(code_value) if isinstance(code_value, str) else "error",
        message=str(message_value) if isinstance(message_value, str) else "",
        hint=body.get("hint") if isinstance(body.get("hint"), str) else None,
        docs_url=body.get("docs_url") if isinstance(body.get("docs_url"), str) else None,
        extra={k: v for k, v in body.items() if k not in _ERROR_ENVELOPE_RESERVED},
    )


def coerce_base_url(base_url: str | None) -> str:
    base = base_url or os.environ.get("LATENCE_TRACE_URL", "http://localhost:8090")
    return base.rstrip("/")


def coerce_api_key(api_key: str | None) -> str | None:
    return api_key or os.environ.get("LATENCE_TRACE_API_KEY")


def is_runpod_endpoint(base_url: str) -> bool:
    """Return whether ``base_url`` points at a RunPod job endpoint.

    Callers still use TRACE product namespaces; this flag only changes the
    transport envelope inside the SDK.
    """

    parsed = urlparse(base_url)
    path = parsed.path.rstrip("/")
    deployment = os.environ.get("LATENCE_TRACE_DEPLOYMENT", "").strip().lower()
    return deployment == "runpod" or path.endswith(("/runsync", "/run"))


def runpod_request_body(
    method: str,
    path: str,
    payload: Mapping[str, Any] | None,
    headers: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Wrap a product-path request in RunPod's ``input`` envelope."""

    normalized_path = "/" + path.lstrip("/")
    body = dict(payload or {})
    if method.upper() == "GET" and normalized_path in {"/healthz", "/readyz"}:
        return {"input": {"health": True}}
    action = RUNPOD_PRODUCT_ACTIONS.get(normalized_path)
    if action is None:
        raise LatenceTraceAPIError(
            f"RunPod deployment does not expose SDK path {normalized_path}",
            status=0,
        )
    body["action"] = action
    if headers:
        idempotency_key = headers.get("Idempotency-Key") or headers.get("idempotency-key")
        if idempotency_key and "idempotency_key" not in body:
            body["idempotency_key"] = idempotency_key
    return {"input": body}


def unwrap_runpod_response(body: Any) -> tuple[Any, str | None]:
    """Extract the runtime payload from direct/local or hosted RunPod responses."""

    if not isinstance(body, Mapping):
        return body, None
    request_id = body.get("id") if isinstance(body.get("id"), str) else None
    output: Any = body
    if "status" in body and ("output" in body or "error" in body):
        status = str(body.get("status") or "").upper()
        if status not in {"COMPLETED", "COMPLETED_WITH_ERRORS"}:
            error = body.get("error") or body.get("output") or body
            raise LatenceTraceAPIError(f"RunPod job {status.lower()}: {error}", status=0)
        output = body.get("output")
    if isinstance(output, Mapping):
        if output.get("success") is False:
            message = output.get("error") or output.get("message") or "RunPod job failed"
            raise LatenceTraceAPIError(str(message), status=int(output.get("status_code") or 0))
        result = output.get("result")
        if isinstance(result, Mapping):
            return result, request_id
    return output, request_id


__all__: Sequence[str] = (
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_USER_AGENT",
    "RUNPOD_PRODUCT_ACTIONS",
    "RetryPolicy",
    "RETRYABLE_STATUS",
    "coerce_api_key",
    "coerce_base_url",
    "decode_error",
    "default_headers",
    "is_runpod_endpoint",
    "parse_retry_after",
    "runpod_request_body",
    "unwrap_runpod_response",
)
