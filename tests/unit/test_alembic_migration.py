"""Alembic V1 migration smoke test against in-memory SQLite.

Mirrors the Java Flyway test pattern : verifies the migration applies
cleanly without errors and creates the expected tables. Doesn't run
against a real Postgres (that's integration-test territory in Étape 9
with testcontainers) — SQLite is enough to catch syntax errors,
forgotten imports, missing constraints.

Caveat : SQLite ignores some Postgres-specific features (e.g. server
defaults via sa.func.now() get translated to CURRENT_TIMESTAMP).
Migration must avoid Postgres-only types (no JSONB, no array columns,
no ENUM). Currently we use only portable types — VARCHAR, INTEGER,
BOOLEAN, DATETIME — so SQLite-tested migrations work on Postgres.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def alembic_config(tmp_path: Path) -> Config:
    """Alembic Config pointing at a SQLite file in a temp dir."""
    db_path = tmp_path / "test.db"
    config = Config(str(REPO_ROOT / "alembic.ini"))
    # aiosqlite scheme — env.py uses async_engine_from_config which requires
    # an async driver. Plain `sqlite://` errors with InvalidRequestError.
    config.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_path}")
    # Override the script_location to absolute path so it works from any CWD.
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    return config


def test_v1_upgrade_creates_all_tables(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")
    url = alembic_config.get_main_option("sqlalchemy.url")
    assert url is not None
    # Use the sync sqlite driver for inspection (no need for async here)
    engine = create_engine(url.replace("sqlite+aiosqlite", "sqlite"))
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert {"customer", "app_user", "refresh_token", "alembic_version"} <= tables
    engine.dispose()


def test_v1_creates_expected_indexes(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")
    url = alembic_config.get_main_option("sqlalchemy.url")
    assert url is not None
    # Use the sync sqlite driver for inspection (no need for async here)
    engine = create_engine(url.replace("sqlite+aiosqlite", "sqlite"))
    inspector = inspect(engine)
    customer_idx = {idx["name"] for idx in inspector.get_indexes("customer")}
    user_idx = {idx["name"] for idx in inspector.get_indexes("app_user")}
    rt_idx = {idx["name"] for idx in inspector.get_indexes("refresh_token")}
    assert "ix_customer_email" in customer_idx
    assert "ix_app_user_username" in user_idx
    assert {"ix_refresh_token_token", "ix_refresh_token_username"} <= rt_idx
    engine.dispose()


def test_v1_downgrade_drops_all_tables(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")
    url = alembic_config.get_main_option("sqlalchemy.url")
    assert url is not None
    # Use the sync sqlite driver for inspection (no need for async here)
    engine = create_engine(url.replace("sqlite+aiosqlite", "sqlite"))
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    # Only alembic_version remains (alembic itself manages it)
    assert tables <= {"alembic_version"}
    engine.dispose()
