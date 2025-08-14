#!/usr/bin/env python3
"""
Paper-QA Gradio UI with optimized local Ollama support.
Based on insights from GitHub discussions and testing.
"""

import asyncio
import html
import logging
import os
import time
import re
from pathlib import Path
from typing import List, Tuple, Any, Dict, Generator
import json
import csv
import zipfile
from queue import Queue, Empty
import threading

import gradio as gr
import httpx
from paperqa import Docs, Settings
from paperqa.agents.tools import DEFAULT_TOOL_NAMES
import importlib

from ..config_manager import ConfigManager

# Configure logging with INFO level for cleaner output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set paper-qa to INFO level and turn down noisy libraries
logging.getLogger("paperqa").setLevel(logging.INFO)
logging.getLogger("litellm").setLevel(logging.WARNING)
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("lmi.types").setLevel(logging.ERROR)
logging.getLogger("lmi").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Global state
app_state: Dict[str, Any] = {
    "uploaded_docs": [],
    "settings": None,
    "docs": None,
    "status_tracker": None,
    "processing_status": "",
    "query_lock": None,
    "analysis_queue": None,
    "query_loop": None,
    "query_loop_thread": None,
    "session_data": None,
    "rewrite_info": None,
}

# Disable Gradio analytics
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"


def check_ollama_status() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        return bool(response.status_code == 200)
    except Exception:
        return False


class StatusTracker:
    """Simple status tracker for paper-qa operations."""

    def __init__(self) -> None:
        self.status_updates: List[str] = []
        self.current_step = 0

    def add_status(self, status: str) -> None:
        """Add a status update."""
        self.status_updates.append(f"{time.strftime('%H:%M:%S')} - {status}")
        logger.info(f"Status: {status}")

    def get_status_html(self) -> str:
        """Get formatted HTML of all status updates."""
        if not self.status_updates:
            return "<div class='pqa-muted' style='text-align:center'>Ready to process questions</div>"

        html_parts = ["<div class='pqa-subtle'>"]
        html_parts.append("<strong>Processing Status</strong>")
        html_parts.append("<ul style='margin:6px 0 0 18px;padding:0'>")
        for i, status in enumerate(self.status_updates[-10:], 1):
            html_parts.append(f"<li><small>{status}</small></li>")
        html_parts.append("</ul>")
        html_parts.append("</div>")
        return "".join(html_parts)

    def clear(self) -> None:
        """Clear all status updates."""
        self.status_updates = []
        self.current_step = 0


def initialize_settings(config_name: str = "optimized_ollama") -> Settings:
    """Initialize paper-qa settings with the specified configuration."""
    try:
        config_manager = ConfigManager()
        config_dict = config_manager.load_config(config_name)
        # Hardening: avoid external metadata providers for faster, local-only flows
        os.environ.setdefault("CROSSREF_MAILTO", "")
        os.environ.setdefault("SEMANTIC_SCHOLAR_API_KEY", "")
        os.environ.setdefault("PAPERQA_DISABLE_METADATA", "1")
        settings = Settings(**config_dict)

        # Tune settings for robust retrieval and research-intelligence defaults
        try:
            # Prefer to allow evidence even with low scores and gather more contexts
            settings.answer.evidence_relevance_score_cutoff = 0
            settings.answer.answer_max_sources = max(
                10, settings.answer.answer_max_sources
            )
            settings.answer.evidence_k = max(15, settings.answer.evidence_k)
            settings.answer.get_evidence_if_no_contexts = True
            settings.answer.group_contexts_by_question = True
            settings.answer.answer_filter_extra_background = True
            # Encourage retries and concurrency for richer evidence
            if getattr(settings.answer, "max_answer_attempts", None) in (None, 0):
                settings.answer.max_answer_attempts = 3
            try:
                # For local Ollama, reduce concurrency for stability
                if (
                    str(settings.llm).lower().startswith("ollama/")
                    or "ollama" in str(settings.llm).lower()
                ):
                    settings.answer.max_concurrent_requests = 1
                else:
                    settings.answer.max_concurrent_requests = max(
                        2, settings.answer.max_concurrent_requests
                    )
            except Exception:
                pass
        except Exception:
            pass
        try:
            # Disable doc details to avoid network lookups if configs enabled them
            settings.parsing.use_doc_details = False
        except Exception:
            pass
        # Agent-side defaults to enhance research capabilities
        try:
            if hasattr(settings, "agent"):
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

        # Ensure clinical_trials_search is available if using agent
        try:
            tool_names = (
                getattr(getattr(settings, "agent", object()), "tool_names", []) or []
            )
            if "clinical_trials_search" not in tool_names:
                settings.agent.tool_names = DEFAULT_TOOL_NAMES + [
                    "clinical_trials_search"
                ]
        except Exception:
            pass

        status_tracker = StatusTracker()
        app_state["settings"] = settings
        app_state["status_tracker"] = status_tracker
        logger.info(f"Initialized Settings with config: {config_name}")
        return settings
    except Exception as e:
        logger.error(f"Failed to initialize Settings: {e}")
        raise


def _ensure_query_loop() -> None:
    """Start a dedicated asyncio event loop in a background thread for model I/O."""
    if app_state.get("query_loop") and app_state.get("query_loop_thread"):
        return
    loop = asyncio.new_event_loop()

    def _run() -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    t = threading.Thread(target=_run, name="pqa-query-loop", daemon=True)
    t.start()
    app_state["query_loop"] = loop
    app_state["query_loop_thread"] = t


async def process_uploaded_files_async(files: List[Any]) -> Tuple[str, str]:
    """Process uploaded files by copying them to papers directory."""
    if not files:
        return "", "No files uploaded."

    # Ensure papers directory exists
    papers_dir = Path("./papers")
    papers_dir.mkdir(exist_ok=True)

    processed_files = []
    failed_files = []

    try:
        # Initialize settings if needed
        if not app_state["settings"]:
            app_state["settings"] = initialize_settings()

        # Update status tracker
        if "status_tracker" in app_state:
            app_state["status_tracker"].add_status("📁 Starting document processing...")

        # Ensure we have a Docs corpus ready for indexing uploaded files
        if app_state.get("docs") is None:
            app_state["docs"] = Docs()

        for i, file_obj in enumerate(files):
            # Handle Gradio file object variations
            wrote_bytes = False
            if isinstance(file_obj, dict):
                # Try common path-like keys first
                source_str = None
                for k in ("name", "path", "tmp_path", "file"):
                    v = file_obj.get(k)
                    if isinstance(v, str) and v:
                        source_str = v
                        break
                if source_str:
                    source_path = Path(source_str)
                else:
                    # If raw bytes provided, write to papers dir with original name
                    data = file_obj.get("data")
                    orig_name = (
                        file_obj.get("orig_name")
                        or file_obj.get("filename")
                        or "upload.pdf"
                    )
                    if isinstance(data, (bytes, bytearray)):
                        source_path = Path("./papers") / Path(str(orig_name)).name
                        try:
                            source_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(source_path, "wb") as f:
                                f.write(data)
                            wrote_bytes = True
                        except Exception:
                            pass
                    else:
                        # Fallback: treat as error
                        raise TypeError("Unrecognized file object from Gradio")
            elif hasattr(file_obj, "name"):
                # Newer Gradio versions return file objects with .name attribute
                source_path = Path(file_obj.name)
            else:
                # Fallback for string paths
                source_path = Path(file_obj)

            dest_path = papers_dir / source_path.name

            try:
                # Update status for current file
                if "status_tracker" in app_state:
                    app_state["status_tracker"].add_status(
                        f"📄 Processing {source_path.name} ({i + 1}/{len(files)})..."
                    )

                # Check if file is already in the target location
                if source_path.resolve() == dest_path.resolve() or wrote_bytes:
                    # File is already in the target location, skip copying
                    logger.info(
                        f"File {source_path.name} is already in papers directory, skipping copy"
                    )
                else:
                    # Copy file to papers directory
                    import shutil

                    if hasattr(file_obj, "name"):
                        # For file objects, use the object directly
                        shutil.copy2(file_obj.name, dest_path)
                    else:
                        # For string paths, use the path
                        shutil.copy2(source_path, dest_path)

                logger.info(f"Successfully copied: {source_path.name}")
                if "status_tracker" in app_state:
                    app_state["status_tracker"].add_status(
                        f"✅ Copied {source_path.name}"
                    )

                # Index the document into the in-memory Docs corpus
                try:
                    if "status_tracker" in app_state:
                        app_state["status_tracker"].add_status(
                            f"📚 Indexing {source_path.name}..."
                        )
                    t0 = time.time()
                    # Use permanent path in papers directory on the dedicated query loop
                    _ensure_query_loop()
                    qloop = app_state["query_loop"]
                    fut = asyncio.run_coroutine_threadsafe(
                        app_state["docs"].aadd(
                            str(dest_path), settings=app_state["settings"]
                        ),
                        qloop,
                    )
                    added_name = await asyncio.to_thread(fut.result, timeout=600)
                    logger.info(
                        f"Indexed {added_name or source_path.name} in {time.time() - t0:.2f}s"
                    )
                    if "status_tracker" in app_state:
                        app_state["status_tracker"].add_status(
                            f"📘 Indexed {source_path.name}"
                        )
                except Exception as index_err:
                    logger.error(f"Failed to index {source_path.name}: {index_err}")
                    failed_files.append(
                        f"{source_path.name}: indexing failed: {str(index_err)}"
                    )
                    if "status_tracker" in app_state:
                        app_state["status_tracker"].add_status(
                            f"❌ Failed to index {source_path.name}"
                        )
                    continue

                # Update app state
                doc_info = {
                    "filename": source_path.name,
                    "size": dest_path.stat().st_size if dest_path.exists() else 0,
                    "status": "Ready",
                    "path": str(dest_path),
                }
                app_state["uploaded_docs"].append(doc_info)
                processed_files.append(source_path.name)

                logger.info(f"Successfully processed: {source_path.name}")

            except Exception as e:
                logger.error(f"Failed to process {source_path.name}: {e}")
                failed_files.append(f"{source_path.name}: {str(e)}")
                if "status_tracker" in app_state:
                    app_state["status_tracker"].add_status(
                        f"❌ Failed to process {source_path.name}"
                    )

        # Update final status
        if "status_tracker" in app_state:
            app_state["status_tracker"].add_status(
                f"🎉 Processing complete! {len(processed_files)} documents ready for questions."
            )

        # Prepare status message
        if processed_files:
            status_msg = (
                f"✅ Successfully processed {len(processed_files)} documents:\n"
            )
            status_msg += "\n".join([f"  • {f}" for f in processed_files])
            status_msg += "\n\n📚 You can now ask questions about these documents!"
        else:
            status_msg = "❌ No documents were successfully processed."

        if failed_files:
            status_msg += f"\n\n❌ Failed to process {len(failed_files)} files:\n"
            status_msg += "\n".join([f"  • {f}" for f in failed_files])

        return f"Processed: {', '.join(processed_files)}", status_msg

    except Exception as e:
        error_msg = f"❌ Processing failed: {str(e)}"
        logger.error(f"Exception in process_uploaded_files: {e}", exc_info=True)
        if "status_tracker" in app_state:
            app_state["status_tracker"].add_status(f"❌ Processing failed: {str(e)}")
        return "", error_msg


def process_uploaded_files(files: List[str]) -> Tuple[str, str]:
    """Synchronous wrapper for process_uploaded_files_async."""
    return asyncio.run(process_uploaded_files_async(files))


