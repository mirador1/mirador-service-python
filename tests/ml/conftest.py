"""Shared fixtures for the ML test suite.

Two axes of dependency exist :

- ``torch`` (the heavy training stack) — only the TRAINING tests
  need it (``test_features.py``, ``test_model.py``,
  ``test_onnx_export.py``). Each of those files declares its own
  ``pytest.importorskip("torch")`` at module top so the skip is
  precise (CI without ``--extra ml`` runs the runtime tests but
  skips the training ones, as designed in Phase C).
- ``onnxruntime`` (the lightweight inference engine, ~30 MB) — now
  in the runtime ``[project.dependencies]`` so it is ALWAYS
  available. Inference tests (``test_inference.py``,
  ``test_router_churn.py``) do NOT skip ; they run on every CI.

Removing the previous global ``importorskip`` here means the
runtime-only Phase C tests run as part of the default ``pytest``
invocation — which is what the coverage gate now expects (the
``ml/inference.py`` + ``ml/router.py`` + ``ml/risk_band.py`` +
``ml/dtos.py`` + ``ml/predictor_singleton.py`` modules are no
longer in the omit list of ``[tool.coverage.run]``).
"""

from __future__ import annotations
