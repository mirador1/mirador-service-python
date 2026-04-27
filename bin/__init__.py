"""Top-level scripts namespace.

The ``bin/`` directory hosts scripts that are NOT part of the
runtime serving wheel — training pipelines, dev helpers, release
automation. Made an importable package (with this ``__init__.py``)
so subdirectories like :mod:`bin.ml` can be invoked via ``python
-m bin.ml.train_churn`` and exercised from ``tests/ml/`` via
standard imports.

Configured as first-party in :file:`pyproject.toml` ``[tool.ruff.lint.isort]``
so import ordering checks group these modules with the project's
own code rather than treating them as third-party.
"""