async def process_question_async(
    question: str, config_name: str = "optimized_ollama", run_critique: bool = False
) -> Tuple[str, str, str, str, str]:
    """Process a question asynchronously using the stored documents."""
    max_retries = 3
    retry_delay = 2.0

    for attempt in range(max_retries):
        try:
            start_time = time.time()

            if not question.strip():
                return "", "", "", "", "Please enter a question."

            # Check if documents have been uploaded and processed
            if not app_state.get("uploaded_docs"):
                return (
                    "",
                    "",
                    "",
                    "",
                    "📚 Please upload documents first. Documents will be automatically processed when uploaded.",
                )

            # Check if Ollama is running (for local configurations)
            if "ollama" in config_name.lower() and not check_ollama_status():
                return (
                    "",
                    "",
                    "",
                    "",
                    "❌ Ollama is not running. Please start Ollama with 'ollama serve' and try again.",
                )

            logger.info(
                f"Processing question: {question} (attempt {attempt + 1}/{max_retries})"
            )
            logger.info(f"Number of uploaded docs: {len(app_state['uploaded_docs'])}")

            # Update status
            if "status_tracker" in app_state:
                app_state["status_tracker"].add_status("🤖 Initializing...")
                app_state["status_tracker"].add_status("🔍 Searching documents...")

            app_state["processing_status"] = "🔍 Searching documents..."

            # Get settings
            settings = app_state.get("settings")
            if not settings:
                settings = initialize_settings(config_name)
                app_state["settings"] = settings

            # Ensure a single active query to avoid event-loop/client contention
            if app_state.get("query_lock") is None:
                app_state["query_lock"] = asyncio.Lock()

            async with app_state["query_lock"]:
                # Build Docs corpus from uploaded files if not already available
                _ensure_query_loop()
                qloop = app_state["query_loop"]
                if app_state.get("docs") is None:
                    app_state["docs"] = Docs()
                    for d in app_state.get("uploaded_docs", []):
                        try:
                            fut_add = asyncio.run_coroutine_threadsafe(
                                app_state["docs"].aadd(d["path"], settings=settings),
                                qloop,
                            )
                            await asyncio.to_thread(fut_add.result, timeout=600)
                        except Exception as e:
                            logger.warning(
                                f"Skipping doc that failed to add: {d.get('filename')}: {e}"
                            )
                # Emit phase events to analysis stream (if active)
                try:
                    aq = app_state.get("analysis_queue")
                    if aq is not None:
                        aq.put(
                            {
                                "type": "phase",
                                "data": {"phase": "summaries", "status": "start"},
                            },
                            timeout=0.05,
                        )
                        aq.put(
                            {
                                "type": "phase",
                                "data": {"phase": "answer", "status": "start"},
                            },
                            timeout=0.05,
                        )
                except Exception:
                    pass

                # Query the in-memory Docs corpus on a dedicated long-lived loop
                # Schedule coroutine on the background loop and wait from current loop
                aquery_start = time.time()
                fut = asyncio.run_coroutine_threadsafe(
                    app_state["docs"].aquery(question, settings=settings), qloop
                )
                # Wait in a thread to avoid blocking current event loop
                session = await asyncio.to_thread(fut.result, timeout=600)
                aquery_elapsed = time.time() - aquery_start

                # Emit phase completion events and answer metrics
                try:
                    aq = app_state.get("analysis_queue")
                    if aq is not None:
                        aq.put(
                            {
                                "type": "phase",
                                "data": {"phase": "summaries", "status": "end"},
                            },
                            timeout=0.05,
                        )
                        aq.put(
                            {
                                "type": "phase",
                                "data": {"phase": "answer", "status": "end"},
                            },
                            timeout=0.05,
                        )
                        # Emit answer generation stats
                        try:
                            contexts = getattr(session, "contexts", []) or []
                            n_sources = len(contexts)
                            total_chars = 0
                            for c in contexts:
                                try:
                                    t = getattr(
                                        getattr(c, "text", object()), "text", None
                                    )
                                    if isinstance(t, str):
                                        total_chars += len(t)
                                except Exception:
                                    continue
                            aq.put(
                                {
                                    "type": "answer_stats",
                                    "data": {
                                        "elapsed_s": aquery_elapsed,
                                        "sources_included": n_sources,
                                        "approx_prompt_chars": total_chars,
                                        "attempts": 1,
                                    },
                                },
                                timeout=0.05,
                            )
                        except Exception:
                            pass
                except Exception:
                    pass

            processing_time = time.time() - start_time
            logger.info(f"Docs.aquery completed in {processing_time:.2f} seconds")

            # Extract answer and contexts from the session
            answer = getattr(session, "answer", "")
            contexts = getattr(session, "contexts", []) or []
            # Apply per-doc cap if configured
            try:
                cap_cfg = app_state.get("curation", {}) or {}
                cap = int(cap_cfg.get("per_doc_cap", 0) or 0)
                if cap > 0 and contexts:
                    kept: List[Any] = []
                    counts: Dict[str, int] = {}
                    for c in contexts:
                        try:
                            txt_obj = getattr(c, "text", None)
                            doc = (
                                getattr(txt_obj, "doc", None)
                                if txt_obj is not None
                                else None
                            )
                            title = None
                            citation = None
                            if doc is not None:
                                citation = getattr(doc, "formatted_citation", None)
                                title = getattr(doc, "title", None) or getattr(
                                    doc, "docname", None
                                )
                            name = citation or title or "Unknown"
                            if counts.get(name, 0) < cap:
                                kept.append(c)
                                counts[name] = counts.get(name, 0) + 1
                        except Exception:
                            kept.append(c)
                    contexts = kept
            except Exception:
                pass

            if answer and "insufficient information" not in answer.lower():
                if "status_tracker" in app_state:
                    app_state["status_tracker"].add_status(
                        "✅ Answer generated successfully!"
                    )
                app_state["processing_status"] = "✅ Answer generated successfully!"
            else:
                if "status_tracker" in app_state:
                    app_state["status_tracker"].add_status(
                        "⚠️ Limited information found - try a more general question"
                    )
                app_state["processing_status"] = (
                    "⚠️ Limited information found - try a more general question"
                )

            # Optional critique (LLM-backed when configured; falls back to heuristic)
            critique_html = ""
            if run_critique and answer:
                try:
                    critique_html = await build_llm_or_heuristic_critique_html(
                        question, answer, contexts, settings
                    )
                except Exception:
                    critique_html = "<div class='pqa-subtle'><small class='pqa-muted'>Critique unavailable.</small></div>"

            answer_html = format_answer_html(answer, contexts)
            sources_html = format_sources_html(contexts)
            metadata_html = format_metadata_html(
                {
                    "processing_time": processing_time,
                    "documents_searched": len(app_state["uploaded_docs"]),
                    "evidence_sources": len(contexts),
                    "confidence": 0.85 if contexts else 0.3,
                }
            )
            intelligence_html = build_intelligence_html(answer, contexts)
            if critique_html:
                intelligence_html += (
                    "<div style='margin-top:8px'><strong>Critique</strong>"
                    + critique_html
                    + "</div>"
                )

            # Session data for exports
            try:
                export_contexts = []
                for c in contexts:
                    txt_obj = getattr(c, "text", None)
                    doc = getattr(txt_obj, "doc", None) if txt_obj is not None else None
                    title = None
                    citation = None
                    if doc is not None:
                        citation = getattr(doc, "formatted_citation", None)
                        title = getattr(doc, "title", None) or getattr(
                            doc, "docname", None
                        )
                    export_contexts.append(
                        {
                            "doc": citation or title or "Unknown",
                            "page": getattr(c, "page", None),
                            "score": getattr(c, "score", None),
                            "text": getattr(txt_obj, "text", None)
                            if txt_obj is not None
                            else None,
                        }
                    )
                app_state["session_data"] = {
                    "question": question,
                    "answer": answer,
                    "contexts": export_contexts,
                    "processing_time": processing_time,
                    "documents_searched": len(app_state.get("uploaded_docs", [])),
                    "rewrite": app_state.get("rewrite_info"),
                    "metrics": {
                        "score_min": None,
                        "score_mean": None,
                        "score_max": None,
                    },
                }
            except Exception:
                pass

            return answer_html, sources_html, metadata_html, intelligence_html, ""

        except Exception as e:
            logger.error(
                f"Exception in process_question (attempt {attempt + 1}): {e}",
                exc_info=True,
            )

            # Check if it's an Ollama connection issue
            if "Event loop is closed" in str(e):
                # Attempt to reset LiteLLM async client to avoid stale-loop issues, then retry
                try:
                    import litellm  # runtime-only optional dependency

                    importlib.reload(litellm)
                    logger.info(
                        "Reloaded litellm to reset async HTTP client after loop-close error"
                    )
                except Exception:
                    pass
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    error_msg = (
                        "❌ Internal async client error. Please retry the question."
                    )
            elif "TCPTransport closed" in str(e) or "APIConnectionError" in str(e):
                if attempt < max_retries - 1:
                    logger.info(
                        f"Connection issue detected, retrying in {retry_delay} seconds..."
                    )
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    error_msg = "❌ Connection to Ollama failed after multiple attempts. Please ensure Ollama is running and try again."
                    logger.error("Ollama connection issue detected after all retries")
            else:
                # For non-connection errors, don't retry
                error_msg = f"❌ Processing failed: {str(e)}"

            app_state["processing_status"] = "❌ Error occurred during processing"
            return "", "", "", "", error_msg
    # Safety net (should not be reached)
    return "", "", "", "", "❌ Unknown error"


def process_question(
    question: str, config_name: str = "optimized_ollama", run_critique: bool = False
) -> Tuple[str, str, str, str, str, str, str]:
    """Synchronous wrapper for process_question_async."""
    answer_html, sources_html, metadata_html, intelligence_html, error_msg = (
        asyncio.run(process_question_async(question, config_name, run_critique))
    )

    # Get status updates
    progress_html = ""
    status_html = ""
    if "status_tracker" in app_state:
        status_html = app_state["status_tracker"].get_status_html()

    return (
        answer_html,
        sources_html,
        metadata_html,
        intelligence_html,
        error_msg,
        progress_html,
        status_html,
    )


