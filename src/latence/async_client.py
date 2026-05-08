"""Asyncio version of :class:`latence.client.Latence`.

Behavioural parity with the sync client; share the same retry policy,
error decoding, and pydantic models.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from latence._transport import (
    DEFAULT_TIMEOUT_SECONDS,
    RETRYABLE_STATUS,
    RetryPolicy,
    coerce_api_key,
    coerce_base_url,
    decode_error,
    default_headers,
    is_runpod_endpoint,
    parse_retry_after,
    runpod_request_body,
    unwrap_runpod_response,
)
from latence.client import _build_groundedness_payload, _normalize_rollup_body
from latence.errors import (
    LatenceTraceAPIError,
    LatenceTraceRateLimited,
    LatenceTraceServerError,
    LatenceTraceTimeout,
    LatenceTraceValidationError,
)
from latence.models import (
    AttributionMode,
    ComplianceCustomLabel,
    ComplianceLabelMode,
    ComplianceRedactionMode,
    ComplianceRedactionRequest,
    ComplianceRedactionResponse,
    CompressionResponse,
    GroundednessResponse,
    MemoryUpdateResponse,
    RollupResponse,
    SupportUnit,
)
from latence.sessions import (
    SessionStorage,
    TraceEvent,
    TraceSessionSnapshot,
    new_idempotency_key,
    normalize_events,
)

PremiseSupportUnits = Sequence[SupportUnit | Mapping[str, Any]]
RawContextInput = str | Sequence[str]
ComplianceCustomLabels = Sequence[ComplianceCustomLabel | Mapping[str, Any]]


def _coerce_raw_context(raw_context: RawContextInput | None) -> str | None:
    if raw_context is None:
        return None
    if isinstance(raw_context, str):
        return raw_context
    return "\n\n".join(str(item) for item in raw_context)


class AsyncPrivacyClient:
    def __init__(self, owner: AsyncLatence) -> None:
        self._owner = owner

    async def redact(self, **kwargs: Any) -> ComplianceRedactionResponse:
        return await self._owner.redact_compliance(**kwargs)


class AsyncGroundingClient:
    def __init__(self, owner: AsyncLatence) -> None:
        self._owner = owner

    async def rag(
        self,
        *,
        context_trust_enabled: bool = False,
        **kwargs: Any,
    ) -> GroundednessResponse:
        extra = dict(kwargs.pop("extra", {}) or {})
        extra.setdefault("scoring_mode", "rag")
        return await self._owner.score_groundedness(
            extra=extra,
            context_trust_enabled=context_trust_enabled,
            **kwargs,
        )

    async def code(self, **kwargs: Any) -> GroundednessResponse:
        raise NotImplementedError("Code scoring has been removed. Use .rag() instead.")


class AsyncCompressionClient:
    def __init__(self, owner: AsyncLatence) -> None:
        self._owner = owner

    async def text(self, text: str, **options: Any) -> CompressionResponse:
        return await self._owner._request(
            "POST",
            "/v1/compress",
            json={"text": text, **options},
            expected_model=CompressionResponse,
        )

    async def messages(
        self,
        messages: Sequence[Mapping[str, Any]],
        **options: Any,
    ) -> CompressionResponse:
        return await self._owner._request(
            "POST",
            "/v1/compress",
            json={"action": "compress_messages", "messages": list(messages), **options},
            expected_model=CompressionResponse,
        )


class AsyncMemoryClient:
    def __init__(self, owner: AsyncLatence) -> None:
        self._owner = owner

    async def step(self, **kwargs: Any) -> MemoryUpdateResponse:
        raise NotImplementedError("Memory API has been removed.")


class AsyncTraceSession:
    """Async SDK-managed state facade for stateless TRACE deployments."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("Sessions have been removed. Use stateless grounding.rag() calls.")

    def event(self, event_type: str, content: str, **metadata: Any) -> Mapping[str, Any]:
        key = str(metadata.pop("idempotency_key", "") or new_idempotency_key("event"))
        event = TraceEvent(
            event_type=event_type,
            content=content,
            metadata=metadata,
            idempotency_key=key,
        ).model_dump(mode="json", exclude_none=True)
        self.events.append(event)
        self.idempotency_keys.append(key)
        self.save()
        return event

    async def memory_step(self, **payload: Any) -> MemoryUpdateResponse:
        raise NotImplementedError("Memory API has been removed.")

    async def rag(
        self,
        *,
        context_trust_enabled: bool | None = None,
        **kwargs: Any,
    ) -> GroundednessResponse:
        extra = dict(kwargs.pop("extra", {}) or {})
        if self.session_id:
            extra.setdefault("session_id", self.session_id)
        if self.memory_state:
            extra.setdefault("memory_state", self.memory_state)
        extra.setdefault("metadata", dict(self.metadata))
        return await self._owner.grounding.rag(
            extra=extra,
            context_trust_enabled=(
                self.context_trust_enabled
                if context_trust_enabled is None
                else context_trust_enabled
            ),
            **kwargs,
        )

    async def code(self, **kwargs: Any) -> GroundednessResponse:
        raise NotImplementedError("Code scoring has been removed. Use .rag() instead.")

    async def rollup(self, **options: Any) -> Mapping[str, Any]:
        return await self._owner.rollup(normalize_events(self.events), **options)

    def snapshot(self) -> TraceSessionSnapshot:
        return TraceSessionSnapshot(
            session_id=self.session_id,
            memory_state=self.memory_state,
            events=list(self.events),
            idempotency_keys=list(self.idempotency_keys),
            metadata=dict(self.metadata),
        )

    def save(self) -> TraceSessionSnapshot:
        snapshot = self.snapshot()
        if self._storage and self.session_id:
            self._storage.save(snapshot)
        return snapshot

    def close(self, *, delete_storage: bool = False) -> TraceSessionSnapshot:
        snapshot = self.save()
        if delete_storage and self._storage and self.session_id:
            self._storage.delete(self.session_id)
        return snapshot


