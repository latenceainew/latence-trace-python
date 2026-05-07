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

from latence.async_client import AsyncLatence, AsyncLatenceTraceClient, AsyncTraceSession
from latence.client import Latence, LatenceTraceClient, TraceSession
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
    GroundednessRequest,
    GroundednessResponse,
    GroundednessScores,
    MemoryUpdateResponse,
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
    FileSessionStorage,
    InMemorySessionStorage,
    SessionStorage,
    TraceEvent,
    TraceSessionSnapshot,
)

__version__ = "0.1.5"

__all__ = [
    "AsyncLatence",
    "AsyncLatenceTraceClient",
    "AsyncTraceSession",
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
    "FileSessionStorage",
    "GroundednessRequest",
    "GroundednessResponse",
    "GroundednessScores",
    "InMemorySessionStorage",
    "Latence",
    "LatenceTraceAPIError",
    "LatenceTraceAuthError",
    "LatenceTraceClient",
    "LatenceTraceRateLimited",
    "LatenceTraceServerError",
    "LatenceTraceTimeout",
    "LatenceTraceValidationError",
    "MemoryUpdateResponse",
    "NLIVerdict",
    "RiskBand",
    "RollupDriftTrend",
    "RollupResponse",
    "RollupTopDeadFile",
    "RuntimeDecision",
    "RuntimeEvidenceUnit",
    "RuntimeUnsupportedSpan",
    "SessionStorage",
    "SupportUnit",
    "TokenScore",
    "TraceEvent",
    "TraceSession",
    "TraceSessionSnapshot",
    "__version__",
]
