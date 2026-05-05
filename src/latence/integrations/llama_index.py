"""LlamaIndex node post-processor that scores response groundedness.

Use as a query-engine ``node_postprocessor`` to attach groundedness
metadata to each retrieved node *after* synthesis::

    from llama_index.core.query_engine import RetrieverQueryEngine
    from latence import Latence
    from latence.integrations.llama_index import LatenceTracePostProcessor

    engine = RetrieverQueryEngine.from_args(
        retriever,
        node_postprocessors=[LatenceTracePostProcessor(Latence())],
    )
    response = engine.query("...")
    print(response.metadata["latence_trace"]["risk_band"])
"""

from __future__ import annotations

import logging

try:  # pragma: no cover - extras-only import
    from llama_index.core.postprocessor.types import BaseNodePostprocessor
    from llama_index.core.schema import NodeWithScore, QueryBundle
except ImportError as exc:  # pragma: no cover - extras-only import
    raise ImportError(
        "llama_index integration requires the LlamaIndex extras. Install with: "
        "pip install 'latence[llama_index]'"
    ) from exc

from latence.client import Latence
from latence.errors import LatenceTraceAPIError
from latence.integrations import _trace
from latence.models import AttributionMode

logger = logging.getLogger(__name__)


class LatenceTracePostProcessor(BaseNodePostprocessor):
    """Attach a `latence_trace` annotation to each node + the bundle.

    LlamaIndex calls ``_postprocess_nodes`` with the retrieved nodes and
    the original query. We don't have the synthesised response yet at
    that point -- instead we score the raw retrieved context against
    the (in-flight) query so callers see the *retrieval-side*
    groundedness budget. To score the synthesised output, call
    ``Latence.grounding.rag`` from the response handler.
    """

    client: Latence
    attribution_mode: AttributionMode = AttributionMode.CLOSED_BOOK

    def __init__(
        self,
        client: Latence,
        *,
        attribution_mode: AttributionMode = AttributionMode.CLOSED_BOOK,
    ) -> None:
        super().__init__()
        object.__setattr__(self, "client", client)
        object.__setattr__(self, "attribution_mode", attribution_mode)

    @classmethod
    def class_name(cls) -> str:
        return "LatenceTracePostProcessor"

    def _postprocess_nodes(
        self,
        nodes: list[NodeWithScore],
        query_bundle: QueryBundle | None = None,
    ) -> list[NodeWithScore]:
        if not nodes or query_bundle is None:
            return nodes
        query = query_bundle.query_str
        context = [n.node.get_content() for n in nodes if n.node]
        if not context:
            return nodes
        try:
            response = _trace.score_rag(
                self.client,
                query=query,
                response_text=" ".join(context),
                raw_context=context,
                attribution_mode=self.attribution_mode,
            )
        except LatenceTraceAPIError as exc:
            logger.warning(
                "latence_trace_postprocess_failed",
                extra={"code": exc.code, "status": exc.status},
            )
            return nodes
        annotation = _trace.trace_metadata(response)
        for node in nodes:
            node.node.metadata.setdefault("latence_trace", annotation)
        return nodes
