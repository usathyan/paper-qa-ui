from __future__ import annotations

import re
from typing import Any, List

from ..schemas import CurationSpec, Filters


def apply_curation(session: Any, spec: CurationSpec) -> Any:
    """
    Apply lightweight curation to a PaperQA session object.
    - Enforce per_doc_cap by trimming contexts per doc
    - Note: relevance_cutoff and max_sources are expected to be applied in Settings before query
    """
    try:
        contexts = list(getattr(session, "contexts", []))
        if spec.per_doc_cap:
            seen_per_doc: dict[str, int] = {}
            curated = []
            for ctx in contexts:
                doc = getattr(getattr(ctx, "text", None), "doc", None)
                docname = (
                    getattr(doc, "docname", None) or getattr(doc, "title", None) or ""
                )
                count = seen_per_doc.get(docname, 0)
                if count < spec.per_doc_cap:
                    curated.append(ctx)
                    seen_per_doc[docname] = count + 1
            try:
                setattr(session, "contexts", curated)
            except Exception:
                pass
    except Exception:
        pass
    return session


_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _extract_year_from_citation(citation: str) -> int | None:
    m = _YEAR_RE.search(citation)
    if not m:
        return None
    try:
        return int(m.group(0))
    except Exception:
        return None


def apply_hard_filters(session: Any, filters: Filters) -> Any:
    """
    Enforce hard filters by trimming contexts to those matching filters.
    Heuristics: year from doc.year or citation; venue match via substring on citation;
    fields match via title/snippet substring.
    """
    try:
        contexts: List[Any] = list(getattr(session, "contexts", []))
        if not contexts:
            return session
        years = set(filters.years or [])
        venues = [v.strip().lower() for v in (filters.venues or []) if v.strip()]
        fields = [f.strip().lower() for f in (filters.fields or []) if f.strip()]
        if not years and not venues and not fields:
            return session
        kept: List[Any] = []
        for ctx in contexts:
            doc = getattr(getattr(ctx, "text", None), "doc", None)
            citation = (
                getattr(doc, "formatted_citation", None)
                or getattr(doc, "title", None)
                or getattr(doc, "docname", "")
            )
            citation_l = str(citation).lower()
            title_l = (getattr(doc, "title", "") or "").lower()
            snippet_l = (getattr(getattr(ctx, "text", None), "text", "") or "").lower()
            # Year predicate
            include = True
            if years:
                doc_year = getattr(doc, "year", None)
                if isinstance(doc_year, int):
                    include = doc_year in years
                else:
                    cy = _extract_year_from_citation(str(citation))
                    include = cy in years if cy is not None else False
            # Venue predicate
            if include and venues:
                include = any(v in citation_l for v in venues)
            # Field predicate
            if include and fields:
                include = any(
                    f in title_l or f in snippet_l or f in citation_l for f in fields
                )
            if include:
                kept.append(ctx)
        setattr(session, "contexts", kept)
    except Exception:
        return session
    return session
