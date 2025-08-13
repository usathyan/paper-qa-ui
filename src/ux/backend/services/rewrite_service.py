from __future__ import annotations

import re
from typing import List, Tuple

from ..schemas import Filters, RewriteRequest, RewriteResponse


_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def _extract_years(text: str) -> List[int]:
    years: List[int] = []
    for m in _YEAR_RE.finditer(text):
        try:
            y = int(m.group(0))
            years.append(y)
        except Exception:
            continue
    # Deduplicate and sort
    return sorted({y for y in years})


def _simple_rewrite(text: str) -> Tuple[str, Filters, bool]:
    # Heuristic rewrite: normalize whitespace and lower superfluous punctuation
    normalized = " ".join(text.split()).strip()
    years = _extract_years(text)
    filters = Filters(years=years or None)
    same = normalized == text.strip()
    return (normalized, filters, same)


def rewrite(req: RewriteRequest) -> RewriteResponse:
    # Stub: LLM-based rewrite can be wired later; heuristic for now
    rewritten, filters, same = _simple_rewrite(req.original)
    return RewriteResponse(rewritten=rewritten, filters=filters, same_as_original=same)
