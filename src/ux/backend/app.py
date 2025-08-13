from __future__ import annotations

import asyncio
from typing import Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .mcp_server import router as mcp_router
from .runtime.state import bus
from .schemas import (
    Event,
    ExportBundle,
    PhaseEvent,
    RewriteRequest,
    RewriteResponse,
    RunRequest,
    SessionSummary,
)
from .services.curation_service import apply_curation
from .services.paperqa_service import PaperQAService
from .services.rewrite_service import rewrite as rewrite_logic


app = FastAPI(title="PaperQA UX Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(mcp_router)

service = PaperQAService()


@app.post("/api/rewrite", response_model=RewriteResponse)  # type: ignore[misc]
async def api_rewrite(req: RewriteRequest) -> RewriteResponse:
    return rewrite_logic(req)


@app.post("/api/run", status_code=202)  # type: ignore[misc]
async def api_run(req: RunRequest) -> Dict[str, str]:
    # Orchestrate a single run in the background and stream events via WS
    settings = service.load_settings(req.settings_name or "optimized_ollama")
    # Apply curation knobs that affect Settings prior to query
    try:
        settings.answer.evidence_relevance_score_cutoff = req.curation.relevance_cutoff
        if req.curation.max_sources:
            settings.answer.answer_max_sources = req.curation.max_sources
    except Exception:
        pass

    async def _task() -> None:
        # Emit initial phase
        await bus.publish(PhaseEvent(data={"phase": "retrieval", "status": "start"}))
        session = await service.run_query(
            question=req.question,
            settings=settings,
            files=req.files,
            stream_answer=req.stream_answer,
        )
        # Post-query curation
        apply_curation(session, req.curation)
        # Save session summary
        # Build minimal sources list
        sources: list[dict] = []
        try:
            for c in getattr(session, "contexts", [])[
                : settings.answer.answer_max_sources or 10
            ]:
                title = getattr(c.text.doc, "title", None) or getattr(
                    c.text.doc, "docname", ""
                )
                citation = getattr(c.text.doc, "formatted_citation", None) or title
                page = getattr(c.text, "page", None)
                score = getattr(c, "score", None)
                sources.append({"citation": citation, "page": page, "score": score})
        except Exception:
            pass
        summary = SessionSummary(
            question=req.question,
            rewritten=(req.rewrite.rewritten if req.rewrite else None),
            filters=(req.rewrite.filters if req.rewrite else None),
            curation=req.curation,
            answer_markdown=getattr(session, "answer", None),
            sources=sources,
        )
        bus.set_latest_session(summary)

    asyncio.create_task(_task())
    return {"status": "accepted"}


@app.websocket("/ws/events")  # type: ignore[misc]
async def ws_events(ws: WebSocket) -> None:
    await ws.accept()
    try:
        async for event in bus.subscribe():
            await ws.send_json(event.model_dump())
    except WebSocketDisconnect:
        return


@app.get("/api/export/session.json", response_model=SessionSummary)  # type: ignore[misc]
def export_session() -> SessionSummary:
    latest = bus.latest_session
    if latest is None:
        raise JSONResponse(status_code=404, content={"error": "No session yet"})
    return latest


@app.get("/api/export/trace.jsonl")  # type: ignore[misc]
def export_trace() -> str:
    lines = []
    for ev in bus.trace:
        lines.append(Event.model_validate(ev).model_dump_json())
    return "\n".join(lines)


@app.get("/api/export/bundle.zip")  # type: ignore[misc]
def export_bundle() -> ExportBundle:  # placeholder: return JSON instead of ZIP
    latest = bus.latest_session
    if latest is None:
        raise JSONResponse(status_code=404, content={"error": "No session yet"})
    return ExportBundle(session=latest, trace=list(bus.trace))
