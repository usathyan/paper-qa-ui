from __future__ import annotations

from typing import Any, Dict, cast

from fastapi import APIRouter

from .schemas import ExportBundle, RewriteRequest, RewriteResponse, RunRequest


router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/manifest")  # type: ignore[misc]
def manifest() -> Dict[str, Any]:
    return {
        "name": "paperqa-ux-backend",
        "version": "0.1.0",
        "tools": [
            {
                "name": "mcp.rewrite",
                "request": "RewriteRequest",
                "response": "RewriteResponse",
            },
            {"name": "mcp.run", "request": "RunRequest", "response": "EventStream"},
            {"name": "mcp.export", "request": "{kind}", "response": "ExportBundle"},
        ],
        "schemas": [
            "RewriteRequest",
            "RewriteResponse",
            "RunRequest",
            "ExportBundle",
        ],
    }


# Stubs for tool invocations (HTTP-based wrappers)
@router.post("/tools/rewrite", response_model=RewriteResponse)  # type: ignore[misc]
def tool_rewrite(req: RewriteRequest) -> RewriteResponse:
    from .services.rewrite_service import rewrite

    return rewrite(req)


@router.post("/tools/run")  # type: ignore[misc]
def tool_run(_: RunRequest) -> Dict[str, str]:
    # Trigger via main REST endpoint instead; this is a placeholder
    return {"status": "accepted"}


@router.get("/tools/export", response_model=ExportBundle)  # type: ignore[misc]
def tool_export() -> ExportBundle:
    # Delegate to main REST endpoint
    from .app import export_bundle  # local import to avoid circular during startup

    result = export_bundle()
    return cast(ExportBundle, result)
