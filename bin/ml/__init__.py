"""ML training pipeline (Phase A — Customer Churn).

See [shared ADR-0061](https://gitlab.com/mirador1/mirador-service-shared/-/blob/main/docs/adr/0061-customer-churn-prediction.md)
for the architectural decisions (feature set, label SQL, PyTorch
MLP, ONNX export contract, MLflow registry).

Public surface :

- :mod:`bin.ml.feature_engineering` — extracts the 8 numeric features
  from a Postgres-shaped DataFrame.
- :mod:`bin.ml.model` — defines the :class:`ChurnMLP` PyTorch
  module + ONNX export helper.
- :mod:`bin.ml.seed_demo_data` — Faker-driven synthetic training
  set (1000 customers + 10K orders, 20 % churn rate, deterministic
  seed).
- :mod:`bin.ml.train_churn` — main training entry point. Run via
  ``uv run python -m bin.ml.train_churn`` or directly.

The package is opt-in : its dependencies live in the ``ml`` extra
(``uv sync --extra ml``) so the runtime serving container stays
slim. CI installs the extra only for the (future) training job.
"""