def ask_with_progress(
    question: str,
    config_name: str = "optimized_ollama",
    run_critique: bool = False,
    rewrite_query_toggle: bool = False,
    use_llm_rewrite: bool = False,
    bias_retrieval: bool = False,
    score_cutoff: float = 0.0,
    per_doc_cap: int = 0,
    max_sources: int = 0,
    show_flags: bool = True,
    show_conflicts: bool = True,
) -> Generator[Tuple[str, str, str, str, str, str, str, Any], None, None]:
    """Stream pre-evidence progress inline, then yield final answer outputs.

    Output tuple order:
    (analysis_progress_html, answer_html, sources_html, metadata_html, intelligence_html, error_msg, status_html, ask_button_update)
    """
    panel_last = ""
    # Optionally rewrite query (heuristic or LLM-based) and optionally bias retrieval
    original_question = question
    if rewrite_query_toggle:
        try:
            settings = app_state.get("settings") or initialize_settings(config_name)
            rewrite_details: Dict[str, Any] = {"original": original_question}
            if use_llm_rewrite:
                try:
                    # Run LLM-based decomposition on dedicated loop
                    _ensure_query_loop()
                    loop = app_state["query_loop"]

                    async def _go() -> Dict[str, Any]:
                        return await llm_decompose_query(original_question, settings)

                    fut = asyncio.run_coroutine_threadsafe(_go(), loop)
                    decomp = fut.result(timeout=45)
                    # llm_decompose_query returns Dict[str, Any]
                    rewrite_details.update(decomp)
                    rw = str(decomp.get("rewritten") or original_question)
                    # Apply retrieval bias by appending filter hints
                    if bias_retrieval:
                        filters = decomp.get("filters") or {}
                        hints: List[str] = []
                        years = filters.get("years")
                        if isinstance(years, (list, tuple)) and len(years) == 2:
                            try:
                                hints.append(f"years {int(years[0])}-{int(years[1])}")
                            except Exception:
                                pass
                        venues = filters.get("venues") or []
                        if isinstance(venues, list) and venues:
                            hints.append("venues " + ", ".join(map(str, venues[:5])))
                        fields = filters.get("fields") or []
                        if isinstance(fields, list) and fields:
                            hints.append("fields " + ", ".join(map(str, fields[:5])))
                        if hints:
                            augmented = rw + " (" + "; ".join(hints) + ")"
                            question = augmented
                            rewrite_details["bias_applied"] = True
                            rewrite_details["augmented"] = augmented
                        else:
                            question = rw
                            rewrite_details["bias_applied"] = False
                    else:
                        question = rw
                        rewrite_details["bias_applied"] = False
                except Exception:
                    # Fallback to heuristic rewriter
                    question = rewrite_query(original_question, settings)
                    rewrite_details["rewritten"] = question
                    rewrite_details["filters"] = {}
                    rewrite_details["bias_applied"] = False
            else:
                question = rewrite_query(original_question, settings)
                rewrite_details["rewritten"] = question
                rewrite_details["filters"] = {}
                rewrite_details["bias_applied"] = False

            app_state["rewrite_info"] = rewrite_details
        except Exception:
            app_state["rewrite_info"] = {"original": original_question}

    # Apply evidence curation settings
    try:
        settings_cur = app_state.get("settings") or initialize_settings(config_name)
        try:
            settings_cur.answer.evidence_relevance_score_cutoff = float(score_cutoff)
        except Exception:
            pass
        try:
            if isinstance(max_sources, int) and max_sources > 0:
                settings_cur.answer.answer_max_sources = int(max_sources)
        except Exception:
            pass
        app_state["settings"] = settings_cur
        app_state["curation"] = {
            "per_doc_cap": int(per_doc_cap) if isinstance(per_doc_cap, int) else 0,
            "score_cutoff": float(score_cutoff)
            if isinstance(score_cutoff, (int, float))
            else 0.0,
            "max_sources": int(max_sources) if isinstance(max_sources, int) else 0,
        }
        app_state["ui_toggles"] = {
            "show_flags": bool(show_flags),
            "show_conflicts": bool(show_conflicts),
        }
    except Exception:
        pass

    try:
        for panel_html in stream_analysis_progress(
            question,
            config_name,
            original_question=original_question if rewrite_query_toggle else None,
        ):
            panel_last = panel_html
            status_html = (
                app_state["status_tracker"].get_status_html()
                if "status_tracker" in app_state and app_state["status_tracker"]
                else ""
            )
            # While running: disable Ask button and show progress label
            yield (
                panel_html,
                "",
                "",
                "",
                "",
                "",
                status_html,
                gr.update(value="Running…", interactive=False),
            )
    except Exception as e:
        err_panel = (
            f"<div style='color:#b00'>Pre-evidence error: {html.escape(str(e))}</div>"
        )
        panel_last = err_panel
        yield (
            err_panel,
            "",
            "",
            "",
            "",
            "",
            "",
            gr.update(value="Ask Question", interactive=True),
        )

    # Now produce the final answer, while streaming a synthesis heartbeat
    result_holder: Dict[str, Any] = {}

    def _run_query() -> None:
        (
            result_holder["answer_html"],
            result_holder["sources_html"],
            result_holder["metadata_html"],
            result_holder["intelligence_html"],
            result_holder["error_msg"],
            _progress_html,
            result_holder["status_html"],
        ) = process_question(question, config_name, run_critique)

    t = threading.Thread(target=_run_query, daemon=True)
    t.start()
    synth_start = time.time()
    # Reuse spinner style
    spinner_css = (
        "<style>@keyframes pqa-spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}"
        " .pqa-spinner{display:inline-block;width:14px;height:14px;border:2px solid #ccc;"
        " border-top-color:#3b82f6;border-radius:50%;animation:pqa-spin 0.8s linear infinite;"
        " margin-right:6px}</style>"
    )
    while t.is_alive():
        elapsed = time.time() - synth_start
        badges = (
            "<div style='margin:6px 0'>"
            "<span class='pqa-subtle' style='border-radius:10px;padding:2px 8px;font-size:12px;margin-right:6px'>Summaries</span>"
            "<span class='pqa-subtle' style='border-radius:10px;padding:2px 8px;font-size:12px;margin-right:6px'>Answer</span>"
            "</div>"
        )
        synth_block = (
            f"{spinner_css}<div class='pqa-panel' style='margin-top:8px;'>"
            f"<span class='pqa-spinner'></span> Synthesizing answer"
            f" <small class='pqa-muted'>({elapsed:.1f}s)</small>"
            f"</div>"
        )
        yield (
            panel_last + badges + synth_block,
            "",
            "",
            "",
            "",
            "",
            "",
            gr.update(value="Running…", interactive=False),
        )
        time.sleep(0.75)

    # Attempt to auto-scroll to the answer section after analysis completes
    scroll_js = (
        "<script>"
        "(function(){try{var el=document.getElementById('pqa-answer-anchor');"
        "if(el){el.scrollIntoView({behavior:'smooth',block:'start'});}"
        "else{location.hash='#pqa-answer-anchor';}}catch(e){}})();"
        "</script>"
    )

    completed_badges = (
        "<div style='margin:6px 0'>"
        "<span style='display:inline-block;background:#10b981;color:white;border-radius:10px;padding:2px 8px;font-size:12px;margin-right:6px'>Summaries✓</span>"
        "<span style='display:inline-block;background:#10b981;color:white;border-radius:10px;padding:2px 8px;font-size:12px;margin-right:6px'>Answer✓</span>"
        "</div>"
    )

    yield (
        panel_last + completed_badges + scroll_js,
        result_holder.get("answer_html", ""),
        result_holder.get("sources_html", ""),
        result_holder.get("metadata_html", ""),
        result_holder.get("intelligence_html", ""),
        result_holder.get("error_msg", ""),
        result_holder.get("status_html", ""),
        gr.update(value="Ask Question", interactive=True),
    )


def _run_pre_evidence_in_thread(
    question: str, settings: Settings, docs: Docs, q: Queue
) -> None:
    """Background worker to run pre-evidence and stream callbacks into queue."""
    _ensure_query_loop()
    loop = app_state["query_loop"]

    def cb(chunk: str) -> None:
        try:
            q.put({"type": "log", "data": chunk}, timeout=0.1)
        except Exception:
            pass
        # Heuristic: parse progress counts from logs to update contexts_selected
        try:
            text = str(chunk)
            cs: int | None = None
            # Pattern like "5/20" or "5 / 20 contexts"
            m = re.search(
                r"(\d+)\s*/\s*(\d+)(?:\s*(?:contexts?|evidence))?", text, re.I
            )
            if m:
                cs = int(m.group(1))
            else:
                m2 = re.search(r"contexts?\s*(?:selected)?\s*[:=]?\s*(\d+)", text, re.I)
                if m2:
                    cs = int(m2.group(1))
                else:
                    m3 = re.search(r"selected\s*[:=]?\s*(\d+)", text, re.I)
                    if m3:
                        cs = int(m3.group(1))
            if cs is not None:
                try:
                    q.put(
                        {"type": "metric", "data": {"contexts_selected": cs}},
                        timeout=0.05,
                    )
                except Exception:
                    pass
        except Exception:
            pass
        # Heuristic: parse candidate lines (doc name and/or score) from logs
        try:
            t = str(chunk)
            if re.search(r"\bcand(?:idate)?\b", t, re.I):
                # Extract optional score
                sc: float | None = None
                ms = re.search(r"score\s*[:=]\s*([-+]?[0-9]*\.?[0-9]+)", t, re.I)
                if ms:
                    try:
                        sc = float(ms.group(1))
                    except Exception:
                        sc = None
                # Extract a doc/title-like token between quotes or before score
                name = None
                mq = re.search(r"[‘'\"]([^‘'\"]{5,120})[’'\"]", t)
                if mq:
                    name = mq.group(1)
                if not name:
                    # Fallback: take a trailing segment before score
                    parts = re.split(r"score\s*[:=]", t, flags=re.I)
                    if parts:
                        seg = parts[0]
                        # Alnum and punctuation slice
                        seg = seg.strip()
                        seg = re.sub(r"\s+", " ", seg)
                        name = seg[-120:]
                candidate_items.append({"doc": name or "Candidate", "score": sc})
        except Exception:
            pass

    async def _go() -> Any:
        return await docs.aget_evidence(question, settings=settings, callbacks=[cb])

    try:
        # Phase start
        try:
            q.put(
                {"type": "phase", "data": {"phase": "retrieval", "status": "start"}},
                timeout=0.1,
            )
        except Exception:
            pass
        t0 = time.time()
        candidate_items: List[Dict[str, Any]] = []
        fut = asyncio.run_coroutine_threadsafe(_go(), loop)
        session = fut.result(timeout=600)
        elapsed = time.time() - t0
        # Emit simple metrics (contexts selected)
        try:
            q.put(
                {
                    "type": "metric",
                    "data": {
                        "contexts_selected": len(
                            getattr(session, "contexts", []) or []
                        ),
                        "elapsed_s": elapsed,
                    },
                },
                timeout=0.1,
            )
        except Exception:
            pass
        # Selection stats for transparency
        try:
            contexts = getattr(session, "contexts", []) or []
            scores: List[float] = []
            per_doc: Dict[str, int] = {}
            mmr_items: List[Dict[str, Any]] = []
            for c in contexts:
                sc = getattr(c, "score", None)
                if isinstance(sc, (int, float)):
                    scores.append(float(sc))
                txt_obj = getattr(c, "text", None)
                doc = getattr(txt_obj, "doc", None) if txt_obj is not None else None
                title = None
                citation = None
                if doc is not None:
                    citation = getattr(doc, "formatted_citation", None)
                    title = getattr(doc, "title", None) or getattr(doc, "docname", None)
                name = citation or title or "Unknown"
                per_doc[name] = per_doc.get(name, 0) + 1
                mmr_items.append(
                    {
                        "doc": name,
                        "score": float(sc) if isinstance(sc, (int, float)) else None,
                    }
                )
            score_min = min(scores) if scores else None
            score_max = max(scores) if scores else None
            score_mean = (sum(scores) / len(scores)) if scores else None
            q.put(
                {
                    "type": "stats",
                    "data": {
                        "score_min": score_min,
                        "score_mean": score_mean,
                        "score_max": score_max,
                        "per_doc": per_doc,
                    },
                },
                timeout=0.1,
            )
            try:
                mmr_items.sort(key=lambda x: (-(x.get("score") or -1e9)))
                q.put({"type": "mmr", "data": {"items": mmr_items}}, timeout=0.1)
            except Exception:
                pass
            # Emit candidate items if any were parsed from logs
            try:
                if candidate_items:
                    # Keep only the last ~200 to limit payload
                    trimmed = candidate_items[-200:]
                    # Normalize structure
                    norm: List[Dict[str, Any]] = []
                    for it in trimmed:
                        score_val = it.get("score")
                        norm.append(
                            {
                                "doc": str(it.get("doc", "Candidate")),
                                "score": (
                                    float(score_val)
                                    if isinstance(score_val, (int, float))
                                    else None
                                ),
                            }
                        )
                    q.put(
                        {"type": "mmr_candidates", "data": {"items": norm}}, timeout=0.1
                    )
            except Exception:
                pass
        except Exception:
            pass
        # Phase end
        try:
            q.put(
                {
                    "type": "phase",
                    "data": {
                        "phase": "retrieval",
                        "status": "end",
                        "elapsed_s": elapsed,
                    },
                },
                timeout=0.1,
            )
        except Exception:
            pass
    except Exception as e:
        try:
            q.put({"type": "log", "data": f"Error during pre-evidence: {e}"})
        except Exception:
            pass


