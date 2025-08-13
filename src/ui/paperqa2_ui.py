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
from pathlib import Path
from typing import List, Tuple, Any, Dict, Generator
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
            # Handle Gradio file object - extract the actual file path
            if hasattr(file_obj, "name"):
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
                if source_path.resolve() == dest_path.resolve():
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
    question: str, config_name: str = "optimized_ollama"
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
                        aq.put({"type": "phase", "data": {"phase": "summaries", "status": "start"}}, timeout=0.05)
                        aq.put({"type": "phase", "data": {"phase": "answer", "status": "start"}}, timeout=0.05)
                except Exception:
                    pass

                # Query the in-memory Docs corpus on a dedicated long-lived loop
                # Schedule coroutine on the background loop and wait from current loop
                fut = asyncio.run_coroutine_threadsafe(
                    app_state["docs"].aquery(question, settings=settings), qloop
                )
                # Wait in a thread to avoid blocking current event loop
                session = await asyncio.to_thread(fut.result, timeout=600)

                # Emit phase completion events
                try:
                    aq = app_state.get("analysis_queue")
                    if aq is not None:
                        aq.put({"type": "phase", "data": {"phase": "summaries", "status": "end"}}, timeout=0.05)
                        aq.put({"type": "phase", "data": {"phase": "answer", "status": "end"}}, timeout=0.05)
                except Exception:
                    pass

            processing_time = time.time() - start_time
            logger.info(f"Docs.aquery completed in {processing_time:.2f} seconds")

            # Extract answer and contexts from the session
            answer = getattr(session, "answer", "")
            contexts = getattr(session, "contexts", []) or []

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
    question: str, config_name: str = "optimized_ollama"
) -> Tuple[str, str, str, str, str, str, str]:
    """Synchronous wrapper for process_question_async."""
    answer_html, sources_html, metadata_html, intelligence_html, error_msg = (
        asyncio.run(process_question_async(question, config_name))
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
    question: str, config_name: str = "optimized_ollama"
) -> Generator[Tuple[str, str, str, str, str, str, str], None, None]:
    """Stream pre-evidence progress inline, then yield final answer outputs.

    Output tuple order:
    (analysis_progress_html, answer_html, sources_html, metadata_html, intelligence_html, error_msg, status_html)
    """
    panel_last = ""
    try:
        for panel_html in stream_analysis_progress(question, config_name):
            panel_last = panel_html
            status_html = (
                app_state["status_tracker"].get_status_html()
                if "status_tracker" in app_state and app_state["status_tracker"]
                else ""
            )
            yield (panel_html, "", "", "", "", "", status_html)
    except Exception as e:
        err_panel = (
            f"<div style='color:#b00'>Pre-evidence error: {html.escape(str(e))}</div>"
        )
        panel_last = err_panel
        yield (err_panel, "", "", "", "", "", "")

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
        ) = process_question(question, config_name)

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
        yield (panel_last + badges + synth_block, "", "", "", "", "", "")
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
    question: str, config_name: str = "optimized_ollama"
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
    embed_latency_s: float | None = None
    # Controls snapshot
    try:
        cutoff = getattr(getattr(app_state["settings"], "answer", object()), "evidence_relevance_score_cutoff", None)
    except Exception:
        cutoff = None
    try:
        get_if_none = bool(getattr(getattr(app_state["settings"], "answer", object()), "get_evidence_if_no_contexts", False))
    except Exception:
        get_if_none = False
    try:
        group_by_q = bool(getattr(getattr(app_state["settings"], "answer", object()), "group_contexts_by_question", False))
    except Exception:
        group_by_q = False
    try:
        filter_extra_bg = bool(getattr(getattr(app_state["settings"], "answer", object()), "answer_filter_extra_background", False))
    except Exception:
        filter_extra_bg = False
    try:
        max_sources = int(getattr(getattr(app_state["settings"], "answer", object()), "answer_max_sources", 10))
    except Exception:
        max_sources = 10
    try:
        max_attempts = int(getattr(getattr(app_state["settings"], "answer", object()), "max_answer_attempts", 1))
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
            "<div class='pqa-panel'>",
            "<style>@keyframes pqa-spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}} .pqa-spinner{display:inline-block;width:14px;height:14px;border:2px solid #9ca3af;border-top-color:#3b82f6;border-radius:50%;animation:pqa-spin 0.8s linear infinite;margin-right:6px}</style>",
            (
                "<div style='display:flex;align-items:center;gap:6px'>"
                + ("<span class='pqa-spinner'></span>" if running else "")
                + "<strong>Analysis Progress</strong>"
                + f" <small class='pqa-muted'>({elapsed:.1f}s)</small></div>"
            ),
            (
                "<div style='margin:6px 0'>"
                + (
                    "<span style='display:inline-block;background:#10b981;color:white;border-radius:10px;padding:2px 8px;font-size:12px;margin-right:6px'>Retrieval✓</span>"
                    if retrieval_done
                    else "<span class='pqa-subtle' style='border-radius:10px;padding:2px 8px;font-size:12px;margin-right:6px'>Retrieval</span>"
                )
                + "<span class='pqa-subtle' style='border-radius:10px;padding:2px 8px;font-size:12px;margin-right:6px'>Summaries</span>"
                + "<span class='pqa-subtle' style='border-radius:10px;padding:2px 8px;font-size:12px;margin-right:6px'>Answer</span>"
                + "</div>"
            ),
            (
                f"<div class='pqa-subtle' style='height:10px; border-radius:6px; overflow:hidden'><div style='height:100%; width:{pct}%; background:#3b82f6'></div></div>"
                f"<div style='margin-top:4px'><small class='pqa-muted'>{contexts_selected}/{ev_k} contexts</small></div>"
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
                f"<li><small>Query embedding & retrieval: embed_latency={embed_latency_s:.2f}s, candidate_count=N/A, mmr_lambda=N/A</small></li>"
                if isinstance(embed_latency_s, (int, float))
                else "<li><small>Query embedding & retrieval: (running...)</small></li>"
            ),
            # Evidence selection
            (
                f"<li><small>Evidence selection: contexts_selected={contexts_selected}, evidence_k={ev_k}, cutoff={cutoff}, get_if_none={get_if_none}</small></li>"
            ),
            # Summaries
            (
                f"<li><small>Summaries synthesis: enabled={group_by_q or filter_extra_bg}, metrics=N/A</small></li>"
            ),
            # Prompt building
            (
                f"<li><small>Prompt building: answer_max_sources={max_sources}, sources_included=N/A, prompt_length=N/A</small></li>"
            ),
            # Answer generation
            (
                f"<li><small>Answer generation: max_attempts={max_attempts}, retries=N/A, tokens=N/A</small></li>"
            ),
            # Post-processing
            (
                "<li><small>Post-processing: sources_used=N/A, final_contexts=N/A, postproc_time=N/A</small></li>"
            ),
            "</ul>",
            "</div>",
        ]
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
                logs.append(str(evt.get("data", "")).strip())
            elif isinstance(evt, dict) and evt.get("type") == "phase":
                data = evt.get("data", {}) or {}
                if data.get("phase") == "retrieval" and data.get("status") == "end":
                    retrieval_done = True
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
    """Format the answer as HTML."""
    if not answer:
        return "<div class='pqa-subtle' style='text-align: center;'><small class='pqa-muted'>No answer generated.</small></div>"

    # Simple formatting - you can enhance this
    formatted_answer = answer.replace("\n", "<br>")
    return f"<div class='pqa-panel' style='padding: 15px;'>{formatted_answer}</div>"


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
            snippet = text_str if isinstance(text_str, str) else str(text_str)
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."

            meta_bits = []
            if isinstance(page, (int, float)):
                meta_bits.append(f"p. {int(page)}")
            if isinstance(score, (int, float)):
                meta_bits.append(f"score={score:.3f}")
            meta = (
                f" <small class='pqa-muted'>({' | '.join(meta_bits)})</small>"
                if meta_bits
                else ""
            )

            html_parts.append(
                "<div class='pqa-subtle' style='margin-bottom:10px; padding:10px; border-left: 3px solid #3b82f6;'>"
            )
            html_parts.append(f"<strong>{display_name}</strong>{meta}<br>")
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
            except Exception:
                continue

        # Detect simple contradictions by antonym pairs across different docs
        antonym_pairs = [
            ("increase", "decrease"),
            ("higher", "lower"),
            ("improves", "worsens"),
            ("upregulated", "downregulated"),
            ("promotes", "inhibits"),
            ("protective", "risk"),
        ]
        conflict_items = []
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
        parts.append("</div>")
        return "".join(parts)
    except Exception as e:
        logger.warning(f"Failed to build intelligence panel: {e}")
        return "<div class='pqa-subtle'><small class='pqa-muted'>Research Intelligence unavailable.</small></div>"


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
        @media (prefers-color-scheme: dark) {
          .pqa-panel { background: #1f2937; color: #e5e7eb; }
          .pqa-subtle { background: #111827; color: #e5e7eb; }
          .pqa-muted { color: #9ca3af; }
          .pqa-table th, .pqa-table td { border-bottom-color: #374151; }
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

            gr.Markdown("### 🧹 Actions")
            clear_button = gr.Button("🗑️ Clear All", variant="secondary")

        with gr.Column(scale=2):
            gr.Markdown("### ❓ Ask Questions")
            question_input = gr.Textbox(
                label="Enter your question",
                placeholder="What is this paper about?",
                lines=3,
            )

            with gr.Row():
                ask_button = gr.Button("🤖 Ask Question", variant="primary", size="lg")

            # Status display
            status_display = gr.HTML(label="Processing Status")

            gr.Markdown("### 🔎 Live Analysis Progress")
            inline_analysis = gr.HTML(label="Analysis", show_label=False)

            gr.Markdown("### 📝 Answer")
            answer_anchor = gr.HTML(
                "<div id='pqa-answer-anchor'></div>", show_label=False
            )
            answer_display = gr.HTML(label="Answer")

            gr.Markdown("### 📚 Sources")
            sources_display = gr.HTML(label="Evidence Sources")

            gr.Markdown("### 🧠 Research Intelligence")
            intelligence_display = gr.HTML(label="Research Intelligence")

            gr.Markdown("### 📊 Metadata")
            metadata_display = gr.HTML(label="Processing Information")

            error_display = gr.Textbox(label="Errors", interactive=False, visible=False)

    # Removed separate Analysis Progress tab; progress now streams inline below the question

    # Event handlers - automatically process documents on upload
    file_upload.change(
        fn=process_uploaded_files,
        inputs=[file_upload],
        outputs=[upload_status, error_display],
    )

    ask_button.click(
        fn=ask_with_progress,
        inputs=[question_input, config_dropdown],
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

    question_input.submit(
        fn=ask_with_progress,
        inputs=[question_input, config_dropdown],
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
