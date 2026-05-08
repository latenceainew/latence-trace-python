# DEPRECATED: Memory API has been removed from the product.
"""Call the stateless InfiniMem update endpoint directly."""

from latence import Latence

with Latence() as client:
    result = client.memory.step(
        turn_text="User needs refund status and approval constraints preserved.",
        memory_domain="support",
    )
    print(result.hot_context)
    print(result.diagnostics)