def stream_analysis_progress(
    question: str,
    config_name: str = "optimized_ollama",
    original_question: str | None = None,
) -> Generator[str, None, None]:
    """Stream live analysis progress (pre-evidence) into an HTML panel."""
    # Initialize queue and settings/docs
    q: Queue = Queue(maxsize=1000)
    app_state["analysis_queue"] = q

    # Ensure settings and docs
    settings: Settings = app_state.get("settings") or initialize_settings(config_name)
    app_state["settings"] = settings

    if app_state.get("docs") is None:
        app_state["docs"] = Docs()
        _ensure_query_loop()
        qloop = app_state["query_loop"]
        for d in app_state.get("uploaded_docs", []):
            try:
                fut = asyncio.run_coroutine_threadsafe(
                    app_state["docs"].aadd(d["path"], settings=settings), qloop
                )
                # Best-effort add; ignore failures/timeouts
                try:
                    fut.result(timeout=300)
                except Exception:
                    pass
            except Exception:
                pass

    # Kick off background thread
    worker = threading.Thread(
        target=_run_pre_evidence_in_thread,
        args=(question, settings, app_state["docs"], q),
        daemon=True,
    )
    worker.start()

    # Initial UI shell
    start_ts = time.time()
    logs: List[str] = ["Started analysis..."]
    # No table rows in live panel; top evidence is rendered later in Research Intelligence
    retrieval_done = False
    contexts_selected = 0
    contexts_selected_filtered: int | None = None
    candidate_count: int | None = None
    mmr_lambda: float | None = None
    score_min: float | None = None
    score_mean: float | None = None
    score_max: float | None = None
    per_doc_counts: Dict[str, int] = {}
    mmr_items_state: List[
        Dict[str, Any]
    ] = []  # [{'doc': str, 'score': Optional[float]}]
    mmr_candidates_state: List[Dict[str, Any]] = []
    embed_latency_s: float | None = None
    # Answer-phase metrics
    answer_elapsed_s: float | None = None
    answer_sources_included: int | None = None
    answer_prompt_chars: int | None = None
    answer_attempts: int | None = None
    # Phase flags
    summaries_done: bool = False
    answer_done: bool = False
    # Controls snapshot
    try:
        cutoff = getattr(
            getattr(app_state["settings"], "answer", object()),
            "evidence_relevance_score_cutoff",
            None,
        )
    except Exception:
        cutoff = None
    try:
        get_if_none = bool(
            getattr(
                getattr(app_state["settings"], "answer", object()),
                "get_evidence_if_no_contexts",
                False,
            )
        )
    except Exception:
        get_if_none = False
    try:
        group_by_q = bool(
            getattr(
                getattr(app_state["settings"], "answer", object()),
                "group_contexts_by_question",
                False,
            )
        )
    except Exception:
        group_by_q = False
    try:
        filter_extra_bg = bool(
            getattr(
                getattr(app_state["settings"], "answer", object()),
                "answer_filter_extra_background",
                False,
            )
        )
    except Exception:
        filter_extra_bg = False
    try:
        max_sources = int(
            getattr(
                getattr(app_state["settings"], "answer", object()),
                "answer_max_sources",
                10,
            )
        )
    except Exception:
        max_sources = 10
    try:
        max_attempts = int(
            getattr(
                getattr(app_state["settings"], "answer", object()),
                "max_answer_attempts",
                1,
            )
        )
    except Exception:
        max_attempts = 1
    try:
        ev_k = int(
            getattr(
                getattr(app_state["settings"], "answer", object()), "evidence_k", 15
            )
        )
    except Exception:
        ev_k = 15

    def render_html() -> str:
        elapsed = time.time() - start_ts
        running = worker.is_alive()
        latest = logs[-1] if logs else ""
        # Clamp progress percent 0..100
        pct = 0
        if ev_k > 0 and contexts_selected >= 0:
            pct = int(max(0, min(100, round((contexts_selected / ev_k) * 100))))
        parts = [
            "<div class='pqa-panel' style='min-height:240px'>",
            "<style>@keyframes pqa-spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}} .pqa-spinner{display:inline-block;width:14px;height:14px;border:2px solid #9ca3af;border-top-color:#3b82f6;border-radius:50%;animation:pqa-spin 0.8s linear infinite;margin-right:6px}</style>",
            (
                "<div style='display:flex;align-items:center;gap:6px'>"
                + ("<span class='pqa-spinner'></span>" if running else "")
                + "<strong>Analysis Progress</strong>"
                + f" <small class='pqa-muted'>({elapsed:.1f}s)</small></div>"
            ),
            (
                "<div class='pqa-subtle' style='margin:6px 0'>"
                + (
                    f"<small class='pqa-muted'>Rewritten from: {html.escape(original_question)}</small>"
                    if original_question
                    else ""
                )
                + (
                    f"<div><small><strong>Rewritten query</strong>: {html.escape(question)}</small></div>"
                    if original_question
                    else ""
                )
                + _render_filters_inline(app_state.get("rewrite_info"))
                + "</div>"
            ),
            (
                "<div class='pqa-steps'>"
                + (
                    "<span class='pqa-step done'>Retrieval</span>"
                    if retrieval_done
                    else "<span class='pqa-step'>Retrieval</span>"
                )
                + (
                    "<span class='pqa-step done'>Summaries</span>"
                    if summaries_done
                    else "<span class='pqa-step'>Summaries</span>"
                )
                + (
                    "<span class='pqa-step done'>Answer</span>"
                    if answer_done
                    else "<span class='pqa-step'>Answer</span>"
                )
                + "</div>"
            ),
            (
                f"<div class='pqa-subtle pqa-bar'><div class='pqa-bar-fill {'pqa-bar-indet' if not retrieval_done and pct == 0 else ''}' style='width:{pct}%'></div></div>"
                + (
                    f"<div style='margin-top:4px'><small class='pqa-muted'>{contexts_selected}/{ev_k} contexts"
                    + (
                        f" (≥cutoff: {contexts_selected_filtered})"
                        if isinstance(contexts_selected_filtered, int)
                        else ""
                    )
                    + "</small></div>"
                )
            ),
            "<div class='pqa-subtle'>",
            f"<div><small>{html.escape(latest)}</small></div>",
            "</div>",
            # Transparency block
            "<div class='pqa-panel' style='margin-top:8px'>",
            "<strong>Processing Transparency</strong>",
            "<ul style='margin:6px 0 0 18px;padding:0'>",
            # Retrieval
            (
                f"<li><small>Query embedding & retrieval: embed_latency={embed_latency_s:.2f}s, candidate_count="
                + (str(candidate_count) if isinstance(candidate_count, int) else "N/A")
                + ", mmr_lambda="
                + (
                    f"{mmr_lambda:.2f}"
                    if isinstance(mmr_lambda, (int, float))
                    else "N/A"
                )
                + "</small></li>"
                if isinstance(embed_latency_s, (int, float))
                else "<li><small>Query embedding & retrieval: (running...)</small></li>"
            ),
            # Evidence selection (with score stats)
            (
                f"<li><small>Evidence selection: contexts_selected={contexts_selected}, evidence_k={ev_k}, cutoff={cutoff}, get_if_none={get_if_none}, score[min/mean/max]="
                + (
                    f"{score_min:.3f}/{score_mean:.3f}/{score_max:.3f}"
                    if all(
                        isinstance(x, (int, float))
                        for x in (score_min, score_mean, score_max)
                    )
                    else "N/A"
                )
                + "</small></li>"
            ),
            (
                "<li><small>Per‑doc counts: "
                + ", ".join(
                    [
                        f"{html.escape(name)}={count}"
                        for name, count in list(per_doc_counts.items())[:5]
                    ]
                )
                + (" …" if len(per_doc_counts) > 5 else "")
                + "</small></li>"
                if per_doc_counts
                else ""
            ),
            # Summaries
            (
                f"<li><small>Summaries synthesis: enabled={group_by_q or filter_extra_bg}, metrics=N/A</small></li>"
            ),
            # Prompt building
            (
                f"<li><small>Prompt building: answer_max_sources={max_sources}, sources_included="
                + (
                    str(answer_sources_included)
                    if isinstance(answer_sources_included, int)
                    else "N/A"
                )
                + ", prompt_length≈"
                + (
                    str(answer_prompt_chars)
                    if isinstance(answer_prompt_chars, int)
                    else "N/A"
                )
                + "</small></li>"
            ),
            # Answer generation (with elapsed/attempts)
            (
                f"<li><small>Answer generation: max_attempts={max_attempts}, elapsed="
                + (
                    f"{answer_elapsed_s:.2f}s"
                    if isinstance(answer_elapsed_s, (int, float))
                    else "N/A"
                )
                + ", attempts="
                + (str(answer_attempts) if isinstance(answer_attempts, int) else "N/A")
                + ", tokens=N/A</small></li>"
            ),
            # Post-processing
            (
                "<li><small>Post-processing: sources_used=N/A, final_contexts=N/A, postproc_time=N/A</small></li>"
            ),
            "</ul>",
            "</div>",
        ]
        # Curation preview (based on current settings and observed counts)
        try:
            cur = app_state.get("curation", {}) or {}
            cap = int(cur.get("per_doc_cap", 0) or 0)
            cutoff_disp = cur.get("score_cutoff", None)
            max_srcs = int(cur.get("max_sources", 0) or 0)
            if cap > 0 or isinstance(cutoff_disp, (int, float)) or max_srcs > 0:
                # Estimate post-cap total contexts (using observed per-doc counts)
                est_total = None
                if per_doc_counts and cap > 0:
                    est_total = sum(min(cap, c) for c in per_doc_counts.values())
                cap_str = f"per_doc_cap={cap}" if cap > 0 else "per_doc_cap=—"
                cutoff_str = (
                    f"cutoff={float(cutoff_disp):.2f}"
                    if isinstance(cutoff_disp, (int, float))
                    else "cutoff=—"
                )
                maxs_str = (
                    f"max_sources={max_srcs}" if max_srcs > 0 else "max_sources=—"
                )
                est_str = (
                    f"estimated_contexts_after_cap≈{est_total}"
                    if isinstance(est_total, int)
                    else "estimated_contexts_after_cap=—"
                )
                parts.append(
                    "<div class='pqa-panel' style='margin-top:8px'><strong>Curation preview</strong>"
                    + f"<div><small class='pqa-muted'>{cap_str}; {cutoff_str}; {maxs_str}; {est_str}</small></div>"
                    + "</div>"
                )
        except Exception:
            pass
        # MMR (Maximum Marginal Relevance) visualization: candidate vs selected
        if mmr_items_state or mmr_candidates_state:
            try:
                # Selected summary
                sel_scores = [
                    float(x["score"])
                    for x in mmr_items_state
                    if isinstance(x.get("score"), (int, float))
                ]
                sel_unique_docs = len(
                    {str(x.get("doc", "Unknown")) for x in mmr_items_state}
                )
                sel_total = len(mmr_items_state)
                sel_div_share = (sel_unique_docs / sel_total) if sel_total > 0 else 0.0
                # Candidate summary
                cand_scores = []
                for x in mmr_candidates_state:
                    sv = x.get("score")
                    if isinstance(sv, (int, float)):
                        cand_scores.append(float(sv))
                cand_total = len(mmr_candidates_state)

                # Overlay histogram (candidates in light blue, selected in blue)
                hist_svg = ""
                if cand_scores or sel_scores:
                    smin = min((cand_scores + sel_scores) or [0.0])
                    smax = max((cand_scores + sel_scores) or [1.0])
                    bins = 10
                    if smax <= smin:
                        smax = smin + 1e-6
                    width, height, pad = 320, 64, 4
                    bucket_c = [0] * bins
                    bucket_s = [0] * bins
                    for s in cand_scores:
                        idx = int((s - smin) / (smax - smin) * (bins - 1) + 1e-9)
                        idx = max(0, min(bins - 1, idx))
                        bucket_c[idx] += 1
                    for s in sel_scores:
                        idx = int((s - smin) / (smax - smin) * (bins - 1) + 1e-9)
                        idx = max(0, min(bins - 1, idx))
                        bucket_s[idx] += 1
                    maxc = max(bucket_c + bucket_s) if (bucket_c or bucket_s) else 1
                    bw = (width - 2 * pad) / bins
                    bars: List[str] = []
                    for i in range(bins):
                        c1 = bucket_c[i]
                        c2 = bucket_s[i]
                        bh1 = (
                            0 if maxc == 0 else int(((c1 / maxc) * (height - 2 * pad)))
                        )
                        bh2 = (
                            0 if maxc == 0 else int(((c2 / maxc) * (height - 2 * pad)))
                        )
                        xpos = int(pad + i * bw)
                        y1 = height - pad - bh1
                        y2 = height - pad - bh2
                        bars.append(
                            f"<rect x='{xpos}' y='{y1}' width='{max(1, int(bw - 1))}' height='{bh1}' fill='#93c5fd' />"
                        )
                        bars.append(
                            f"<rect x='{xpos}' y='{y2}' width='{max(1, int(bw - 1))}' height='{bh2}' fill='#3b82f6' />"
                        )
                    axis = (
                        f"<text x='{pad}' y='{height - 2}' font-size='9' fill='#9ca3af'>{smin:.2f}</text>"
                        f"<text x='{width - pad - 20}' y='{height - 2}' font-size='9' fill='#9ca3af' text-anchor='end'>{smax:.2f}</text>"
                    )
                    hist_svg = (
                        f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg'>"
                        + "".join(bars)
                        + axis
                        + "</svg>"
                    )
                parts.append("<div class='pqa-panel' style='margin-top:8px'>")
                parts.append(
                    "<strong>MMR (Maximum Marginal Relevance) selection</strong>"
                )
                parts.append(
                    f"<div style='margin-top:4px'><small class='pqa-muted'>Candidates={cand_total}; Selected={sel_total}, Unique docs={sel_unique_docs} (share={sel_div_share:.0%})</small></div>"
                )
                if hist_svg:
                    parts.append("<div style='margin-top:4px'>" + hist_svg + "</div>")
                parts.append("</div>")
            except Exception:
                pass
        # Compact per-doc bar visualization (top 5)
        if per_doc_counts:
            try:
                maxcnt = max(per_doc_counts.values())
                bars_items: List[str] = []
                for name, cnt in sorted(per_doc_counts.items(), key=lambda x: -x[1])[
                    :5
                ]:
                    pct = int(round((cnt / maxcnt) * 100)) if maxcnt > 0 else 0
                    bars_items.append(
                        f"<div style='margin:4px 0'><small>{html.escape(name)}</small>"
                        f"<div class='pqa-subtle' style='height:8px;border-radius:6px;overflow:hidden'><div style='height:100%;width:{pct}%;background:#3b82f6'></div></div>"
                        f"<small class='pqa-muted'>{cnt}</small></div>"
                    )
                parts.append(
                    "<div class='pqa-panel' style='margin-top:8px'><strong>Evidence by document</strong>"
                    + "".join(bars_items)
                    + "</div>"
                )
            except Exception:
                pass
        # Omit Top evidence table here; it belongs in Research Intelligence
        parts.append("</div>")
        return "".join(parts)

    # Stream loop
    yield render_html()
    # Poll queue until thread completes and queue is drained
    idle_cycles = 0
    while worker.is_alive() or not q.empty():
        try:
            evt = q.get(timeout=0.5)
            if isinstance(evt, dict) and evt.get("type") == "log":
                msg = str(evt.get("data", "")).strip()
                logs.append(msg)
                # Attempt to parse candidate_count and mmr_lambda from logs
                try:
                    m_c = re.search(r"candidates?\s*[:=]\s*(\d+)", msg, re.I)
                    if m_c:
                        candidate_count = int(m_c.group(1))
                except Exception:
                    pass
                try:
                    m_l = re.search(
                        r"mmr[_\s-]*lambda\s*[:=]\s*([0-9]*\.?[0-9]+)", msg, re.I
                    )
                    if m_l:
                        mmr_lambda = float(m_l.group(1))
                except Exception:
                    pass
            elif isinstance(evt, dict) and evt.get("type") == "phase":
                data = evt.get("data", {}) or {}
                if data.get("phase") == "retrieval" and data.get("status") == "end":
                    retrieval_done = True
                elif data.get("phase") == "summaries" and data.get("status") == "end":
                    summaries_done = True
                elif data.get("phase") == "answer" and data.get("status") == "end":
                    answer_done = True
            elif isinstance(evt, dict) and evt.get("type") == "metric":
                data = evt.get("data", {}) or {}
                try:
                    cs = int(data.get("contexts_selected", 0))
                    contexts_selected = max(0, cs)
                except Exception:
                    pass
                try:
                    el = data.get("elapsed_s", None)
                    if isinstance(el, (int, float)):
                        embed_latency_s = float(el)
                except Exception:
                    pass
            elif isinstance(evt, dict) and evt.get("type") == "stats":
                data = evt.get("data", {}) or {}
                try:
                    smin = data.get("score_min")
                    smean = data.get("score_mean")
                    smax = data.get("score_max")
                    if isinstance(smin, (int, float)):
                        score_min = float(smin)
                    if isinstance(smean, (int, float)):
                        score_mean = float(smean)
                    if isinstance(smax, (int, float)):
                        score_max = float(smax)
                    pdoc = data.get("per_doc") or {}
                    if isinstance(pdoc, dict):
                        # ensure str->int
                        tmp: Dict[str, int] = {}
                        for k, v in pdoc.items():
                            try:
                                tmp[str(k)] = int(v)
                            except Exception:
                                continue
                        per_doc_counts = tmp
                    # compute filtered contexts count using current cutoff, if scores present
                    try:
                        cutoff_val = float(
                            getattr(
                                getattr(app_state.get("settings"), "answer", object()),
                                "evidence_relevance_score_cutoff",
                                0.0,
                            )
                        )
                    except Exception:
                        cutoff_val = 0.0
                    scores_list = data.get("scores_list")
                    if isinstance(scores_list, list):
                        try:
                            contexts_selected_filtered = sum(
                                1
                                for v in scores_list
                                if isinstance(v, (int, float))
                                and float(v) >= cutoff_val
                            )
                        except Exception:
                            contexts_selected_filtered = None
                except Exception:
                    pass
            elif isinstance(evt, dict) and evt.get("type") == "mmr":
                data = evt.get("data", {}) or {}
                items = data.get("items") or []
                if isinstance(items, list):
                    # Shallow copy to avoid mutation issues
                    mmr_items_state = []
                    for it in items:
                        try:
                            mmr_items_state.append(
                                {
                                    "doc": str(it.get("doc", "Unknown")),
                                    "score": (
                                        float(it.get("score"))
                                        if isinstance(it.get("score"), (int, float))
                                        else None
                                    ),
                                }
                            )
                        except Exception:
                            continue
            elif isinstance(evt, dict) and evt.get("type") == "mmr_candidates":
                data = evt.get("data", {}) or {}
                items = data.get("items") or []
                if isinstance(items, list):
                    mmr_candidates_state = []
                    for it in items:
                        try:
                            mmr_candidates_state.append(
                                {
                                    "doc": str(it.get("doc", "Candidate")),
                                    "score": (
                                        float(it.get("score"))
                                        if isinstance(it.get("score"), (int, float))
                                        else None
                                    ),
                                }
                            )
                        except Exception:
                            continue
            elif isinstance(evt, dict) and evt.get("type") == "answer_stats":
                data = evt.get("data", {}) or {}
                try:
                    # Persist answer metrics for rendering
                    elapsed_ans = data.get("elapsed_s")
                    if isinstance(elapsed_ans, (int, float)):
                        answer_elapsed_s = float(elapsed_ans)
                    srcs = data.get("sources_included")
                    if isinstance(srcs, int):
                        answer_sources_included = srcs
                    plen = data.get("approx_prompt_chars")
                    if isinstance(plen, int):
                        answer_prompt_chars = plen
                    atts = data.get("attempts")
                    if isinstance(atts, int):
                        answer_attempts = atts
                except Exception:
                    pass
            idle_cycles = 0
            yield render_html()
        except Empty:
            idle_cycles += 1
            # heartbeat UI refresh every ~2s
            if idle_cycles % 4 == 0:
                yield render_html()
    logs.append("Analysis complete.")
    yield render_html()


