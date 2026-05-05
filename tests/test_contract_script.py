from __future__ import annotations

import pytest

from scripts.check_contract import DEFAULT_MANIFEST, check_contract


def test_standalone_sdk_matches_runtime_manifest() -> None:
    if not DEFAULT_MANIFEST.exists():
        pytest.skip(f"runtime manifest not available at {DEFAULT_MANIFEST}")
    assert check_contract() == []
