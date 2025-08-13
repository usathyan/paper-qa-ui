from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Callable, List, Optional

from paperqa import Docs, Settings

from src.config_manager import ConfigManager
from ..runtime.state import bus
from ..schemas import (
    AnswerEvent,
    LogEvent,
    MetricEvent,
    PhaseEvent,
    PhaseName,
    PhaseStatus,
)


logger = logging.getLogger(__name__)


class PaperQAService:
    def __init__(self) -> None:
        # Environment hardening to avoid external metadata calls
        os.environ.setdefault("CROSSREF_MAILTO", "")
        os.environ.setdefault("SEMANTIC_SCHOLAR_API_KEY", "")
        os.environ.setdefault("PAPERQA_DISABLE_METADATA", "1")

    def load_settings(self, config_name: str) -> Settings:
        cfg = ConfigManager().load_config(config_name)
        cfg.setdefault("parsing", {})["use_doc_details"] = False
        settings = Settings(**cfg)
        # Research defaults tuned in current app
        try:
            settings.parsing.use_doc_details = False
            settings.answer.evidence_relevance_score_cutoff = 0
            settings.answer.answer_max_sources = max(
                10, settings.answer.answer_max_sources
            )
            settings.answer.evidence_k = max(15, settings.answer.evidence_k)
            settings.answer.get_evidence_if_no_contexts = True
            settings.answer.group_contexts_by_question = True
            settings.answer.answer_filter_extra_background = True
            if getattr(settings.answer, "max_answer_attempts", None) in (None, 0):
                settings.answer.max_answer_attempts = 3
        except Exception:
            pass
        try:
            settings.agent.should_pre_search = True
            settings.agent.return_paper_metadata = True
            try:
                settings.agent.agent_evidence_n = max(
                    5, settings.agent.agent_evidence_n
                )
            except Exception:
                pass
            try:
                settings.agent.search_count = max(20, settings.agent.search_count)
            except Exception:
                pass
        except Exception:
            pass
        # Ollama stability
        try:
            if hasattr(settings.answer, "max_concurrent_requests"):
                settings.answer.max_concurrent_requests = max(
                    1, settings.answer.max_concurrent_requests
                )
        except Exception:
            pass
        return settings

    async def add_local_docs(self, docs: Docs, files: Optional[List[str]]) -> int:
        if files is None:
            # Scan ./papers
            base = Path("./papers")
            paths = (
                [
                    p
                    for p in base.iterdir()
                    if p.is_file()
                    and p.suffix.lower() in {".pdf", ".txt", ".md", ".html"}
                ]
                if base.exists()
                else []
            )
        else:
            paths = [Path(p) for p in files]
        added = 0
        for p in paths:
            try:
                t0 = time.perf_counter()
                name = await docs.aadd(str(p))
                logger.info("Added %s in %.2fs", p.name, time.perf_counter() - t0)
                if name:
                    added += 1
            except Exception as e:
                logger.error("Failed to add %s: %s", p.name, e)
        return added

    async def run_query(
        self,
        question: str,
        settings: Settings,
        files: Optional[List[str]],
        stream_answer: bool,
    ) -> Any:  # returns PaperQA session
        await bus.publish(
            PhaseEvent(data={"phase": PhaseName.retrieval, "status": PhaseStatus.start})
        )
        docs = Docs()
        added = await self.add_local_docs(docs, files)
        await bus.publish(LogEvent(data={"message": f"Indexed {added} document(s)"}))
        t0 = time.perf_counter()
        # Optional streaming callback
        callbacks: Optional[List[Callable[[str], Any]]] = None
        if stream_answer:

            async def _pub(chunk: str) -> None:
                await bus.publish(LogEvent(data={"message": chunk}))

            # Wrap sync interface expected by paperqa into an async->sync proxy
            def _cb(chunk: str) -> None:
                asyncio.create_task(_pub(chunk))

            callbacks = [_cb]
        session = await docs.aquery(question, settings=settings, callbacks=callbacks)
        elapsed = time.perf_counter() - t0
        await bus.publish(MetricEvent(data={"elapsed_s": elapsed}))
        await bus.publish(
            PhaseEvent(data={"phase": PhaseName.retrieval, "status": PhaseStatus.end})
        )
        await bus.publish(
            PhaseEvent(data={"phase": PhaseName.answer, "status": PhaseStatus.start})
        )
        if session.answer:
            await bus.publish(AnswerEvent(data={"markdown": session.answer}))
        await bus.publish(
            PhaseEvent(data={"phase": PhaseName.answer, "status": PhaseStatus.end})
        )
        return session
