# Paper-QA UI Roadmap (Rewritten)

This roadmap summarizes what is done and prioritizes next steps. It reflects the current, working UI (inline progress, exports, toggles) and targets scientist‑relevant features.

## Done (current state)
- Inline Live Analysis Progress
  - Chevron phases (Retrieval → Summaries → Answer) with completion ticks
  - Live retrieval progress bar (contexts_selected / evidence_k), indeterminate stripes before counts arrive
  - Transparency metrics: score min/mean/max; per-document counts (mini bars)
  - MMR (MVP): compact selected‑by‑score list (proxy based on selected evidence)
- Answer renders as Markdown
- Research Intelligence
  - Contradictions (heuristic), key insights, evidence summary, top evidence
  - Optional Critique (heuristic) under Configuration
- Query Options
  - Rewrite query (experimental) toggle; displays original question above progress
- Exports
  - JSON (answer + contexts + metrics + trace if present)
  - CSV (contexts)
  - JSONL trace (events) – initial support
  - Bundle (ZIP) for JSON/CSV/JSONL
- Stability/UX
  - Dedicated async loop; single query lock
  - Ask button disabled during uploads (shows Wait…); runtime config switching
  - Dark‑mode‑safe styling; Processing Status hidden
- Docs & license updates

## Next (high priority)
1) True MMR visualization
   - Add a retrieval hook (or upstream PR) to capture the candidate set and the selected indices
   - UI: display selected vs discarded with a score histogram and diversity summary (unique docs before/after)
2) Critique (LLM‑based, optional)
   - Replace heuristic with a fast LLM pass (OpenRouter), with timeout and cost notice
   - Output: concise flags referencing implicated evidence items
3) Exports polish
   - Enrich JSON with rewritten/original question, config toggles, and final metrics
   - Add structured event types and timestamps to JSONL; include rewritten query and answer metrics
   - Optionally append MMR candidate/selected sets when available

## Medium priority
- Live analytics UI
  - Tool calls table (name, status, duration)
  - Score histogram
  - Pause streaming and compact mode for long runs
  - Disable Ask during query execution; restore automatically
- Query rewrite (advanced)
  - LLM‑based decomposition inspired by ai2‑scholarqa‑lib (years, venues, fields of study)
  - Use extracted filters to bias retrieval (toggle)
  - Include rewritten form and filters in exports/traces
- Evidence curation enhancements
  - Evidence filtering controls (e.g., per‑doc caps, score cutoff sliders)
  - Source quality indicators (journal metrics proxy, venue reputation, open/retracted status)
  - Evidence conflicts view (cluster excerpts across docs; highlight opposing claims)

## Scientist‑relevant analytics (future)
- Contradiction analysis (Paper‑QA aware)
  - Expand beyond heuristics by grouping semantically similar claims and marking polarity
- Retraction details
  - Flag retracted papers (if metadata available); surface retraction notices
- Journal quality signals
  - Lightweight proxy scores (e.g., indexed venue lists, DOAJ/open access flags, acceptance rates when available)
- Diversity & recency
  - Charts for publication year distribution, doc/journal/author diversity

## Technical notes
- Prefer structured callbacks over log scraping for progress/events
- Keep exports deterministic; redact or truncate long texts in traces
- Maintain local‑first defaults; cloud toggles must be explicit
