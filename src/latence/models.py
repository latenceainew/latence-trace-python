"""SDK-facing pydantic models.

These mirror the server schema field-for-field for the surface that
production callers consume directly. Anything not yet typed still
rides along under ``GroundednessResponse.raw`` (and remains accessible
via ``model_extra`` on every model thanks to ``extra="allow"``), so
server-side additions never break the typed surface.

The typed coverage targets parity with
``latence_trace.api.models.GroundednessResponse`` /
``RuntimeDecisionRecord`` / ``GroundednessScores`` / ``RollupResponse``
so SDK callers do not have to reach into ``raw`` for any field the
server documents in its public response schema.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class RiskBand(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"


class AttributionMode(str, Enum):
    CLOSED_BOOK = "closed_book"
    OPEN_DOMAIN = "open_domain"


class ComplianceLabelMode(str, Enum):
    OPEN = "open"
    CATEGORY = "category"


class ComplianceRedactionMode(str, Enum):
    MASK = "mask"
    REPLACE = "replace"


class SupportUnit(BaseModel):
    """One structured premise (sentence/paragraph + attribution).

    Optional ``source_id`` / ``speaker`` / ``timestamp`` propagate to
    the per-unit attribution slot in the response so callers can render
    a citation panel without re-resolving the source.
    """

    model_config = ConfigDict(extra="allow")
    text: str
    source_id: str | None = None
    speaker: str | None = None
    timestamp: str | None = None
    metadata: Mapping[str, Any] | None = None


class TokenScore(BaseModel):
    model_config = ConfigDict(extra="allow")
    token: str
    char_start: int
    char_end: int
    g_t: float = Field(..., description="Per-token groundedness signal.")
    e_t: float | None = Field(default=None, description="Per-token query echo.")
    j_star: int | None = None


class NLIVerdict(BaseModel):
    model_config = ConfigDict(extra="allow")
    claim: str
    label: str
    score: float
    premise_index: int | None = None


class GroundednessNLIAtom(BaseModel):
    """Per-atom entailment record produced by atomic-fact decomposition.

    Mirrors ``latence_trace.api.models.GroundednessNLIAtom``.
    """

    model_config = ConfigDict(extra="allow")
    atom_index: int = 0
    text: str = ""
    char_start: int = 0
    char_end: int = 0
    entailment: float = 0.0
    neutral: float = 0.0
    contradiction: float = 0.0
    score: float = 0.0
    band: str | None = None
    skipped: bool = False
    skip_reason: str | None = None
    premise_count: int = 0
    support_ids: list[str] = Field(default_factory=list)
    support_unit_indices: list[int] = Field(default_factory=list)


class GroundednessNLIClaim(BaseModel):
    """Per-claim entailment record returned by the NLI verifier.

    Mirrors ``latence_trace.api.models.GroundednessNLIClaim``.
    ``band`` is the server-stamped verdict (green/amber/red/skipped)
    incorporating a contradiction-floor gate.
    """

    model_config = ConfigDict(extra="allow")
    index: int = 0
    text: str = ""
    char_start: int = 0
    char_end: int = 0
    entailment: float = 0.0
    neutral: float = 0.0
    contradiction: float = 0.0
    score: float = 0.0
    band: str | None = None
    skipped: bool = False
    skip_reason: str | None = None
    premise_count: int = 0
    support_ids: list[str] = Field(default_factory=list)
    support_unit_indices: list[int] = Field(default_factory=list)
    atoms: list[GroundednessNLIAtom] = Field(default_factory=list)


class GroundednessNLIDiagnostics(BaseModel):
    """Per-request NLI verification diagnostics.

    Mirrors ``latence_trace.api.models.GroundednessNLIDiagnostics``.
    """

    model_config = ConfigDict(extra="allow")
    aggregate_score: float | None = Field(
        default=None,
        validation_alias=AliasChoices("aggregate_score", "aggregate"),
    )
    claims: list[GroundednessNLIClaim] = Field(default_factory=list)
    claims_total: int | None = None
    claims_scored: int | None = None
    claims_skipped_for_budget: int | None = None
    claims_skipped_for_no_premises: int | None = None


class GroundednessScores(BaseModel):
    """Aggregate scores returned by ``/groundedness``.

    Mirrors ``latence_trace.api.models.GroundednessScores`` so SDK
    callers can read every documented score channel without
    falling through to ``raw``.
    """

    model_config = ConfigDict(extra="allow")
    # Headline / fused
    primary_name: str | None = None
    primary_score: float | None = None
    groundedness_v1: float | None = None
    groundedness_v2: float | None = None
    consensus_hardened: float | None = None
    # Reverse-context family
    reverse_context: float | None = None
    reverse_context_calibrated: float | None = None
    reverse_query_context: float | None = None
    triangular: float | None = None
    echo_mean: float | None = None
    grounded_coverage: float | None = None
    null_bank_size: int | None = None
    # NLI lane
    nli_aggregate: float | None = None
    nli_claim_count: int | None = None
    nli_skipped_count: int | None = None
    nli_contradiction_prob_max: float | None = None
    nli_cascade_triggered: bool | None = None
    # Literal lane
    literal_guarded: float | None = None
    literal_match_count: int | None = None
    literal_mismatch_count: int | None = None
    literal_total_count: int | None = None
    literal_novelty_min: float | None = None
    literal_novelty_missing_count: int | None = None
    # Semantic-entropy lane
    semantic_entropy_aggregate: float | None = None
    semantic_entropy_raw: float | None = None
    semantic_entropy_sample_count: int | None = None
    # Structured lane
    structured_source: float | None = None
    structured_source_guarded: float | None = None
    structured_source_detected: bool | None = None
    structured_source_typed_aligned: int | None = None
    structured_source_typed_count: int | None = None
    # AST / phantom verdicts (code lane)
    ast_phantom_symbol_count: int | None = None
    ast_phantom_verdict: str | None = None
    ast_literal_drift_count: int | None = None
    composite_phantom_score: float | None = None
    composite_phantom_probability: float | None = None
    composite_phantom_verdict: str | None = None
    # Coverage / observability
    coverage_score_u: float | None = None
    semantic_entropy: float | None = None
    context_coverage_ratio: float | None = None
    context_coverage_threshold: float | None = None
    context_attribution_ratio: float | None = None
    context_attribution_used_count: int | None = None
    support_units_used: int | None = None
    support_units_total: int | None = None
    support_units_usage_used: int | None = None
    support_units_usage_uncertain: int | None = None
    support_units_unused: int | None = None
    context_unused_ratio: float | None = None
    context_uncertain_ratio: float | None = None
    context_usage_ratio: float | None = None
    dead_weight_ratio: float | None = None
    dead_weight_file_count: int | None = None
    # Trust lane
    context_trust_score: float | None = Field(default=None, exclude=True)
    context_trust_suspicious_count: int | None = Field(default=None, exclude=True)
    context_trust_blocked_count: int | None = Field(default=None, exclude=True)
    context_trust_max_risk: float | None = Field(default=None, exclude=True)
    # Headline band
    risk_band: str | None = None


class GroundednessRequest(BaseModel):
    """Wire-compatible request body.

    Use exactly one premise lane: ``chunk_ids`` (vector fast path),
    ``raw_context`` (free-text), or ``support_units`` (structured).
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)
    query_text: str | None = None
    response_text: str
    chunk_ids: list[str] | None = None
    raw_context: str | None = None
    support_units: list[SupportUnit] | None = None
    attribution_mode: AttributionMode = AttributionMode.CLOSED_BOOK
    primary_metric: str | None = None
    coverage_threshold: float | None = None
    raw_context_chunk_tokens: int | None = None
    response_chunk_tokens: int | None = None
    # ``language`` is the canonical wire field the server reads when
    # selecting the per-class calibration bundle
    # (`latence_trace.api.models.GroundednessRequest.language`). Older
    # SDK callers used ``locale`` which the server silently dropped;
    # accept both names so existing call-sites keep working but the
    # body always serializes to ``language``.
    language: str | None = Field(
        default=None,
        validation_alias=AliasChoices("language", "locale"),
        serialization_alias="language",
    )
    context_trust_enabled: bool | None = None
    runtime_head_features: Mapping[str, float] | None = None
    trajectory_features: Mapping[str, float] | None = None
    # First-class scoring knobs the server reads. Until 0.1.5 these
    # were only reachable via the ``extra`` kwarg fall-through; promote
    # them so callers stop guessing at server keyword names.
    profile: str | None = None
    response_format: str | None = None
    include_triangular_diagnostics: bool | None = None
    evidence_limit: int | None = None
    heatmap_format: str | None = None
    auto_decide: bool | None = None
    scoring_mode: Literal["rag", "code"] | None = None