class AsyncLatence:
    """Async TRACE client. ``async with AsyncLatence(...) as c:`` closes the pool."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        retry_policy: RetryPolicy | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        self._base_url = coerce_base_url(base_url)
        self._api_key = coerce_api_key(api_key)
        self._retry = retry_policy or RetryPolicy()
        self._headers = default_headers(self._api_key, headers)
        self._runpod = is_runpod_endpoint(self._base_url)
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            transport=transport,
            headers=self._headers,
        )
        self.privacy = AsyncPrivacyClient(self)
        self.grounding = AsyncGroundingClient(self)
        self.compression = AsyncCompressionClient(self)
        self.memory = AsyncMemoryClient(self)
        self.trace = self

    async def __aenter__(self) -> AsyncLatence:
        return self

    async def __aexit__(self, *exc) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    # --- public surface --------------------------------------------------

    async def health(self) -> Mapping[str, Any]:
        return await self._request("GET", "/healthz", expected_model=None)

    async def ready(self) -> Mapping[str, Any]:
        return await self._request("GET", "/readyz", expected_model=None)

    async def agent_help(self) -> Mapping[str, Any]:
        return await self._request("GET", "/agent-help", expected_model=None)

    async def score_groundedness(
        self,
        *,
        response_text: str,
        query: str | None = None,
        chunk_ids: Sequence[str] | None = None,
        raw_context: RawContextInput | None = None,
        support_units: PremiseSupportUnits | None = None,
        attribution_mode: AttributionMode = AttributionMode.CLOSED_BOOK,
        primary_metric: str | None = None,
        coverage_threshold: float | None = None,
        raw_context_chunk_tokens: int | None = None,
        response_chunk_tokens: int | None = None,
        language: str | None = None,
        locale: str | None = None,
        context_trust_enabled: bool = True,
        runtime_head_features: Mapping[str, float] | None = None,
        trajectory_features: Mapping[str, float] | None = None,
        profile: str | None = None,
        scoring_mode: str | None = None,
        response_format: str | None = None,
        include_triangular_diagnostics: bool | None = None,
        evidence_limit: int | None = None,
        heatmap_format: str | None = None,
        auto_decide: bool | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> GroundednessResponse:
        payload = self._build_payload(
            response_text=response_text,
            query=query,
            chunk_ids=chunk_ids,
            raw_context=raw_context,
            support_units=support_units,
            attribution_mode=attribution_mode,
            primary_metric=primary_metric,
            coverage_threshold=coverage_threshold,
            raw_context_chunk_tokens=raw_context_chunk_tokens,
            response_chunk_tokens=response_chunk_tokens,
            language=language,
            locale=locale,
            context_trust_enabled=context_trust_enabled,
            runtime_head_features=runtime_head_features,
            trajectory_features=trajectory_features,
            profile=profile,
            scoring_mode=scoring_mode,
            response_format=response_format,
            include_triangular_diagnostics=include_triangular_diagnostics,
            evidence_limit=evidence_limit,
            heatmap_format=heatmap_format,
            auto_decide=auto_decide,
            extra=extra,
        )
        return await self._request(
            "POST",
            "/v1/grounding",
            json=payload,
            expected_model=GroundednessResponse,
        )

    async def redact_compliance(
        self,
        *,
        text: str,
        mode: ComplianceLabelMode = ComplianceLabelMode.OPEN,
        categories: Sequence[str] | None = None,
        labels: Sequence[str] | None = None,
        threshold: float = 0.5,
        redact: bool = True,
        redaction_mode: ComplianceRedactionMode = ComplianceRedactionMode.MASK,
        custom_labels: ComplianceCustomLabels | None = None,
        country: str | None = None,
        flat_ner: bool = True,
        multi_label: bool = False,
        include_original_text: bool = False,
        extra: Mapping[str, Any] | None = None,
    ) -> ComplianceRedactionResponse:
        normalised_custom = [
            c.model_dump(exclude_none=True) if isinstance(c, ComplianceCustomLabel) else dict(c)
            for c in (custom_labels or [])
        ]
        try:
            req = ComplianceRedactionRequest(
                text=text,
                mode=mode,
                categories=list(categories or []),
                labels=list(labels) if labels else None,
                threshold=threshold,
                redact=redact,
                redaction_mode=redaction_mode,
                custom_labels=[ComplianceCustomLabel(**c) for c in normalised_custom],
                country=country,
                flat_ner=flat_ner,
                multi_label=multi_label,
                include_original_text=include_original_text,
            )
        except ValidationError as exc:
            raise LatenceTraceValidationError(
                f"client-side compliance request validation failed: {exc.errors()[:3]}",
                status=422,
            ) from exc
        body = req.model_dump(mode="json", exclude_none=True)
        if extra:
            body.update(dict(extra))
        return await self._request(
            "POST",
            "/v1/redact",
            json=body,
            expected_model=ComplianceRedactionResponse,
        )

    async def rollup(
        self,
        turns: Sequence[Mapping[str, Any]],
        *,
        as_model: bool = False,
        **options: Any,
    ) -> RollupResponse | Mapping[str, Any]:
        body = await self._request(
            "POST",
            "/groundedness/rollup",
            json={"turns": list(turns), **options},
            expected_model=None,
        )
        normalized = _normalize_rollup_body(body)
        if as_model:
            return RollupResponse.model_validate({**normalized, "raw": body})
        return normalized

    def session(self, **kwargs: Any) -> AsyncTraceSession:
        raise NotImplementedError("Sessions have been removed. Use stateless grounding.rag() calls.")

    # --- internal --------------------------------------------------------

    def _build_payload(
        self,
        *,
        response_text: str,
        query: str | None,
        chunk_ids: Sequence[str] | None,
        raw_context: RawContextInput | None,
        support_units: PremiseSupportUnits | None,
        attribution_mode: AttributionMode,
        primary_metric: str | None,
        coverage_threshold: float | None,
        raw_context_chunk_tokens: int | None,
        response_chunk_tokens: int | None,
        language: str | None,
        locale: str | None,
        context_trust_enabled: bool,
        runtime_head_features: Mapping[str, float] | None,
        trajectory_features: Mapping[str, float] | None,
        profile: str | None,
        scoring_mode: str | None,
        response_format: str | None,
        include_triangular_diagnostics: bool | None,
        evidence_limit: int | None,
        heatmap_format: str | None,
        auto_decide: bool | None,
        extra: Mapping[str, Any] | None,
    ) -> dict:
        return _build_groundedness_payload(
            runpod=self._runpod,
            response_text=response_text,
            query=query,
            chunk_ids=chunk_ids,
            raw_context=raw_context,
            support_units=support_units,
            attribution_mode=attribution_mode,
            primary_metric=primary_metric,
            coverage_threshold=coverage_threshold,
            raw_context_chunk_tokens=raw_context_chunk_tokens,
            response_chunk_tokens=response_chunk_tokens,
            language=language,
            locale=locale,
            context_trust_enabled=context_trust_enabled,
            runtime_head_features=runtime_head_features,
            trajectory_features=trajectory_features,
            profile=profile,
            scoring_mode=scoring_mode,
            response_format=response_format,
            include_triangular_diagnostics=include_triangular_diagnostics,
            evidence_limit=evidence_limit,
            heatmap_format=heatmap_format,
            auto_decide=auto_decide,
            extra=extra,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        headers: Mapping[str, str] | None = None,
        expected_model: type[BaseModel] | None = None,
    ) -> Any:
        attempt = 0
        while True:
            try:
                request_path = self._base_url if self._runpod else path
                request_json = (
                    runpod_request_body(method, path, json, headers) if self._runpod else json
                )
                response = await self._client.request(
                    "POST" if self._runpod else method,
                    request_path,
                    json=request_json,
                    headers=headers,
                )
            except httpx.TimeoutException as exc:
                if attempt >= self._retry.max_retries:
                    raise LatenceTraceTimeout(str(exc)) from exc
                await asyncio.sleep(self._retry.sleep_for(attempt, None))
                attempt += 1
                continue
            except httpx.HTTPError as exc:
                raise LatenceTraceAPIError(str(exc), status=0) from exc

            if response.status_code < 400:
                return self._parse_success(response, expected_model)

            if response.status_code in RETRYABLE_STATUS and attempt < self._retry.max_retries:
                retry_after = parse_retry_after(response.headers.get("Retry-After"))
                await asyncio.sleep(self._retry.sleep_for(attempt, retry_after))
                attempt += 1
                continue

            raise self._error_from_response(response)

    def _parse_success(
        self,
        response: httpx.Response,
        expected_model: type[BaseModel] | None,
    ) -> Any:
        request_id = response.headers.get("x-request-id")
        body = response.json()
        if self._runpod:
            body, runpod_request_id = unwrap_runpod_response(body)
            request_id = request_id or runpod_request_id
        if expected_model is None:
            if isinstance(body, dict) and request_id and "request_id" not in body:
                body = {**body, "request_id": request_id}
            return body
        try:
            instance = expected_model.model_validate({**body, "raw": body})
        except ValidationError as exc:
            raise LatenceTraceServerError(
                f"server response did not match expected schema: {exc.errors()[:3]}",
                status=200,
                request_id=request_id,
            ) from exc
        if request_id and getattr(instance, "request_id", None) is None:
            object.__setattr__(instance, "request_id", request_id)
        return instance

    @staticmethod
    def _error_from_response(response: httpx.Response) -> LatenceTraceAPIError:
        try:
            body = response.json()
        except ValueError:
            body = response.text
        request_id = response.headers.get("x-request-id")
        err = decode_error(response.status_code, body, request_id)
        if isinstance(err, LatenceTraceRateLimited):
            err.retry_after = parse_retry_after(response.headers.get("Retry-After"))
        return err


AsyncLatenceTraceClient = AsyncLatence
