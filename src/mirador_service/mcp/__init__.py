"""Mirador MCP server — exposes domain + observability tools to LLM clients.

Mounts at `/mcp` on the existing FastAPI app (see :mod:`.mount`). Tool
catalogue mirrors the Java sibling (see ADR-0062 in the Java repo) :
7 domain tools + 7 backend-local observability tools, all returning
typed Pydantic DTOs (NEVER raw ORM entities).

Architectural constraint mirrored from the Java side : the Mirador
backend MUST stay infrastructure-agnostic. The MCP server only exposes
what the backend already PRODUCES in-process — Python `logging` ring
buffer, `prometheus_client` REGISTRY, FastAPI's auto-OpenAPI, the
domain services. Zero HTTP clients to Loki / Mimir / Grafana / GitLab /
GitHub / k8s. Those are external community MCPs the Claude session
adds independently via `claude mcp add`.

Public entry point : :func:`mount_mcp_server` in :mod:`.mount`.
"""

from __future__ import annotations

__all__: list[str] = []

# Re-exports added in :mod:`mirador_service.mcp.mount` once the module
# lands ; keeping this file intentionally empty until then so the package
# is importable in isolation (matters for unit tests of dtos / ring_buffer
# / metrics_registry / actuator that don't need the full mounting wiring).