class RuntimeEvidenceUnit(BaseModel):
    """One support unit cited in the runtime decision evidence list."""

    model_config = ConfigDict(extra="allow")
    index: int | None = None
    support_id: str | None = None
    text: str | None = None
    coverage_score: float | None = None
    usage_state: str | None = None
    context_trust_state: str | None = None
    context_trust_score: float | None = None
    context_trust_labels: Sequence[str] = Field(default_factory=list)
    usage_confidence: float | None = None


class RuntimeUnsupportedSpan(BaseModel):
    """One token / span flagged as unsupported by the runtime decision."""

    model_config = ConfigDict(extra="allow")
    token_index: int | None = None
    token: str | None = None
    heatmap_score: float | None = None
    nli_score: float | None = None
    reverse_context_calibrated: float | None = None
    char_start: int | None = None
    char_end: int | None = None


class RuntimeDecision(BaseModel):
    """Decision record produced by ``build_runtime_decision``.

    Mirrors ``latence_trace.api.models.RuntimeDecisionRecord`` so the
    band-coercion fields (``band``, ``reason_codes``, ``policy_*``,
    thresholds, ``rollback_safe``) are typed and documented for
    SDK callers.
    """

    model_config = ConfigDict(extra="allow")
    action: str
    score: float
    score_channel: str
    class_key: str
    band: str | None = None
    policy_version: str | None = None
    policy_sha256: str | None = None
    head_id: str | None = None
    head_version: str | None = None
    head_registry_sha256: str | None = None
    head_enabled: bool | None = None
    head_score: float | None = None
    head_features_used: Sequence[str] = Field(default_factory=list)
    head_reason_codes: Sequence[str] = Field(default_factory=list)
    reason_codes: Sequence[str] = Field(default_factory=list)
    evidence: Sequence[RuntimeEvidenceUnit] = Field(default_factory=list)
    unsupported_spans: Sequence[RuntimeUnsupportedSpan] = Field(default_factory=list)
    allow_disabled: bool | None = None
    block_disabled: bool | None = None
    allow_threshold: float | None = None
    block_threshold: float | None = None
    rollback_safe: bool = True