def format_answer_html(answer: str, contexts: List) -> str:
    """Return markdown string for the answer block."""
    if not answer:
        return "_No answer generated._"

    return answer


def format_sources_html(contexts: List) -> str:
    """Format the sources as HTML."""
    if not contexts:
        return "<div class='pqa-subtle' style='text-align:center'><small class='pqa-muted'>No sources found.</small></div>"

    html_parts = [
        "<div class='pqa-panel' style='max-height:300px; overflow-y:auto;'>",
        "<h4>Evidence Sources:</h4>",
    ]

    for i, context in enumerate(contexts, 1):
        try:
            # Derive a robust citation/title
            citation = None
            title = None
            page = getattr(context, "page", None)
            score = getattr(context, "score", None)

            if hasattr(context, "text"):
                txt_obj = getattr(context, "text")
                # Extract document-level citation info if available
                doc = getattr(txt_obj, "doc", None)
                if doc is not None:
                    citation = getattr(doc, "formatted_citation", None)
                    title = getattr(doc, "title", None) or getattr(doc, "docname", None)
                # Extract underlying text string for snippet
                if hasattr(txt_obj, "text"):
                    text_str = getattr(txt_obj, "text") or ""
                else:
                    text_str = str(txt_obj)
            else:
                text_str = str(context)

            # Fallbacks
            display_name = (
                citation
                or title
                or getattr(getattr(context, "text", object()), "name", None)
                or f"Source {i}"
            )
            # Venue/reputation (when metadata available)
            venue_bits = []
            try:
                venue = None
                if hasattr(context, "text"):
                    doc = getattr(getattr(context, "text", object()), "doc", None)
                    if doc is not None:
                        venue = getattr(doc, "venue", None) or getattr(
                            doc, "journal", None
                        )
                if isinstance(venue, str) and venue.strip():
                    venue_bits.append(venue.strip())
            except Exception:
                pass
            snippet = text_str if isinstance(text_str, str) else str(text_str)
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."

            meta_bits = []
            if isinstance(page, (int, float)):
                meta_bits.append(f"p. {int(page)}")
            if isinstance(score, (int, float)):
                meta_bits.append(f"score={score:.3f}")
            # Flags: preprint / possible retraction (heuristic)
            flags_bits = []
            try:
                dn_low = (display_name or "").lower()
                if any(
                    k in dn_low for k in ["arxiv", "biorxiv", "medrxiv", "preprint"]
                ):
                    flags_bits.append("Preprint")
                if "retract" in dn_low:
                    flags_bits.append("Retracted?")
            except Exception:
                pass
            meta = (
                f" <small class='pqa-muted'>({' | '.join(meta_bits)})</small>"
                if meta_bits
                else ""
            )

            html_parts.append(
                "<div class='pqa-subtle' style='margin-bottom:10px; padding:10px; border-left: 3px solid #3b82f6;'>"
            )
            html_parts.append(f"<strong>{display_name}</strong>{meta}<br>")
            if venue_bits:
                html_parts.append(
                    f"<small class='pqa-muted'>Venue: {html.escape(', '.join(venue_bits))}</small><br>"
                )
            ui = app_state.get("ui_toggles", {}) or {}
            show_flags = bool(ui.get("show_flags", True))
            if flags_bits and show_flags:
                html_parts.append(
                    "".join(
                        [
                            f"<span class='pqa-subtle' style='display:inline-block;padding:2px 6px;margin:2px;border-radius:10px'>{html.escape(flag)}</span>"
                            for flag in flags_bits
                        ]
                    )
                )
            html_parts.append(f"<small>{snippet}</small>")
            html_parts.append("</div>")
        except Exception as e:
            logger.warning(f"Error formatting context {i}: {e}")
            html_parts.append(f"<div>Source {i}: [Error formatting source]</div>")

    html_parts.append("</div>")
    return "".join(html_parts)


def format_metadata_html(metadata: dict) -> str:
    """Format metadata as HTML."""
    html_parts = ["<div class='pqa-panel' style='font-size:0.9em;'>"]
    html_parts.append("<h5>Processing Information:</h5>")
    html_parts.append(
        f"<strong>Processing Time:</strong> {metadata.get('processing_time', 0):.2f} seconds<br>"
    )
    html_parts.append(
        f"<strong>Documents Searched:</strong> {metadata.get('documents_searched', 0)}<br>"
    )
    html_parts.append(
        f"<strong>Evidence Sources:</strong> {metadata.get('evidence_sources', 0)}<br>"
    )
    html_parts.append(
        f"<strong>Confidence:</strong> {metadata.get('confidence', 0):.1%}"
    )
    html_parts.append("</div>")
    return "".join(html_parts)


