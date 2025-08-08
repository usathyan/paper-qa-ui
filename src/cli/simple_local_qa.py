#!/usr/bin/env python3
"""
Simple local PaperQA runner using your configured models.
- Loads settings from configs (default: optimized_ollama)
- Disables external metadata lookups
- Adds local docs from ./papers (or provided paths)
- Queries the docs and prints the answer and sources

Usage:
  python -m src.cli.simple_local_qa "Your question here"
  python -m src.cli.simple_local_qa "Your question" --config optimized_ollama --files papers/foo.pdf papers/bar.pdf
"""

import argparse
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import List, Optional

from paperqa import Docs, Settings

# Allow importing local config manager
from ..config_manager import ConfigManager


ALLOWED_SUFFIXES = {".pdf", ".txt", ".md", ".html"}


def find_local_docs(
    default_dir: str = "./papers", explicit_files: Optional[List[str]] = None
) -> List[Path]:
    # If --files was provided (even with zero entries), do NOT scan the default dir
    if explicit_files is not None:
        return [
            Path(p).resolve()
            for p in explicit_files
            if Path(p).suffix.lower() in ALLOWED_SUFFIXES
        ]
    base = Path(default_dir)
    if not base.exists():
        return []
    return [
        p.resolve()
        for p in base.iterdir()
        if p.is_file() and p.suffix.lower() in ALLOWED_SUFFIXES
    ]


async def main_async(
    question: str,
    config_name: str,
    files: Optional[List[str]],
    verbosity: int,
    log_level: str,
    stream: bool,
) -> int:
    # Logging configuration
    lvl = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("paperqa").setLevel(
        logging.INFO if verbosity >= 1 else logging.WARNING
    )
    logging.getLogger("paperqa.agents").setLevel(
        logging.INFO if verbosity >= 2 else logging.WARNING
    )
    # Suppress LiteLLM noise entirely
    logging.getLogger("litellm").setLevel(logging.ERROR)
    for _lname in ("litellm", "LiteLLM", "LiteLLM Router", "LiteLLM Proxy"):
        _llog = logging.getLogger(_lname)
        _llog.setLevel(logging.CRITICAL)
        _llog.disabled = True
        _llog.propagate = False
    # Silence lmi cost calculator warnings like "Could not find cost for model ..."
    logging.getLogger("lmi.types").setLevel(logging.ERROR)
    logging.getLogger("lmi").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    log = logging.getLogger("simple_local_qa")
    # Environment hardening to avoid external metadata calls
    os.environ.setdefault("CROSSREF_MAILTO", "")
    os.environ.setdefault("SEMANTIC_SCHOLAR_API_KEY", "")
    os.environ.setdefault("PAPERQA_DISABLE_METADATA", "1")

    # Load settings from your configs
    cfg = ConfigManager().load_config(config_name)
    # Force offline behavior before creating Settings
    cfg.setdefault("parsing", {})["use_doc_details"] = False
    settings = Settings(**cfg)
    # Extra safety at runtime
    settings.parsing.use_doc_details = False
    settings.verbosity = max(0, min(3, verbosity))
    # Ensure we don't filter away all contexts due to low scores
    try:
        settings.answer.evidence_relevance_score_cutoff = 0
        settings.answer.answer_max_sources = max(5, settings.answer.answer_max_sources)
        settings.answer.evidence_k = max(10, settings.answer.evidence_k)
        settings.answer.get_evidence_if_no_contexts = True
    except Exception:
        pass

    if verbosity:
        log.info("Using config: %s", config_name)
        log.info("LLM: %s | Embedding: %s", settings.llm, settings.embedding)

    # Discover docs
    doc_paths = find_local_docs(explicit_files=files)
    if files is not None and not doc_paths:
        print("No valid files were passed to --files (expected .pdf/.txt/.md/.html).")
        return 1
    if files is None and not doc_paths:
        print(
            "No local documents found. Add PDFs or text files to ./papers or pass --files."
        )
        return 1

    print(f"Adding {len(doc_paths)} document(s) to the corpus...")
    docs = Docs()
    added = 0
    for p in doc_paths:
        try:
            t0 = time.perf_counter()
            if verbosity:
                log.info("Adding %s", p.name)
            name = await docs.aadd(str(p), settings=settings)
            if verbosity:
                log.info("Added %s in %.2fs", p.name, time.perf_counter() - t0)
            if name:
                added += 1
        except Exception as e:
            log.error("Failed to add %s: %s", p.name, e)

    if added == 0:
        print("No documents were added successfully; cannot proceed.")
        return 1

    print(f"Querying with: {question}")
    t0 = time.perf_counter()
    # Optional streaming/typewriter-style callback per chunk
    callbacks = None
    if stream:

        def _typewriter(chunk: str) -> None:
            print(chunk, end="", flush=True)

        callbacks = [_typewriter]

    session = await docs.aquery(question, settings=settings, callbacks=callbacks)
    if verbosity:
        log.info("Query completed in %.2fs", time.perf_counter() - t0)
        try:
            scores = [getattr(c, "score", None) for c in session.contexts]
            non_null = [s for s in scores if s is not None]
            if non_null:
                log.info(
                    "Retrieved %d contexts (score min/mean/max: %.3f/%.3f/%.3f)",
                    len(non_null),
                    min(non_null),
                    sum(non_null) / len(non_null),
                    max(non_null),
                )
            else:
                log.info("Retrieved %d contexts (no scores)", len(session.contexts))
        except Exception:
            pass

    # If streaming, we've already printed the answer progressively
    if stream:
        print("\n\n=== Answer (final) ===")
        print(session.answer or "No answer generated.")
    else:
        print("\n=== Answer ===")
        print(session.answer or "No answer generated.")

    # Print a brief list of sources (if available)
    if session.contexts:
        print("\n=== Sources (top) ===")
        for i, c in enumerate(session.contexts[: min(5, len(session.contexts))], 1):
            try:
                title = getattr(c.text.doc, "title", None) or getattr(
                    c.text.doc, "docname", ""
                )
                citation = getattr(c.text.doc, "formatted_citation", None) or title
                score = getattr(c, "score", None)
                score_str = (
                    f" (score={score:.3f})" if isinstance(score, (int, float)) else ""
                )
                print(f"{i}. {citation}{score_str}")
            except Exception:
                print(f"{i}. [Unlabeled source]")
    else:
        print("\n(no sources found)")

    return 0


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Simple local QA over ./papers using PaperQA"
    )
    ap.add_argument("question", help="Question to ask over local documents")
    ap.add_argument(
        "--config",
        default="optimized_ollama",
        help="Config name in configs/*.json (default: optimized_ollama)",
    )
    ap.add_argument(
        "--files",
        nargs="*",
        help="Optional explicit file paths instead of scanning ./papers",
    )
    ap.add_argument("--verbosity", type=int, default=1, help="PaperQA verbosity (0-3)")
    ap.add_argument(
        "--log-level", default="INFO", help="Python log level (DEBUG, INFO, WARNING)"
    )
    ap.add_argument(
        "--stream",
        action="store_true",
        help="Stream tokens with a typewriter-style callback",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    return asyncio.run(
        main_async(
            args.question,
            args.config,
            args.files,
            args.verbosity,
            args.log_level,
            args.stream,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