class CorpusRoute(BaseModel):
    """Per-class router decision attached to ``GroundednessResponse``."""

    model_config = ConfigDict(extra="allow")
    corpus_type: str | None = None
    confidence: float | None = None
    source: str | None = None
    language: str | None = None
    bundle_metric: str | None = None
    bundle_metric_value: float | None = None
    artefact_sha256: str | None = None
    classifier_latency_ms: float | None = None
    classifier_probabilities: Mapping[str, float] | None = None
    classifier_top_classes: Sequence[Mapping[str, Any]] = Field(default_factory=list)
    fusion_weights_applied: Mapping[str, float] | None = None
    rule_reason: str | None = None
    scoring_mode_applied: str | None = None
    thresholds_applied: Mapping[str, float] | None = None


class GroundednessResponse(BaseModel):
    """Wire-compatible response body.

    Spans both the canonical FastAPI shape (nested ``scores``,
    ``runtime_decision``, etc.) and the RunPod ``compact`` flat shape
    (top-level ``band``, ``score``, ``groundedness_v2``); the
    pydantic validator backfills ``risk_band`` from either source.
    """

    model_config = ConfigDict(extra="allow")
    risk_band: RiskBand | None = None
    risk_reason: str | None = None
    scores: GroundednessScores = Field(default_factory=GroundednessScores)
    response_tokens: Sequence[TokenScore] = Field(default_factory=list)
    nli: Sequence[NLIVerdict] = Field(default_factory=list)
    support_units: Sequence[Mapping[str, Any]] = Field(default_factory=list)
    context_trust_diagnostics: Mapping[str, Any] | None = Field(default=None, exclude=True)
    runtime_decision: RuntimeDecision | None = None
    runtime_head_features: Mapping[str, float] | None = None
    runtime_feature_source: str | None = None
    runtime_feature_missing_groups: Sequence[str] = Field(default_factory=list)
    corpus_route: CorpusRoute | None = None
    heatmap: Mapping[str, Any] | None = None
    heatmap_html: str | None = None
    file_attribution: Mapping[str, Any] | None = None
    nli_diagnostics: GroundednessNLIDiagnostics | None = None
    semantic_entropy_diagnostics: Mapping[str, Any] | None = None
    literal_diagnostics: Mapping[str, Any] | None = None
    structured_diagnostics: Mapping[str, Any] | None = None
    code_lane_diagnostics: Mapping[str, Any] | None = Field(default=None, exclude=True)
    profile_diagnostics: Mapping[str, Any] | None = None
    next_memory_state: Mapping[str, Any] | None = Field(default=None, exclude=True)
    hot_context_preview: str | None = Field(default=None, exclude=True)
    memory_diagnostics: Mapping[str, Any] | None = Field(default=None, exclude=True)
    next_session_state: Mapping[str, Any] | None = Field(default=None, exclude=True)
    session_signals: Mapping[str, Any] | None = Field(default=None, exclude=True)
    amber_escalation: Mapping[str, Any] | None = None
    warnings: Sequence[str] = Field(default_factory=list)
    reason: str | None = None
    eligibility: Mapping[str, Any] | None = None
    debug: Mapping[str, Any] | None = None
    top_evidence: Sequence[Mapping[str, Any]] = Field(default_factory=list)
    query_tokens: Sequence[Mapping[str, Any]] = Field(default_factory=list)
    profile: str | None = None
    effective_profile: str | None = None
    scoring_mode: str | None = None
    attribution_mode: str | None = None
    session_id: str | None = None
    collection: str | None = None
    mode: str | None = None
    model: str | None = None
    time_ms: float | None = None
    # Compact / RunPod-flat lane (top-level when response_format=compact)
    band: str | None = None
    score: float | None = None
    groundedness_v2: float | None = None
    nli_aggregate: float | None = None
    auto_repair: bool | None = None
    request_id: str | None = None
    raw: Mapping[str, Any] | None = None

    @model_validator(mode="after")
    def fill_native_risk_band(self) -> GroundednessResponse:
        """Backfill ``risk_band`` from any of the three wire sources.

        Source priority (lowest-noise first):

        1. ``scores.risk_band`` — canonical FastAPI shape.
        2. Top-level ``band`` — RunPod compact shape.
        3. ``runtime_decision.band`` — fallback only when neither of
           the above is present (this branch should be rare now that
           the backend coerces ``runtime_decision.band`` to match
           calibration).
        """

        if self.risk_band is not None:
            return self
        candidates: list[Any] = [
            self.scores.risk_band,
            self.band,
        ]
        rd = self.runtime_decision
        if rd is not None and getattr(rd, "band", None):
            candidates.append(rd.band)
        for candidate in candidates:
            if candidate is None:
                continue
            normalized = {
                "low": "green",
                "medium": "amber",
                "high": "red",
            }.get(str(candidate).lower(), str(candidate).lower())
            if normalized in {item.value for item in RiskBand}:
                self.risk_band = RiskBand(normalized)
                return self
        return self