def build_intelligence_html(answer: str, contexts: List) -> str:
    """Generate a research-intelligence panel: contradictions, insights, evidence summary.
    Heuristic-only (local) to avoid extra LLM calls.
    """
    try:
        # Prepare simple per-doc aggregation
        by_doc: Dict[str, List[str]] = {}
        doc_years: Dict[str, int] = {}
        doc_flags: Dict[str, List[str]] = {}

        def _extract_year(s: str) -> int | None:
            try:
                m = re.search(r"\b(20\d{2}|19\d{2})\b", s)
                if m:
                    y = int(m.group(1))
                    if 1900 <= y <= 2100:
                        return y
            except Exception:
                return None
            return None

        def _is_preprint(s: str) -> bool:
            s_low = s.lower()
            return any(
                k in s_low for k in ["arxiv", "biorxiv", "medrxiv", "preprint"]
            )  # heuristic

        def _is_retracted(s: str) -> bool:
            return "retract" in s.lower()

        for c in contexts or []:
            try:
                doc = getattr(getattr(c, "text", object()), "doc", None)
                doc_title = None
                if doc is not None:
                    doc_title = (
                        getattr(doc, "formatted_citation", None)
                        or getattr(doc, "title", None)
                        or getattr(doc, "docname", None)
                    )
                if not doc_title:
                    doc_title = "Unknown source"
                txt = ""
                if hasattr(c, "text"):
                    t = getattr(c.text, "text", None)
                    txt = (
                        t
                        if isinstance(t, str)
                        else (str(c.text) if c.text is not None else "")
                    )
                else:
                    txt = str(c)
                by_doc.setdefault(doc_title, []).append(txt.lower())
                # Flags and year per doc (first seen wins)
                if doc_title not in doc_years:
                    y = None
                    try:
                        y = _extract_year(doc_title)
                    except Exception:
                        y = None
                    if y is not None:
                        doc_years[doc_title] = y
                # Flags
                flags: List[str] = []
                if _is_retracted(doc_title):
                    flags.append("Retracted?")
                if _is_preprint(doc_title):
                    flags.append("Preprint")
                if flags:
                    doc_flags[doc_title] = list(
                        set(doc_flags.get(doc_title, []) + flags)
                    )
            except Exception:
                continue

        # Detect contradictions by antonym pairs and simple polarity clustering across docs
        antonym_pairs = [
            ("increase", "decrease"),
            ("higher", "lower"),
            ("improves", "worsens"),
            ("upregulated", "downregulated"),
            ("promotes", "inhibits"),
            ("protective", "risk"),
        ]
        conflict_items = []
        # Quick claim extractor: (entity_key, polarity, doc_title)
        claim_map: Dict[str, List[Tuple[int, str, str]]] = {}
        verb_to_pol = {
            "increase": 1,
            "increases": 1,
            "increased": 1,
            "higher": 1,
            "upregulate": 1,
            "upregulated": 1,
            "upregulation": 1,
            "promote": 1,
            "promotes": 1,
            "improve": 1,
            "improves": 1,
            "decrease": -1,
            "decreases": -1,
            "decreased": -1,
            "lower": -1,
            "downregulate": -1,
            "downregulated": -1,
            "downregulation": -1,
            "inhibit": -1,
            "inhibits": -1,
            "worsen": -1,
            "worsens": -1,
        }
        negations = ["no ", "not ", "does not ", "lack of ", "without "]
        docs_list = list(by_doc.items())
        for i in range(len(docs_list)):
            doc_a, texts_a = docs_list[i]
            text_a = "\n".join(texts_a)
            for j in range(i + 1, len(docs_list)):
                doc_b, texts_b = docs_list[j]
                text_b = "\n".join(texts_b)
                for w1, w2 in antonym_pairs:
                    if w1 in text_a and w2 in text_b:
                        conflict_items.append(
                            f"{doc_a} mentions '{w1}', while {doc_b} mentions '{w2}'."
                        )
                    if w2 in text_a and w1 in text_b:
                        conflict_items.append(
                            f"{doc_a} mentions '{w2}', while {doc_b} mentions '{w1}'."
                        )

        # Extract simple claims per sentence and cluster by entity phrase
        try:
            for doc_title, texts in by_doc.items():
                for raw in texts:
                    for sent in re.split(r"(?<=[.!?])\s+", raw):
                        s = sent.strip()
                        if not s:
                            continue
                        for verb, pol in verb_to_pol.items():
                            if verb in s:
                                inv = pol
                                s_low = s.lower()
                                if any(neg in s_low for neg in negations):
                                    inv = -pol
                                m = re.search(
                                    rf"{verb}[^a-zA-Z0-9]+(?:(?:in|of|on|for|to)\s+)?([a-z0-9\-_/]+(?:\s+[a-z0-9\-_/]+){{0,4}})",
                                    s_low,
                                )
                                entity = m.group(1) if m else s_low
                                entity = re.sub(r"\s+", " ", entity).strip()
                                entity = entity[:80]
                                claim_map.setdefault(entity, []).append(
                                    (inv, verb, doc_title)
                                )
                                break
            contradiction_clusters: List[str] = []
            for entity, items in claim_map.items():
                pols = {p for p, _v, _d in items}
                if 1 in pols and -1 in pols:
                    # Mixed polarity across docs
                    docs_for_entity = list({d for _p, _v, d in items})
                    contradiction_clusters.append(
                        f"{html.escape(entity)}: mixed polarity across {len(docs_for_entity)} sources"
                    )
            # Add clustered contradictions to list
            for cc in contradiction_clusters[:6]:
                conflict_items.append(cc)
        except Exception:
            pass

        # Key insights: pick sentences from answer if available, else from contexts
        insights = []
        if answer:
            for sent in answer.replace("\n", " ").split(". "):
                s = sent.strip()
                if not s:
                    continue
                if any(
                    k in s.lower()
                    for k in [
                        "suggest",
                        "indicat",
                        "demonstrat",
                        "evidence",
                        "supports",
                        "contradict",
                    ]
                ):
                    insights.append(s)
                if len(insights) >= 5:
                    break
        if not insights:
            # Fallback: pull first snippets from contexts
            for c in contexts[:5]:
                try:
                    t = getattr(getattr(c, "text", object()), "text", None)
                    snippet = t if isinstance(t, str) else (str(getattr(c, "text", "")))
                    if snippet:
                        insights.append(
                            snippet[:160] + ("..." if len(snippet) > 160 else "")
                        )
                except Exception:
                    continue

        # Evidence summary: count by doc
        ev_summary_items = [
            f"{doc}: {len(chunks)} excerpt(s)" for doc, chunks in by_doc.items()
        ]

        # Top evidence with scores
        scored_items = []
        for c in contexts or []:
            try:
                score = getattr(c, "score", None)
                txt_obj = getattr(c, "text", None)
                doc = getattr(txt_obj, "doc", None) if txt_obj is not None else None
                title = None
                citation = None
                if doc is not None:
                    citation = getattr(doc, "formatted_citation", None)
                    title = getattr(doc, "title", None) or getattr(doc, "docname", None)
                page = getattr(c, "page", None)
                raw_text = (
                    getattr(txt_obj, "text", None) if txt_obj is not None else None
                )
                snippet = (
                    raw_text
                    if isinstance(raw_text, str)
                    else (str(txt_obj) if txt_obj is not None else str(c))
                )
                if snippet and len(snippet) > 220:
                    snippet = snippet[:220] + "..."
                display = citation or title or "Unknown source"
                scored_items.append(
                    (
                        score if isinstance(score, (int, float)) else None,
                        display,
                        page,
                        snippet,
                    )
                )
            except Exception:
                continue
        # Sort by score desc, None at end
        scored_items.sort(
            key=lambda x: (-x[0], 1) if isinstance(x[0], (int, float)) else (9999, 1)
        )

        parts = [
            "<div class='pqa-panel'>",
            "<h4>Research Intelligence</h4>",
            "<div><strong>Potential contradictions</strong><ul>",
        ]
        if conflict_items:
            parts.extend([f"<li>{x}</li>" for x in conflict_items[:8]])
        else:
            parts.append("<li>No explicit contradictions detected across sources.</li>")
        parts.append("</ul></div>")

        # Evidence conflicts view (cluster excerpts across docs)
        try:
            ui = app_state.get("ui_toggles", {}) or {}
            if not bool(ui.get("show_conflicts", True)):
                raise RuntimeError("conflicts hidden")
            conflicts_ui: List[str] = []
            for entity, items in list(claim_map.items())[:6]:
                docs_for_entity = list({d for _p, _v, d in items})
                docs_display = ", ".join([html.escape(d) for d in docs_for_entity[:4]])
                conflicts_ui.append(
                    f"<li><small><strong>{html.escape(entity)}</strong>: {len(docs_for_entity)} source(s) [{docs_display}{' …' if len(docs_for_entity) > 4 else ''}]</small></li>"
                )
            parts.append(
                "<div style='margin-top:8px'><strong>Evidence conflicts</strong><ul>"
            )
            if conflicts_ui:
                parts.extend(conflicts_ui)
            else:
                parts.append("<li><small>No clustered conflicts detected.</small></li>")
            parts.append("</ul></div>")
        except Exception:
            pass

        parts.append("<div style='margin-top:8px'><strong>Key insights</strong><ul>")
        if insights:
            parts.extend([f"<li>{x}</li>" for x in insights[:8]])
        else:
            parts.append("<li>No additional insights extracted.</li>")
        parts.append("</ul></div>")

        parts.append(
            "<div style='margin-top:8px'><strong>Evidence summary</strong><ul>"
        )
        if ev_summary_items:
            parts.extend([f"<li>{x}</li>" for x in ev_summary_items])
        parts.append("</ul></div>")

        # Render top evidence table under Research Intelligence
        if scored_items:
            parts.append(
                "<div style='margin-top:8px'><strong>Top evidence (by score)</strong>"
            )
            parts.append("<div style='overflow-x:auto'><table class='pqa-table'>")
            parts.append(
                "<tr><th>Source</th><th>Score</th><th>Page</th><th>Snippet</th></tr>"
            )
            for score, display, page, snippet in scored_items[:10]:
                score_str = f"{score:.3f}" if isinstance(score, (int, float)) else "-"
                page_str = str(int(page)) if isinstance(page, (int, float)) else "-"
                parts.append(
                    f"<tr><td>{display}</td>"
                    f"<td>{score_str}</td>"
                    f"<td>{page_str}</td>"
                    f"<td><small>{snippet}</small></td></tr>"
                )
            parts.append("</table></div></div>")
        # Add scientist-relevant metrics: Quality flags and Recency/Diversity
        try:
            # Quality flags
            flagged = [(doc, flags) for doc, flags in doc_flags.items() if flags]
            parts.append(
                "<div style='margin-top:8px'><strong>Quality flags</strong><ul>"
            )
            if flagged:
                for doc, flags in flagged[:8]:
                    parts.append(
                        f"<li><small>{html.escape(doc)}: {', '.join(flags)}</small></li>"
                    )
            else:
                parts.append("<li><small>No quality flags detected.</small></li>")
            parts.append("</ul></div>")

            # Diversity & recency
            years: List[int] = []
            for y in doc_years.values():
                try:
                    years.append(int(y))
                except Exception:
                    continue
            unique_docs = len(by_doc)
            preprints = sum(1 for f in doc_flags.values() if "Preprint" in f)
            preprint_share = (preprints / unique_docs) if unique_docs > 0 else 0.0
            parts.append(
                "<div style='margin-top:8px'><strong>Diversity & recency</strong>"
            )
            parts.append(
                f"<div><small>Unique papers={unique_docs}, Preprint share={preprint_share:.0%}</small></div>"
            )
            if years:
                y_min = min(years)
                y_max = max(years)
                # Year histogram (compact SVG)
                year_counts: Dict[int, int] = {}
                for y in years:
                    year_counts[y] = year_counts.get(y, 0) + 1
                ys_sorted = list(range(y_min, y_max + 1))
                width, height, pad = 320, 64, 4
                maxc = max(year_counts.values()) if year_counts else 1
                bw = (width - 2 * pad) / max(1, len(ys_sorted))
                bars = []
                for i, y in enumerate(ys_sorted):
                    c = year_counts.get(y, 0)
                    bh = 0 if maxc == 0 else int(((c / maxc) * (height - 2 * pad)))
                    x = pad + int(i * bw)
                    ypix = height - pad - bh
                    bars.append(
                        f"<rect x='{x}' y='{ypix}' width='{max(1, int(bw - 1))}' height='{bh}' fill='#10b981' />"
                    )
                axis = (
                    f"<text x='{pad}' y='{height - 2}' font-size='9' fill='#9ca3af'>{y_min}</text>"
                    f"<text x='{width - pad - 20}' y='{height - 2}' font-size='9' fill='#9ca3af' text-anchor='end'>{y_max}</text>"
                )
                svg = (
                    f"<svg width='{width}' height='{height}' viewBox='0 0 {width} {height}' xmlns='http://www.w3.org/2000/svg'>"
                    + "".join(bars)
                    + axis
                    + "</svg>"
                )
                parts.append("<div style='margin-top:4px'>" + svg + "</div>")
            parts.append("</div>")
        except Exception:
            pass

        parts.append("</div>")
        return "".join(parts)
    except Exception as e:
        logger.warning(f"Failed to build intelligence panel: {e}")
        return "<div class='pqa-subtle'><small class='pqa-muted'>Research Intelligence unavailable.</small></div>"


