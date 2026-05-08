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
from latence.client import Latence, LatenceTraceClient  # noqa: F401
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
    NLIVerdict,
    RiskBand,
    RuntimeDecision,
    RuntimeEvidenceUnit,
    RuntimeUnsupportedSpan,
    SupportUnit,
    TokenScore,
)

__version__ = "0.2.0"

__all__ = [
    "AsyncLatence",
    "AsyncLatenceTraceClient",
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
    "GroundednessNLIAtom",
    "GroundednessNLIClaim",
    "GroundednessNLIDiagnostics",
    "GroundednessRequest",
    "GroundednessResponse",
    "GroundednessScores",
    "Latence",
    "LatenceTraceAPIError",
    "LatenceTraceAuthError",
    "LatenceTraceClient",
    "LatenceTraceRateLimited",
    "LatenceTraceServerError",
    "LatenceTraceTimeout",
    "LatenceTraceValidationError",
    "NLIVerdict",
    "RiskBand",
    "RuntimeDecision",
    "RuntimeEvidenceUnit",
    "RuntimeUnsupportedSpan",
    "SupportUnit",
    "TokenScore",
    "__version__",
]