class ComplianceCustomLabel(BaseModel):
    label_name: str
    extractor: str


class ComplianceEntity(BaseModel):
    model_config = ConfigDict(extra="allow")
    start: int
    end: int
    text: str
    label: str
    score: float = 0.0
    source: str = "model"
    redacted_value: str | None = None
    redaction_mode: str | None = None
    metadata: Mapping[str, Any] | None = None


class ComplianceUsage(BaseModel):
    model_config = ConfigDict(extra="allow")
    chunks_processed: int
    labels_used: int
    entity_count: int = 0
    unique_labels: list[str] = Field(default_factory=list)
    redaction_mode: ComplianceRedactionMode | None = None
    redacted: bool = False
    mode: ComplianceLabelMode
    categories: list[str] = Field(default_factory=list)


class ComplianceRedactionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    text: str
    mode: ComplianceLabelMode = ComplianceLabelMode.OPEN
    categories: list[str] = Field(default_factory=list)
    labels: list[str] | None = None
    threshold: float = 0.5
    redact: bool = True
    redaction_mode: ComplianceRedactionMode = ComplianceRedactionMode.MASK
    custom_labels: list[ComplianceCustomLabel] = Field(default_factory=list)
    country: str | None = None
    flat_ner: bool = True
    multi_label: bool = False
    include_original_text: bool = False


class ComplianceRedactionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    success: bool = True
    original_text: str | None = None
    entities: list[ComplianceEntity] = Field(default_factory=list)
    entity_count: int
    unique_labels: list[str] = Field(default_factory=list)
    redacted_text: str | None = None
    chunks_processed: int
    labels_used: list[str] = Field(default_factory=list)
    label_mode: ComplianceLabelMode
    selected_categories: list[str] = Field(default_factory=list)
    processing_time_ms: float
    timings_ms: Mapping[str, float] = Field(default_factory=dict)
    usage: ComplianceUsage


class CompressionSpan(BaseModel):
    model_config = ConfigDict(extra="allow")
    start: int
    end: int
    text: str
    keep_score: float


class CompressionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    compressed_text: str
    original_tokens: int | None = None
    compressed_tokens: int | None = None
    compression_ratio: float | None = None
    compression_percentage: float = 0.0
    tokens_saved: int = 0
    preserved_terms: list[str] = Field(default_factory=list)
    compressed_messages: list[dict[str, Any]] | None = None
    spans: list[CompressionSpan] = Field(default_factory=list)
    provider: str | None = None
    diagnostics: Mapping[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    raw: Mapping[str, Any] | None = None


class MemoryUpdateResponse(BaseModel):
    """Deprecated - memory API removed"""

    model_config = ConfigDict(extra="allow")
    next_memory_state: Mapping[str, Any]
    hot_context: str = ""
    hot_context_preview: str | None = None
    actions: list[Mapping[str, Any]] = Field(default_factory=list)
    diagnostics: Mapping[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    raw: Mapping[str, Any] | None = None


class RollupTopDeadFile(BaseModel):
    """Per-file dead-weight metric inside :class:`RollupResponse`.

    Mirrors ``latence_trace.api.models.RollupTopDeadFile``.
    """

    model_config = ConfigDict(extra="allow")
    path: str = ""
    dead_turns: int = 0
    ema_owner_share: float = 0.0


class RollupDriftTrend(BaseModel):
    """Drift-z-score trajectory summary inside :class:`RollupResponse`.

    Mirrors ``latence_trace.api.models.DriftTrend``.
    """

    model_config = ConfigDict(extra="allow")
    min: float = 0.0
    max: float = 0.0
    mean: float = 0.0
    last: float = 0.0


class RollupResponse(BaseModel):
    """Session aggregates returned by ``/groundedness/rollup``.

    Mirrors ``latence_trace.api.models.RollupResponse``. The SDK's
    ``Latence.rollup`` normalizes the RunPod envelope (``{success,
    action, rollup: {...}}``) so this typed model is populated the
    same way for REST and RunPod transports.
    """

    model_config = ConfigDict(extra="allow")
    turns: int = 0
    noise_pct: float = 0.0
    model_drift_pct: float = 0.0
    retrieval_waste_pct: float = 0.0
    reason_code_histogram: Mapping[str, int] = Field(default_factory=dict)
    recommendations: list[str] = Field(default_factory=list)
    risk_band_trail: list[str] = Field(default_factory=list)
    drift_trend: RollupDriftTrend = Field(default_factory=RollupDriftTrend)
    top_dead_files: list[RollupTopDeadFile] = Field(default_factory=list)
    session_id: str | None = None
    heatmap: Mapping[str, Any] | None = None
    heatmap_html: str | None = None
    request_id: str | None = None
    raw: Mapping[str, Any] | None = None
