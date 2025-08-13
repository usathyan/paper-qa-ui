from __future__ import annotations

import re
import json
import os
from typing import List, Optional, Tuple

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


def _llm_decompose(original: str) -> Optional[Tuple[str, Filters]]:
    """
    Call LLM via litellm to rewrite and extract filters. Expects JSON-only output.
    Returns (rewritten, Filters) or None on failure.
    """
    try:
        from litellm import completion

        model = os.environ.get(
            "OPENROUTER_MODEL",
            os.environ.get("OPENAI_MODEL", "openrouter/anthropic/claude-3.5-sonnet"),
        )
        system = (
            "You rewrite user questions for literature search. "
            "Return a compact rewritten question optimized for retrieval and a list of filters. "
            "Output strict JSON with keys: rewritten, filters {years, venues, fields}."
        )
        user = (
            "Question: "
            + original
            + '\nRespond only in JSON, no prose. Example: {"rewritten": "...", "filters": {"years": [2021], "venues": ["NeurIPS"], "fields": ["NLP"]}}'
        )
        resp = completion(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        text = resp["choices"][0]["message"]["content"]
        data = json.loads(text)
        rewritten = str(data.get("rewritten") or original).strip()
        f = data.get("filters") or {}
        years = f.get("years") or []
        venues = f.get("venues") or []
        fields = f.get("fields") or []
        filters = Filters(
            years=[
                int(y) for y in years if isinstance(y, (int, str)) and str(y).isdigit()
            ]
            or None,
            venues=[str(v) for v in venues if str(v).strip()] or None,
            fields=[str(t) for t in fields if str(t).strip()] or None,
        )
        return (rewritten, filters)
    except Exception:
        return None


def rewrite(req: RewriteRequest) -> RewriteResponse:
    # Try LLM-based rewrite if enabled
    if req.use_llm:
        llm = _llm_decompose(req.original)
        if llm is not None:
            rewritten, filters = llm
            return RewriteResponse(
                rewritten=rewritten,
                filters=filters,
                same_as_original=(rewritten.strip() == req.original.strip()),
            )
    # Fallback heuristic
    rewritten, filters, same = _simple_rewrite(req.original)
    return RewriteResponse(rewritten=rewritten, filters=filters, same_as_original=same)
