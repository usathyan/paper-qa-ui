#!/usr/bin/env python3
"""
Query an existing PaperQA Tantivy index and generate an answer.

Examples:
  python -m src.cli.query_index "What is this paper about?" --index-name my_index --index-dir ./indexes \
      --config optimized_ollama --stream

Notes:
- This script does not add files; it reads from an existing index.
- If the index is empty, it will exit with an error.
"""

import argparse
import asyncio
import logging
import os
import time
from typing import Optional

from paperqa import Docs, Settings
from paperqa.agents.search import get_directory_index

from ..config_manager import ConfigManager


async def build_docs_from_index(settings: Settings, top_n: int) -> Docs:
    """Reconstruct a Docs corpus from a saved Tantivy docs index.

    Reads the saved Docs objects directly from the index storage rather than using search,
    which also avoids the 'answers' index shape.
    """
    # Load existing index (build=False ensures we do not rebuild/sync)
    index = await get_directory_index(settings=settings, build=False)
    count = await index.count
    if count == 0:
        raise RuntimeError("Index is empty. Run the indexer first.")

    combined = Docs()
    embedding_model = settings.get_embedding_model()

    # Iterate through stored objects directly
    index_files = await index.index_files
    loaded = 0
    for i, file_location in enumerate(index_files.keys()):
        if loaded >= top_n:
            break
        try:
            obj = await index.get_saved_object(file_location)
        except FileNotFoundError:
            # Missing stored object on disk; skip this entry
            continue
        # The docs index stores Docs objects; the answers index stores AnswerResponse JSON
        if obj is None:
            continue
        try:
            if isinstance(obj, Docs):
                # Merge all docs/texts from this shard
                for _dockey, d in obj.docs.items():
                    # Select this doc's texts
                    doc_texts = [t for t in obj.texts if t.doc.dockey == d.dockey]
                    if not doc_texts:
                        continue
                    await combined.aadd_texts(
                        texts=doc_texts,
                        doc=d,
                        settings=settings,
                        embedding_model=embedding_model,
                    )
                loaded += 1
            else:
                # Skip non-Docs objects (e.g., AnswerResponse in 'answers' index)
                continue
        except Exception:
            continue

    return combined


async def main_async(
    question: str,
    index_dir: Optional[str],
    index_name: Optional[str],
    config_name: str,
    top_n: int,
    stream: bool,
    verbosity: int,
    log_level: str,
    pre_evidence: bool,
    include_citations: bool,
    evidence_k: Optional[int],
) -> int:
    # Logging
    lvl = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("paperqa").setLevel(
        logging.INFO if verbosity >= 1 else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # Suppress LiteLLM noise and cost warnings
    for _lname in ("litellm", "LiteLLM", "LiteLLM Router", "LiteLLM Proxy"):
        _llog = logging.getLogger(_lname)
        _llog.setLevel(logging.CRITICAL)
        _llog.disabled = True
        _llog.propagate = False
    logging.getLogger("lmi.types").setLevel(logging.ERROR)

    # Avoid unwanted metadata lookups
    os.environ.setdefault("CROSSREF_MAILTO", "")
    os.environ.setdefault("SEMANTIC_SCHOLAR_API_KEY", "")
    os.environ.setdefault("PAPERQA_DISABLE_METADATA", "1")

    # Load settings and point to desired index directory/name
    cfg = ConfigManager().load_config(config_name)
    cfg_agent = cfg.setdefault("agent", {})
    cfg_index = cfg_agent.setdefault("index", {})
    if index_dir:
        cfg_index["index_directory"] = index_dir
    if index_name:
        cfg_index["name"] = index_name
    # We are reusing index; do not sync/remove files in this script
    cfg_index.setdefault("sync_with_paper_directory", False)

    settings = Settings(**cfg)
    # Optional tuning for evidence
    if evidence_k is not None:
        try:
            settings.answer.evidence_k = int(evidence_k)
        except Exception:
            pass
    try:
        settings.answer.evidence_detailed_citations = bool(include_citations)
    except Exception:
        pass

    # Build combined docs from index
    t0 = time.perf_counter()
    try:
        docs = await build_docs_from_index(settings, top_n=top_n)
    except RuntimeError as e:
        print(str(e))
        print(
            "Hint: run the indexer first, e.g., python -m src.cli.index_docs --dir ./papers"
        )
        return 1

    print(f"Loaded {len(docs.docs)} document(s) from index. Querying: {question}")

    # Streaming callback (used for both pre-evidence summaries and final answer)
    callbacks = None
    if stream:

        def _typewriter(chunk: str) -> None:
            print(chunk, end="", flush=True)

        callbacks = [_typewriter]

    # Optionally pre-gather evidence (retrieval + summaries) before answering
    if pre_evidence:
        print("\n[Evidence] Gathering and summarizing relevant contexts...\n")
        pre_session = await docs.aget_evidence(
            question, settings=settings, callbacks=callbacks
        )
        if verbosity:
            print(f"[Evidence] Retrieved {len(pre_session.contexts)} context(s)")

    session = await docs.aquery(question, settings=settings, callbacks=callbacks)

    print("\n=== Answer ===")
    print(session.answer or "No answer generated.")

    if verbosity:
        dt = time.perf_counter() - t0
        logging.getLogger("query_index").info("Completed in %.2fs", dt)

    if session.contexts:
        print("\n=== Sources (top) ===")
        for i, c in enumerate(session.contexts[: min(5, len(session.contexts))], 1):
            try:
                title = getattr(c.text.doc, "title", None) or getattr(
                    c.text.doc, "docname", ""
                )
                citation = getattr(c.text.doc, "formatted_citation", None) or title
                print(f"{i}. {citation}")
            except Exception:
                print(f"{i}. [Unlabeled source]")

    return 0


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Query an existing PaperQA index")
    ap.add_argument("question", help="Question to ask")
    ap.add_argument(
        "--index-dir", help="Index directory root (where named index lives)"
    )
    ap.add_argument("--index-name", help="Name of existing index to use")
    ap.add_argument(
        "--config", default="optimized_ollama", help="Config name in configs/*.json"
    )
    ap.add_argument(
        "--top-n", type=int, default=25, help="How many docs to load from index"
    )
    ap.add_argument(
        "--stream", action="store_true", help="Stream tokens while answering"
    )
    ap.add_argument("--verbosity", type=int, default=1, help="Verbosity (0-3)")
    ap.add_argument("--log-level", default="INFO", help="Python log level")
    ap.add_argument(
        "--pre-evidence",
        action="store_true",
        help="Run retrieval + evidence summaries before answering",
    )
    ap.add_argument(
        "--include-citations",
        action="store_true",
        help="Include detailed citations in evidence contexts",
    )
    ap.add_argument(
        "--evidence-k", type=int, help="Number of evidence texts to retrieve"
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    return asyncio.run(
        main_async(
            question=args.question,
            index_dir=args.index_dir,
            index_name=args.index_name,
            config_name=args.config,
            top_n=args.top_n,
            stream=args.stream,
            verbosity=args.verbosity,
            log_level=args.log_level,
            pre_evidence=args.pre_evidence,
            include_citations=args.include_citations,
            evidence_k=args.evidence_k,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
