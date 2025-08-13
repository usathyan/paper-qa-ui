#!/usr/bin/env python3
"""
Query metadata providers directly using PaperQA clients.

Examples:
  python -m src.cli.clients_query --title "Augmenting language models with chemistry tools"
  python -m src.cli.clients_query --doi 10.1038/s42256-024-00832-8 --providers all

Providers:
  crossref, semanticscholar, openalex, unpaywall, journal_quality, retractions, all

Outputs:
  - formatted citation
  - citation count
  - license
  - pdf url (if available)
"""

import argparse
import asyncio
import logging
import os
from typing import Iterable, List, Dict, Any

from paperqa.clients import (
    ALL_CLIENTS,
    DocMetadataClient,
)


NAME_TO_PROVIDER = {
    "crossref": "CrossrefProvider",
    "semanticscholar": "SemanticScholarProvider",
    "openalex": "OpenAlexProvider",
    "unpaywall": "UnpaywallProvider",
    "journal_quality": "JournalQualityPostProcessor",
    "retractions": "RetractionDataPostProcessor",
}


def select_clients(provider_names: Iterable[str]) -> List[type]:
    if not provider_names or any(n.lower() == "all" for n in provider_names):
        return ALL_CLIENTS
    # Import classes from paperqa.clients.* dynamically
    import importlib

    selected = []
    for name in provider_names:
        key = name.lower()
        if key not in NAME_TO_PROVIDER:
            raise ValueError(f"Unknown provider: {name}")
        class_name = NAME_TO_PROVIDER[key]
        # Determine module based on name
        module = "paperqa.clients.client_models"
        if key == "crossref":
            module = "paperqa.clients.crossref"
        elif key == "semanticscholar":
            module = "paperqa.clients.semantic_scholar"
        elif key == "openalex":
            module = "paperqa.clients.openalex"
        elif key == "unpaywall":
            module = "paperqa.clients.unpaywall"
        elif key == "journal_quality":
            module = "paperqa.clients.journal_quality"
        elif key == "retractions":
            module = "paperqa.clients.retractions"
        cls = getattr(importlib.import_module(module), class_name)
        selected.append(cls)
    return selected


async def main_async(
    title: str, doi: str, authors: List[str], providers: List[str], log_level: str
) -> int:
    lvl = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Encourage setting mailto/API keys (but allow empty)
    os.environ.setdefault("CROSSREF_MAILTO", "")

    clients = select_clients(providers)
    client = DocMetadataClient(clients=clients)

    kwargs: Dict[str, Any] = {}
    if doi:
        kwargs["doi"] = doi
    if title:
        kwargs["title"] = title
    if authors:
        # Many client query signatures expect a comma-separated string; coerce safely
        kwargs["authors"] = ", ".join(authors)
    if not kwargs:
        print("Provide at least one of --title/--doi/--authors")
        return 1

    details = await client.query(**kwargs)
    if not details:
        print("No details found.")
        return 1

    print("\n=== Formatted Citation ===")
    print(details.formatted_citation or "(none)")

    print("\n=== Citation Count ===")
    print(getattr(details, "citation_count", None))

    print("\n=== License ===")
    print(getattr(details, "license", None))

    print("\n=== PDF URL ===")
    print(getattr(details, "pdf_url", None))

    return 0


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Query PaperQA metadata clients directly")
    ap.add_argument("--title", default="", help="Title to search for")
    ap.add_argument("--doi", default="", help="DOI to look up")
    ap.add_argument("--authors", nargs="*", default=[], help="Authors (list)")
    ap.add_argument(
        "--providers", nargs="*", default=["all"], help="Providers to use (or 'all')"
    )
    ap.add_argument("--log-level", default="INFO", help="Log level")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    return asyncio.run(
        main_async(args.title, args.doi, args.authors, args.providers, args.log_level)
    )


if __name__ == "__main__":
    raise SystemExit(main())
