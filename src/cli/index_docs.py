#!/usr/bin/env python3
"""
Index documents into PaperQA's Tantivy index without querying.

Examples:
  python -m src.cli.index_docs --dir ./papers --config optimized_ollama
  python -m src.cli.index_docs --dir ./papers --index-dir ./indexes --index-name my_index \
      --recurse --concurrency 2 --config optimized_ollama

Notes:
- By default, this script avoids external metadata calls (Crossref/Semantic Scholar).
- Override with --use-doc-details to enable metadata enrichment during parsing.
"""

import argparse
import asyncio
import logging
import os
from typing import Optional

from paperqa.settings import Settings
from paperqa.agents.search import get_directory_index

from ..config_manager import ConfigManager


async def main_async(
    src_dir: str,
    index_dir: Optional[str],
    index_name: Optional[str],
    config_name: str,
    recurse: bool,
    sync: bool,
    concurrency: Optional[int],
    batch_size: Optional[int],
    use_doc_details: bool,
    log_level: str,
) -> int:
    # Logging
    lvl = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    # Keep PaperQA logs informative
    logging.getLogger("paperqa").setLevel(logging.INFO)
    # Suppress LiteLLM noise entirely
    for _lname in ("litellm", "LiteLLM", "LiteLLM Router", "LiteLLM Proxy"):
        _llog = logging.getLogger(_lname)
        _llog.setLevel(logging.CRITICAL)
        _llog.disabled = True
        _llog.propagate = False

    # Environment hardening unless user opts in to metadata
    if not use_doc_details:
        os.environ.setdefault("CROSSREF_MAILTO", "")
        os.environ.setdefault("SEMANTIC_SCHOLAR_API_KEY", "")
        os.environ.setdefault("PAPERQA_DISABLE_METADATA", "1")

    # Load and override settings
    cfg = ConfigManager().load_config(config_name)
    cfg_agent = cfg.setdefault("agent", {})
    cfg_index = cfg_agent.setdefault("index", {})
    cfg_index["paper_directory"] = src_dir
    if index_dir:
        cfg_index["index_directory"] = index_dir
    if index_name:
        cfg_index["name"] = index_name
    cfg_index["recurse_subdirectories"] = bool(recurse)
    cfg_index["sync_with_paper_directory"] = bool(sync)
    if concurrency is not None:
        cfg_index["concurrency"] = int(concurrency)
    if batch_size is not None:
        cfg_index["batch_size"] = int(batch_size)

    # Parsing options
    cfg.setdefault("parsing", {})["use_doc_details"] = bool(use_doc_details)

    settings = Settings(**cfg)

    # Build (or update) the index
    search_index = await get_directory_index(settings=settings, build=True)
    count = await search_index.count
    print(
        f"Index '{search_index.index_name}' at '{settings.agent.index.index_directory}' now has {count} docs."
    )

    # Persist index files if pending
    await search_index.save_index()
    return 0


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Index local documents into a PaperQA Tantivy index"
    )
    ap.add_argument(
        "--dir",
        required=True,
        help="Source directory of documents (.pdf/.txt/.md/.html)",
    )
    ap.add_argument(
        "--index-dir", help="Destination directory for indexes (defaults to settings)"
    )
    ap.add_argument(
        "--index-name", help="Optional index name (defaults to settings-derived)"
    )
    ap.add_argument(
        "--config", default="optimized_ollama", help="Config name in configs/*.json"
    )
    ap.add_argument(
        "--recurse", action="store_true", help="Recurse into subdirectories"
    )
    ap.add_argument(
        "--sync", action="store_true", help="Sync index with source dir (add/remove)"
    )
    ap.add_argument(
        "--concurrency", type=int, help="Concurrent file processing for indexing"
    )
    ap.add_argument(
        "--batch-size", type=int, help="Save after N files (index writer batch size)"
    )
    ap.add_argument(
        "--use-doc-details",
        action="store_true",
        help="Enable metadata providers for citations/DOIs",
    )
    ap.add_argument(
        "--log-level", default="INFO", help="Log level (DEBUG, INFO, WARNING)"
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    return asyncio.run(
        main_async(
            src_dir=args.dir,
            index_dir=args.index_dir,
            index_name=args.index_name,
            config_name=args.config,
            recurse=args.recurse,
            sync=args.sync,
            concurrency=args.concurrency,
            batch_size=args.batch_size,
            use_doc_details=args.use_doc_details,
            log_level=args.log_level,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
