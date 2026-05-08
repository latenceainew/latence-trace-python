# Changelog

## 0.2.0 (2026-05-08)

**Breaking**: default `base_url` changed from `http://localhost:8090` to
`https://api.latence.ai`. All traffic now routes through the authenticated
gateway which handles API key verification, rate limiting, balance gating,
and usage logging.

- **Endpoint paths** aligned with the public gateway surface:
  - `/groundedness` -> `/v1/grounding`
  - `/v1/compliance/redact` -> `/v1/redact`
  - `/v1/compression` -> `/v1/compress`
- RunPod-direct mode (`LATENCE_TRACE_DEPLOYMENT=runpod`) still works for
  local or self-hosted deployments; the legacy action map is preserved.
- Code scoring (`grounding.code()`) and sessions remain `NotImplementedError`.
  Use `grounding.rag()` for all groundedness scoring.

## 0.1.6

Initial public release.