def build_critique_html(answer: str, contexts: List) -> str:
    """Heuristic critique: flag potential unsupported claims and suggest checks.
    This is a lightweight placeholder; can be upgraded to an LLM call.
    """
    try:
        flags: List[str] = []
        if len(answer.split()) > 250:
            flags.append("Answer is long; consider tighter citation linkage.")
        # Simple unsupported claim heuristic: claim words without numbers/citations nearby
        risky_terms = ["significant", "novel", "first", "proves", "causes"]
        if any(t in answer.lower() for t in risky_terms):
            flags.append(
                "Contains strong language; verify claims against evidence excerpts."
            )
        if not contexts:
            flags.append(
                "No evidence excerpts selected; answer may be under-supported."
            )
        if not flags:
            flags.append("No obvious issues detected.")
        return (
            "<div class='pqa-subtle' style='margin-top:6px'>"
            + "<ul>"
            + "".join([f"<li><small>{html.escape(x)}</small></li>" for x in flags])
            + "</ul>"
            + "</div>"
        )
    except Exception:
        return "<div class='pqa-subtle'><small class='pqa-muted'>Critique unavailable.</small></div>"


def _render_markdown_inline(text: str) -> str:
    """Render a minimal subset of Markdown to HTML for inline use.

    Supports: **bold**, *italic*, `code`, and [text](https://url) links.
    Other HTML is escaped for safety.
    """
    try:
        s = html.escape(text)
        # Links first
        s = re.sub(
            r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
            r"<a href=\"\\2\" target=\"_blank\" rel=\"noopener noreferrer\">\\1</a>",
            s,
        )
        # Bold
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\\1</strong>", s)
        # Italic (avoid bold sequences)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\\1</em>", s)
        # Inline code
        s = re.sub(r"`([^`]+)`", r"<code>\\1</code>", s)
        return s
    except Exception:
        return html.escape(text)


def _render_filters_inline(ri: Any) -> str:
    try:
        if not isinstance(ri, dict):
            return ""
        filters = ri.get("filters")
        if not isinstance(filters, dict):
            return ""
        parts: List[str] = []
        yrs = filters.get("years")
        if isinstance(yrs, (list, tuple)) and len(yrs) == 2:
            parts.append(f"years {yrs[0]}-{yrs[1]}")
        venues = filters.get("venues")
        if isinstance(venues, list) and venues:
            parts.append("venues " + ", ".join(list(map(str, venues[:3]))))
        fields = filters.get("fields")
        if isinstance(fields, list) and fields:
            parts.append("fields " + ", ".join(list(map(str, fields[:3]))))
        if not parts:
            return ""
        bias = " (bias applied)" if ri.get("bias_applied") else ""
        return f"<div><small class='pqa-muted'>Filters: {', '.join(parts)}{bias}</small></div>"
    except Exception:
        return ""


async def build_llm_or_heuristic_critique_html(
    question: str, answer: str, contexts: List, settings: Settings
) -> str:
    """Attempt an LLM-based critique via OpenRouter when configured; otherwise fallback.

    Runs any network LLM call on the dedicated background loop to avoid event-loop conflicts.
    """
    try:
        model_name = str(getattr(settings, "llm", "") or "").strip()
        if model_name:
            try:
                import litellm

                # Build concise evidence bullets for the model
                evidence_lines: List[str] = []
                for c in (contexts or [])[:10]:
                    try:
                        txt_obj = getattr(c, "text", None)
                        doc = (
                            getattr(txt_obj, "doc", None)
                            if txt_obj is not None
                            else None
                        )
                        title = None
                        citation = None
                        if doc is not None:
                            citation = getattr(doc, "formatted_citation", None)
                            title = getattr(doc, "title", None) or getattr(
                                doc, "docname", None
                            )
                        page = getattr(c, "page", None)
                        raw_text = (
                            getattr(txt_obj, "text", None)
                            if txt_obj is not None
                            else None
                        )
                        snippet = (
                            raw_text
                            if isinstance(raw_text, str)
                            else (str(txt_obj) if txt_obj is not None else str(c))
                        )
                        if snippet and len(snippet) > 240:
                            snippet = snippet[:240] + "..."
                        display = citation or title or "Unknown source"
                        pg = f" p.{int(page)}" if isinstance(page, (int, float)) else ""
                        evidence_lines.append(f"- {display}{pg}: {snippet}")
                    except Exception:
                        continue

                messages: List[Dict[str, str]] = [
                    {
                        "role": "system",
                        "content": (
                            "You are a scientific QA auditor. Provide a brief, critical assessment of the answer's support. "
                            "Flag unsupported or overconfident claims, missing citations, and contradictory evidence. "
                            "Be concise and actionable. Return 3-6 bullet points max."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Question:\n{question}\n\n"
                            f"Answer:\n{answer}\n\n"
                            "Evidence excerpts (doc/page: snippet):\n"
                            + "\n".join(evidence_lines)
                        ),
                    },
                ]

                def _extract_content(resp: Any) -> str:
                    try:
                        choices = getattr(resp, "choices", None)
                        if isinstance(choices, list) and choices:
                            choice0 = choices[0]
                            message = getattr(choice0, "message", None)
                            if isinstance(message, dict):
                                c = message.get("content")
                                if isinstance(c, str):
                                    return c
                            c2 = getattr(message, "content", None)
                            if isinstance(c2, str):
                                return c2
                        content_attr = getattr(resp, "content", None)
                        if isinstance(content_attr, str):
                            return content_attr
                    except Exception:
                        pass
                    return ""

                async def _go() -> str:
                    kwargs: Dict[str, Any] = {
                        "model": model_name,
                        "messages": messages,
                        "timeout": 20,
                    }
                    # Include OpenRouter API key if applicable; other providers use their own env keys
                    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
                    if api_key and model_name.startswith("openrouter/"):
                        kwargs["api_key"] = api_key
                    resp = await litellm.acompletion(**kwargs)
                    return _extract_content(resp)

                _ensure_query_loop()
                fut = asyncio.run_coroutine_threadsafe(_go(), app_state["query_loop"])
                content = await asyncio.to_thread(fut.result, timeout=45)
                if isinstance(content, str) and content.strip():
                    # Normalize numbering (e.g., "\\1 foo" -> "1. foo") and detect ordered list
                    raw_lines = [
                        ln.strip() for ln in content.splitlines() if ln.strip()
                    ]
                    norm_lines: List[str] = []
                    numbered = 0
                    for ln in raw_lines:
                        ln2 = re.sub(r"^\\(\d+)\s+", r"\1. ", ln)
                        if re.match(r"^(?:\d+\.|\d+\)|\d+\s+)", ln2):
                            numbered += 1
                        ln2 = ln2.lstrip("-*").strip()
                        norm_lines.append(ln2)
                    use_ol = numbered >= max(1, int(0.5 * len(norm_lines)))
                    tag_open = "<ol>" if use_ol else "<ul>"
                    tag_close = "</ol>" if use_ol else "</ul>"
                    items_html: List[str] = []
                    for ln in norm_lines[:6]:
                        items_html.append(
                            f"<li><small>{_render_markdown_inline(ln)}</small></li>"
                        )
                    if items_html:
                        return (
                            "<div class='pqa-subtle' style='margin-top:6px'>"
                            + tag_open
                            + "".join(items_html)
                            + tag_close
                            + "</div>"
                        )
            except Exception:
                pass

        # Fallback to heuristic critique
        return build_critique_html(answer, contexts)
    except Exception:
        return "<div class='pqa-subtle'><small class='pqa-muted'>Critique unavailable.</small></div>"


async def llm_decompose_query(question: str, settings: Settings) -> Dict[str, Any]:
    """Use the configured LLM to rewrite the query and produce lightweight filters.

    Returns a dict: {"rewritten": str, "filters": {"years": [start, end], "venues": [..], "fields": [..]}}
    """
    try:
        import litellm

        model_name = str(getattr(settings, "llm", "") or "").strip()
        if not model_name:
            return {"rewritten": question, "filters": {}}

        system = (
            "You are a query rewriting assistant for scientific literature retrieval. "
            "Rewrite the user's question to be concise and retrieval-friendly. "
            "Also propose optional filters as a JSON object with: years [start,end], venues [strings], fields [strings]. "
            "If unknown, use null or empty arrays. Respond with JSON only."
        )
        user = (
            "Question: " + question + "\n\n"
            "Return strictly this JSON schema: "
            '{"rewritten": string, "filters": {"years": [number, number] | null, "venues": string[], "fields": string[]}}'
        )
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        async def _go() -> Any:
            kwargs: Dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                "timeout": 20,
            }
            api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
            if api_key and model_name.startswith("openrouter/"):
                kwargs["api_key"] = api_key
            return await litellm.acompletion(**kwargs)

        _ensure_query_loop()
        fut = asyncio.run_coroutine_threadsafe(_go(), app_state["query_loop"])
        resp = fut.result(timeout=45)

        def _extract(resp_obj: Any) -> str:
            try:
                choices = getattr(resp_obj, "choices", None)
                if isinstance(choices, list) and choices:
                    m = getattr(choices[0], "message", None)
                    if isinstance(m, dict):
                        mc = m.get("content")
                        if isinstance(mc, str):
                            return mc
                    c2 = getattr(m, "content", None)
                    if isinstance(c2, str):
                        return c2
                c3 = getattr(resp_obj, "content", None)
                if isinstance(c3, str):
                    return c3
            except Exception:
                pass
            return ""

        content_res = _extract(resp)
        content = content_res if isinstance(content_res, str) else ""

        # Try to parse JSON from the content (strip code fences if present)
        txt = content.strip()
        if txt.startswith("```"):
            # remove leading/trailing fences
            try:
                txt = re.sub(r"^```[a-zA-Z0-9]*\n?|```$", "", txt).strip()
            except Exception:
                pass
        data: Dict[str, Any]
        try:
            data = json.loads(txt)
        except Exception:
            # attempt to find JSON substring
            try:
                m = re.search(r"\{[\s\S]*\}$", txt)
                if m:
                    data = json.loads(m.group(0))
                else:
                    data = {}
            except Exception:
                data = {}
        rewritten = str(data.get("rewritten") or question)
        filters = data.get("filters") or {}
        # Normalize filters
        norm: Dict[str, Any] = {"venues": [], "fields": []}
        # years
        yrs = filters.get("years") if isinstance(filters, dict) else None
        if isinstance(yrs, (list, tuple)) and len(yrs) == 2:
            try:
                y0 = int(yrs[0])
                y1 = int(yrs[1])
                norm["years"] = [y0, y1]
            except Exception:
                norm["years"] = None
        else:
            norm["years"] = None
        # venues, fields
        for key in ("venues", "fields"):
            val = filters.get(key) if isinstance(filters, dict) else None
            if isinstance(val, list):
                norm[key] = [str(x) for x in val if isinstance(x, (str, int, float))][
                    :10
                ]
            else:
                norm[key] = []
        return {"rewritten": rewritten, "filters": norm}
    except Exception:
        return {"rewritten": question, "filters": {}}


def rewrite_query(question: str, settings: Settings) -> str:
    """Minimal local query rewriter: tighten phrasing and strip boilerplate.
    Placeholder for advanced LLM-based decomposition.
    """
    q = " ".join(question.strip().split())
    # Remove polite fillers
    q = re.sub(r"^(please|kindly)\s+", "", q, flags=re.I)
    # Prefer imperative style
    q = re.sub(r"^(what is|what are)\s+", "summarize ", q, flags=re.I)
    # Trim repeated punctuation
    q = re.sub(r"[?!.]{2,}$", "?", q)
    return q


def clear_all() -> Tuple[str, str, str, str, str, str, str]:
    """Clear all uploaded documents and reset the interface."""
    app_state["uploaded_docs"] = []
    app_state["processing_status"] = ""

    if "status_tracker" in app_state:
        app_state["status_tracker"].clear()
        app_state["status_tracker"].add_status("🧹 All documents and data cleared")

    logger.info("Cleared all documents and reset interface")
    return "", "", "", "", "", "", ""


# Initialize default settings
try:
    initialize_settings("optimized_ollama")
    logger.info("✅ Initialized with optimized Ollama configuration")
except Exception as e:
    logger.error(f"❌ Failed to initialize settings: {e}")

