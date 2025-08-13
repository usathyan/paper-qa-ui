from __future__ import annotations

from typing import Any

from ..schemas import CurationSpec


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
