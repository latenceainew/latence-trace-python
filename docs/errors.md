# Errors

All SDK exceptions inherit from `LatenceTraceAPIError`.

Common subclasses:

- `LatenceTraceAuthError` for invalid or missing credentials.
- `LatenceTraceRateLimited` for HTTP 429 responses. The `retry_after` attribute is set when the server provides it.
- `LatenceTraceTimeout` for client-side timeouts.
- `LatenceTraceValidationError` for request validation errors.
- `LatenceTraceServerError` for malformed or failed server responses.

The SDK retries transient `408`, `409`, `425`, `429`, and `5xx` responses according to `RetryPolicy`.
