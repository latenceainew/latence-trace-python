"""Official Python SDK for Latence TRACE.

Two top-level clients:

- :class:`Latence` -- synchronous, suitable for scripts,
  Jupyter, CLI tools, and request-scoped server frameworks.
- :class:`AsyncLatence` -- asyncio version with the same
  surface, suitable for FastAPI / aiohttp servers and pipelines.

Both implementations share retry, backoff, OTel propagation, and
typed Pydantic models, so calling code stays identical regardless of
the runtime.
"""

from latence.async_client import AsyncLatence, AsyncLatenceTraceClient  # noqa: F401
# from latence.async_client import AsyncTraceSession  # removed: sessions API removed
from latence.client import Latence, LatenceTraceClient  # noqa: F401
# from latence.client import TraceSession  # removed: sessions API removed
from latence.errors import (
    LatenceTraceAPIError,
    LatenceTraceAuthError,
    LatenceTraceRateLimited,
    LatenceTraceServerError,
    LatenceTraceTimeout,
    LatenceTraceValidationError,
)
from latence.models import (
    AttributionMode,
    ComplianceCustomLabel,
    ComplianceEntity,
    ComplianceLabelMode,
    ComplianceRedactionMode,
    ComplianceRedactionRequest,
    ComplianceRedactionResponse,
    ComplianceUsage,
    CompressionResponse,
    CorpusRoute,
    GroundednessNLIAtom,
    GroundednessNLIClaim,
    GroundednessNLIDiagnostics,
    GroundednessRequest,
    GroundednessResponse,
    GroundednessScores,
    # MemoryUpdateResponse,  # removed: memory API removed
    NLIVerdict,
    RiskBand,
    RollupDriftTrend,
    RollupResponse,
    RollupTopDeadFile,
    RuntimeDecision,
    RuntimeEvidenceUnit,
    RuntimeUnsupportedSpan,
    SupportUnit,
    TokenScore,
)
from latence.sessions import (
    # FileSessionStorage,  # removed: sessions API removed
    # InMemorySessionStorage,  # removed: sessions API removed
    # SessionStorage,  # removed: sessions API removed
    TraceEvent,
    # TraceSessionSnapshot,  # removed: sessions API removed
)

__version__ = "0.1.6"

__all__ = [
    "AsyncLatence",
    "AsyncLatenceTraceClient",
    # "AsyncTraceSession",  # removed: sessions API removed
    "AttributionMode",
    "ComplianceCustomLabel",
    "ComplianceEntity",
    "ComplianceLabelMode",
    "ComplianceRedactionMode",
    "ComplianceRedactionRequest",
    "ComplianceRedactionResponse",
    "ComplianceUsage",
    "CompressionResponse",
    "CorpusRoute",
    # "FileSessionStorage",  # removed: sessions API removed
    "GroundednessNLIAtom",
    "GroundednessNLIClaim",
    "GroundednessNLIDiagnostics",
    "GroundednessRequest",
    "GroundednessResponse",
    "GroundednessScores",
    # "InMemorySessionStorage",  # removed: sessions API removed
    "Latence",
    "LatenceTraceAPIError",
    "LatenceTraceAuthError",
    "LatenceTraceClient",
    "LatenceTraceRateLimited",
    "LatenceTraceServerError",
    "LatenceTraceTimeout",
    "LatenceTraceValidationError",
    # "MemoryUpdateResponse",  # removed: memory API removed
    "NLIVerdict",
    "RiskBand",
    "RollupDriftTrend",
    "RollupResponse",
    "RollupTopDeadFile",
    "RuntimeDecision",
    "RuntimeEvidenceUnit",
    "RuntimeUnsupportedSpan",
    # "SessionStorage",  # removed: sessions API removed
    "SupportUnit",
    "TokenScore",
    "TraceEvent",
    # "TraceSession",  # removed: sessions API removed
    # "TraceSessionSnapshot",  # removed: sessions API removed
    "__version__",
]
