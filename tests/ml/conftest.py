"""Shared fixtures for the ML test suite.

The ML tests are NOT marked ``@pytest.mark.integration`` — they run
in the default pytest invocation. They depend on the ``ml`` extra
(``uv sync --extra ml``) being installed ; CI pipelines that don't
need ML training skip them automatically via the
``pytest.importorskip("torch")`` collection-time guard at module
import.
"""

from __future__ import annotations

import pytest

# Skip the entire tests/ml/ subtree when torch is not installed.
# Keeps the default `pytest` invocation clean on a runtime-only
# install (no `--extra ml`).
torch = pytest.importorskip("torch", reason="ML training tests require the `ml` extra (uv sync --extra ml)")
