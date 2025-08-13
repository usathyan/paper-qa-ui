#!/usr/bin/env python3
"""
Paper-QA Gradio UI with optimized local Ollama support.
Based on insights from GitHub discussions and testing.
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import List, Tuple

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
app_state = {
    "uploaded_docs": [],
    "settings": None,
    "docs": None,
    "status_tracker": None,
    "processing_status": "",
    "query_lock": None,
}

# Disable Gradio analytics
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"


def check_ollama_status() -> bool:
    """Check if Ollama is running and accessible."""
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


class StatusTracker:
    """Simple status tracker for paper-qa operations."""

    def __init__(self):
        self.status_updates = []
        self.current_step = 0

    def add_status(self, status: str):
        """Add a status update."""
        self.status_updates.append(f"{time.strftime('%H:%M:%S')} - {status}")
        logger.info(f"Status: {status}")

    def get_status_html(self) -> str:
        """Get formatted HTML of all status updates."""
        if not self.status_updates:
            return "<div style='text-align: center; color: #666;'>Ready to process questions</div>"

        html_parts = [
            "<div style='max-height: 200px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 5px;'>"
        ]
        html_parts.append("<strong>Processing Status:</strong><br>")
        for i, status in enumerate(
            self.status_updates[-10:], 1
        ):  # Show last 10 updates
            html_parts.append(f"{i}. {status}<br>")
        html_parts.append("</div>")
        return "".join(html_parts)

    def clear(self):
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
        if hasattr(settings, "agent") and hasattr(settings.agent, "tool_names"):
            if "clinical_trials_search" not in settings.agent.tool_names:
                settings.agent.tool_names = DEFAULT_TOOL_NAMES + [
                    "clinical_trials_search"
                ]
        else:
            from paperqa.settings import AgentSettings

            settings.agent = AgentSettings(
                tool_names=DEFAULT_TOOL_NAMES + ["clinical_trials_search"]
            )

        status_tracker = StatusTracker()
        app_state["settings"] = settings
        app_state["status_tracker"] = status_tracker
        logger.info(f"Initialized Settings with config: {config_name}")
        return settings
    except Exception as e:
        logger.error(f"Failed to initialize Settings: {e}")
        raise


async def process_uploaded_files_async(files: List[str]) -> Tuple[str, str]:
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
                    # Use permanent path in papers directory
                    added_name = await app_state["docs"].aadd(
                        str(dest_path), settings=app_state["settings"]
                    )
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
                return "", "", "", "Please enter a question."

            # Check if documents have been uploaded and processed
            if not app_state.get("uploaded_docs"):
                return (
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
                if app_state.get("docs") is None:
                    app_state["docs"] = Docs()
                    for d in app_state.get("uploaded_docs", []):
                        try:
                            await app_state["docs"].aadd(d["path"], settings=settings)
                        except Exception as e:
                            logger.warning(
                                f"Skipping doc that failed to add: {d.get('filename')}: {e}"
                            )

                # Query the in-memory Docs corpus in an isolated event loop (prevents 'Event loop is closed')

                def _blocking_query() -> object:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            app_state["docs"].aquery(question, settings=settings)
                        )
                        # Drain any pending tasks
                        try:
                            pending = [
                                t for t in asyncio.all_tasks(loop) if not t.done()
                            ]
                            if pending:
                                loop.run_until_complete(
                                    asyncio.gather(*pending, return_exceptions=True)
                                )
                        except Exception:
                            pass
                        # Clean up loop executors/generators
                        try:
                            loop.run_until_complete(loop.shutdown_asyncgens())
                            loop.run_until_complete(loop.shutdown_default_executor())
                        except Exception:
                            pass
                        return result
                    finally:
                        try:
                            loop.close()
                        except Exception:
                            pass

                session = await asyncio.get_running_loop().run_in_executor(
                    None, _blocking_query
                )

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
                    import litellm  # type: ignore

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


def format_answer_html(answer: str, contexts: List) -> str:
    """Format the answer as HTML."""
    if not answer:
        return (
            "<div style='color: #666; text-align: center;'>No answer generated.</div>"
        )

    # Simple formatting - you can enhance this
    formatted_answer = answer.replace("\n", "<br>")
    return f"<div style='background: #f8f9fa; padding: 15px; border-radius: 5px;'>{formatted_answer}</div>"


def format_sources_html(contexts: List) -> str:
    """Format the sources as HTML."""
    if not contexts:
        return "<div style='color: #666; text-align: center;'>No sources found.</div>"

    html_parts = ["<div style='max-height: 300px; overflow-y: auto;'>"]
    html_parts.append("<h4>Evidence Sources:</h4>")

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
                f" <small style='color:#666'>({' | '.join(meta_bits)})</small>"
                if meta_bits
                else ""
            )

            html_parts.append(
                "<div style='margin-bottom: 10px; padding: 10px; background: #fff; border-left: 3px solid #007bff;'>"
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
    html_parts = [
        "<div style='background: #e9ecef; padding: 10px; border-radius: 5px; font-size: 0.9em;'>"
    ]
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
        by_doc = {}
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
            "<div style='background:#fff; padding:12px; border-radius:6px;'>",
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

        # Render top evidence table
        if scored_items:
            parts.append(
                "<div style='margin-top:8px'><strong>Top evidence (by score)</strong>"
            )
            parts.append(
                "<div style='overflow-x:auto'><table style='width:100%; border-collapse:collapse'>"
            )
            parts.append(
                "<tr><th style='text-align:left;padding:6px;border-bottom:1px solid #ddd'>Source</th>"
                "<th style='text-align:left;padding:6px;border-bottom:1px solid #ddd'>Score</th>"
                "<th style='text-align:left;padding:6px;border-bottom:1px solid #ddd'>Page</th>"
                "<th style='text-align:left;padding:6px;border-bottom:1px solid #ddd'>Snippet</th></tr>"
            )
            for score, display, page, snippet in scored_items[:10]:
                score_str = f"{score:.3f}" if isinstance(score, (int, float)) else "-"
                page_str = str(int(page)) if isinstance(page, (int, float)) else "-"
                parts.append(
                    f"<tr><td style='padding:6px;border-bottom:1px solid #f0f0f0'>{display}</td>"
                    f"<td style='padding:6px;border-bottom:1px solid #f0f0f0'>{score_str}</td>"
                    f"<td style='padding:6px;border-bottom:1px solid #f0f0f0'>{page_str}</td>"
                    f"<td style='padding:6px;border-bottom:1px solid #f0f0f0'><small>{snippet}</small></td></tr>"
                )
            parts.append("</table></div></div>")
        parts.append("</div>")
        return "".join(parts)
    except Exception as e:
        logger.warning(f"Failed to build intelligence panel: {e}")
        return "<div style='color:#666'>Research Intelligence unavailable.</div>"


def clear_all():
    """Clear all uploaded documents and reset the interface."""
    app_state["uploaded_docs"] = []
    app_state["processing_status"] = ""

    if "status_tracker" in app_state:
        app_state["status_tracker"].clear()
        app_state["status_tracker"].add_status("🧹 All documents and data cleared")

    logger.info("Cleared all documents and reset interface")
    return "", "", "", "", "", ""


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

            gr.Markdown("### 📝 Answer")
            answer_display = gr.HTML(label="Answer")

            gr.Markdown("### 📚 Sources")
            sources_display = gr.HTML(label="Evidence Sources")

            gr.Markdown("### 🧠 Research Intelligence")
            intelligence_display = gr.HTML(label="Research Intelligence")

            gr.Markdown("### 📊 Metadata")
            metadata_display = gr.HTML(label="Processing Information")

            error_display = gr.Textbox(label="Errors", interactive=False, visible=False)

    # Event handlers - automatically process documents on upload
    file_upload.change(
        fn=process_uploaded_files,
        inputs=[file_upload],
        outputs=[upload_status, error_display],
    )

    ask_button.click(
        fn=process_question,
        inputs=[question_input, config_dropdown],
        outputs=[
            answer_display,
            sources_display,
            metadata_display,
            intelligence_display,
            error_display,
            status_display,
            status_display,
        ],
    )

    question_input.submit(
        fn=process_question,
        inputs=[question_input, config_dropdown],
        outputs=[
            answer_display,
            sources_display,
            metadata_display,
            intelligence_display,
            error_display,
            status_display,
            status_display,
        ],
    )

    clear_button.click(
        fn=clear_all,
        outputs=[
            answer_display,
            sources_display,
            metadata_display,
            intelligence_display,
            error_display,
            status_display,
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
