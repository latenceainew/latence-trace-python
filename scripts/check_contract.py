"""Verify the SDK surface against the latence-trace runtime manifest."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNTIME_REPO = ROOT.parent / "latence-trace"
DEFAULT_MANIFEST = DEFAULT_RUNTIME_REPO / "docs/core_freeze/api_surface_manifest.json"


def _load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_path(root: object, path: str) -> bool:
    target = root
    for part in path.split("."):
        if not hasattr(target, part):
            return False
        target = getattr(target, part)
    return True


def check_contract(manifest_path: Path = DEFAULT_MANIFEST) -> list[str]:
    if str(ROOT / "src") not in sys.path:
        sys.path.insert(0, str(ROOT / "src"))

    from latence import AsyncLatence, AsyncTraceSession, Latence, TraceSession  # noqa: PLC0415

    manifest = _load_manifest(manifest_path)
    errors: list[str] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    sync_client = Latence(base_url="http://contract-check", transport=httpx.MockTransport(handler))
    async_client = AsyncLatence(
        base_url="http://contract-check",
        transport=httpx.MockTransport(handler),
    )
    roots = {
        "sync": {"client": sync_client, "TraceSession": TraceSession},
        "async": {"client": async_client, "AsyncTraceSession": AsyncTraceSession},
    }
    try:
        for product in manifest.get("product_paths", []):
            for mode, paths in (product.get("sdk") or {}).items():
                for path in paths:
                    if "." in path and path.split(".", 1)[0] in roots[mode]:
                        root_name, rest = path.split(".", 1)
                        root = roots[mode][root_name]
                    else:
                        root = roots[mode]["client"]
                        rest = path
                    if not _has_path(root, rest):
                        errors.append(f"{product['id']}: SDK {mode} path missing {path}")
    finally:
        sync_client.close()
        asyncio.run(async_client.aclose())
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    errors = check_contract(args.manifest)
    payload = {
        "success": not errors,
        "manifest": str(args.manifest),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
    else:
        print("Latence SDK contract check passed")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