# Create Gradio interface
with gr.Blocks(title="Paper-QA UI", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📚 Paper-QA UI")
    gr.Markdown("Upload PDF documents and ask questions using local Ollama models.")
    gr.HTML(
        """
        <style>
        .pqa-panel { background: #ffffff; color: #111827; padding: 12px; border-radius: 6px; }
        .pqa-subtle { background: #f3f4f6; color: inherit; padding: 10px; border-radius: 5px; }
        .pqa-muted { color: #6b7280; }
        .pqa-table { width: 100%; border-collapse: collapse; }
        .pqa-table th, .pqa-table td { padding: 6px; border-bottom: 1px solid #e5e7eb; text-align: left; }
        /* Chevron step badges */
        .pqa-steps { display: flex; gap: 6px; align-items: center; margin: 6px 0; flex-wrap: wrap; }
        .pqa-step { position: relative; display: inline-block; background: #e5e7eb; color: #111827; padding: 6px 16px 6px 16px; font-size: 12px; line-height: 1; }
        .pqa-step::before { content: ""; position: absolute; top: 0; left: -10px; width: 0; height: 0; border-top: 12px solid transparent; border-bottom: 12px solid transparent; border-right: 10px solid #e5e7eb; }
        .pqa-step::after { content: ""; position: absolute; top: 0; right: -10px; width: 0; height: 0; border-top: 12px solid transparent; border-bottom: 12px solid transparent; border-left: 10px solid #e5e7eb; }
        .pqa-step.done { background: #10b981; color: #ffffff; }
        .pqa-step.done::after { border-left-color: #10b981; }
        .pqa-step.done::before { border-right-color: #10b981; }
        .pqa-step:first-child::before { display: none; }
        /* Indeterminate progress bar */
        .pqa-bar { height: 10px; border-radius: 6px; overflow: hidden; position: relative; }
        .pqa-bar-fill { height: 100%; background: #3b82f6; }
        .pqa-bar-indet { background-image: linear-gradient(45deg, rgba(255,255,255,0.15) 25%, transparent 25%, transparent 50%, rgba(255,255,255,0.15) 50%, rgba(255,255,255,0.15) 75%, transparent 75%, transparent); background-size: 20px 20px; animation: pqa-stripes 1s linear infinite; }
        @keyframes pqa-stripes { 0% { background-position: 0 0; } 100% { background-position: 40px 0; } }
        @media (prefers-color-scheme: dark) {
          .pqa-panel { background: #1f2937; color: #e5e7eb; }
          .pqa-subtle { background: #111827; color: #e5e7eb; }
          .pqa-muted { color: #9ca3af; }
          .pqa-table th, .pqa-table td { border-bottom-color: #374151; }
          .pqa-step { background: #374151; color: #e5e7eb; }
          .pqa-step::after { border-left-color: #374151; }
          .pqa-step::before { border-right-color: #374151; }
          .pqa-step.done { background: #059669; color: #ffffff; }
          .pqa-step.done::after { border-left-color: #059669; }
          .pqa-step.done::before { border-right-color: #059669; }
        }
        </style>
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📁 Document Upload")
            file_upload = gr.File(
                file_count="multiple", file_types=[".pdf"], label="Upload PDF Documents"
            )
            upload_status = gr.Textbox(
                label="Upload & Processing Status", interactive=False
            )

            gr.Markdown("### ⚙️ Configuration")

            def _on_config_change(cfg: str) -> str:
                app_state["settings"] = initialize_settings(cfg)
                return f"Configuration set to: {cfg}"

            config_dropdown = gr.Dropdown(
                choices=[
                    "optimized_ollama",
                    "openrouter_ollama",
                    "ollama",
                    "clinical_trials",
                ],
                value="optimized_ollama",
                label="Select Configuration",
                info="Choose your preferred model configuration",
            )
            cfg_status = gr.Markdown(visible=False)

            # Critique toggle (moved here under configuration)
            gr.Markdown(
                "<small class='pqa-muted'>Enable a quick post‑answer sanity check to flag potentially unsupported or overly strong claims. This does not change the answer.</small>"
            )
            critique_toggle = gr.Checkbox(
                label="Run Critique",
                value=False,
                info="Adds a brief critique after the answer (no answer change)",
            )

            gr.Markdown("### 🔧 Query Options")
            rewrite_toggle = gr.Checkbox(
                label="Rewrite query",
                value=False,
                info="Rephrase your question for retrieval; shows original above progress",
            )
            use_llm_rewrite_toggle = gr.Checkbox(
                label="Use LLM rewrite",
                value=False,
                info="Apply LLM-based decomposition (years/venues/fields)",
            )
            bias_retrieval_toggle = gr.Checkbox(
                label="Bias retrieval using filters",
                value=False,
                info="Append extracted filters to the rewritten query",
            )

            gr.Markdown("### 🧪 Evidence Curation")
            score_cutoff_slider = gr.Slider(
                minimum=0.0,
                maximum=1.0,
                step=0.01,
                value=0.0,
                label="Relevance score cutoff",
                info="Discard evidence below this score",
            )
            per_doc_cap_number = gr.Number(
                value=0,
                label="Per-document evidence cap",
                info="0 = unlimited; limit evidence excerpts per source",
            )
            max_sources_number = gr.Number(
                value=0,
                label="Max sources included",
                info="0 = default; hard cap on sources in answer",
            )

            gr.Markdown("### ⚙️ Display Toggles")
            show_flags_toggle = gr.Checkbox(
                label="Show source flags (Preprint/Retracted?)",
                value=True,
                info="Toggle visibility of source quality badges",
            )
            show_conflicts_toggle = gr.Checkbox(
                label="Show evidence conflicts",
                value=True,
                info="Toggle the clustered conflicts view",
            )

            gr.Markdown("### 🧹 Actions")
            clear_button = gr.Button("🗑️ Clear All", variant="secondary")

            gr.Markdown("### 📦 Export")
            export_json_btn = gr.DownloadButton("⬇️ Export JSON", variant="secondary")
            export_csv_btn = gr.DownloadButton("⬇️ Export CSV", variant="secondary")
            export_trace_btn = gr.DownloadButton(
                "⬇️ Export Trace (JSONL)", variant="secondary"
            )
            export_bundle_btn = gr.DownloadButton(
                "⬇️ Export Bundle (ZIP)", variant="secondary"
            )

        with gr.Column(scale=2):
            gr.Markdown("### ❓ Ask Questions")
            question_input = gr.Textbox(
                label="Enter your question",
                placeholder="What is this paper about?",
                lines=3,
            )

            with gr.Row():
                ask_button = gr.Button("🤖 Ask Question", variant="primary", size="lg")

            # Status display (hidden for now)
            status_display = gr.HTML(label="Processing Status", visible=False)

            gr.Markdown("### 🔎 Live Analysis Progress")
            inline_analysis = gr.HTML(
                label="Analysis", show_label=False, elem_id="pqa-inline-analysis"
            )
            # Ensure Analysis area has minimum height via CSS
            gr.HTML(
                "<style>#pqa-inline-analysis { min-height: 300px; }</style>",
                show_label=False,
            )

            gr.Markdown("### 📝 Answer")
            answer_anchor = gr.HTML(
                "<div id='pqa-answer-anchor'></div>", show_label=False
            )
            answer_display = gr.Markdown(label="Answer")

            gr.Markdown("### 📚 Sources")
            sources_display = gr.HTML(label="Evidence Sources")

            gr.Markdown("### 🧠 Research Intelligence")
            intelligence_display = gr.HTML(label="Research Intelligence")

            gr.Markdown("### 📊 Metadata")
            metadata_display = gr.HTML(label="Processing Information")

            error_display = gr.Textbox(label="Errors", interactive=False, visible=False)

    # Removed separate Analysis Progress tab; progress now streams inline below the question

    # Event handlers - automatically process documents on upload
    def _pre_upload_disable() -> Any:
        return gr.update(value="⏳ Wait…", interactive=False)

    def _post_upload_enable() -> Any:
        return gr.update(value="🤖 Ask Question", interactive=True)

    file_upload.change(
        fn=process_uploaded_files,
        inputs=[file_upload],
        outputs=[upload_status, error_display],
        preprocess=False,
        postprocess=False,
    )

    # Disable Ask during uploads; enable after status updates
    file_upload.change(fn=_pre_upload_disable, outputs=[ask_button])
    upload_status.change(fn=_post_upload_enable, outputs=[ask_button])

    def _enable_ask(is_ready: bool) -> Any:
        return gr.update(interactive=bool(is_ready))

    config_dropdown.change(
        fn=_on_config_change, inputs=[config_dropdown], outputs=[cfg_status]
    )

    # Export helpers
    def _ensure_exports_dir() -> Path:
        p = Path("./exports")
        p.mkdir(exist_ok=True)
        return p

    def export_json() -> str:
        data = app_state.get("session_data") or {}
        # include trace if present
        trace = app_state.get("session_trace") or []
        if trace:
            data = {**data, "trace": trace}
        outdir = _ensure_exports_dir()
        fname = f"session_{int(time.time())}.json"
        fpath = outdir / fname
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(fpath)

    def export_csv() -> str:
        data = app_state.get("session_data") or {}
        contexts = data.get("contexts") or []
        outdir = _ensure_exports_dir()
        fname = f"contexts_{int(time.time())}.csv"
        fpath = outdir / fname
        with open(fpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["doc", "page", "score", "text"])
            for c in contexts:
                writer.writerow(
                    [
                        c.get("doc"),
                        c.get("page"),
                        c.get("score"),
                        (c.get("text") or "").replace("\n", " ")[:4000],
                    ]
                )
        return str(fpath)

    def export_trace() -> str:
        trace = app_state.get("session_trace") or []
        outdir = _ensure_exports_dir()
        fname = f"trace_{int(time.time())}.jsonl"
        fpath = outdir / fname
        with open(fpath, "w", encoding="utf-8") as f:
            for ev in trace:
                f.write(json.dumps(ev, ensure_ascii=False))
                f.write("\n")
        return str(fpath)

    def export_bundle() -> str:
        outdir = _ensure_exports_dir()
        ts = int(time.time())
        json_path = Path(export_json())
        csv_path = Path(export_csv())
        trace_path = Path(export_trace())
        zip_path = outdir / f"bundle_{ts}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(json_path, arcname=json_path.name)
            zf.write(csv_path, arcname=csv_path.name)
            zf.write(trace_path, arcname=trace_path.name)
        return str(zip_path)

    ask_button.click(
        fn=ask_with_progress,
        inputs=[
            question_input,
            config_dropdown,
            critique_toggle,
            rewrite_toggle,
            use_llm_rewrite_toggle,
            bias_retrieval_toggle,
            score_cutoff_slider,
            per_doc_cap_number,
            max_sources_number,
            show_flags_toggle,
            show_conflicts_toggle,
        ],
        outputs=[
            inline_analysis,
            answer_display,
            sources_display,
            metadata_display,
            intelligence_display,
            error_display,
            status_display,
            ask_button,
        ],
    )

    question_input.submit(
        fn=ask_with_progress,
        inputs=[
            question_input,
            config_dropdown,
            critique_toggle,
            rewrite_toggle,
            use_llm_rewrite_toggle,
            bias_retrieval_toggle,
            score_cutoff_slider,
            per_doc_cap_number,
            max_sources_number,
            show_flags_toggle,
            show_conflicts_toggle,
        ],
        outputs=[
            inline_analysis,
            answer_display,
            sources_display,
            metadata_display,
            intelligence_display,
            error_display,
            status_display,
            ask_button,
        ],
    )

    clear_button.click(
        fn=clear_all,
        outputs=[
            inline_analysis,
            answer_display,
            sources_display,
            metadata_display,
            intelligence_display,
            error_display,
            status_display,
        ],
    )

    # Wire export buttons
    export_json_btn.click(fn=export_json, outputs=[export_json_btn])
    export_csv_btn.click(fn=export_csv, outputs=[export_csv_btn])
    export_trace_btn.click(fn=export_trace, outputs=[export_trace_btn])
    export_bundle_btn.click(fn=export_bundle, outputs=[export_bundle_btn])

if __name__ == "__main__":
    import os

    # Suppress Gradio version warning
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

    try:
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            quiet=False,
        )
    except OSError as e:
        if "address already in use" in str(e):
            print("❌ Port 7860 is already in use. Try: make kill-server")
        else:
            raise
