# Paper-QA UI Roadmap (Rewritten)

This roadmap summarizes what is done and prioritizes next steps. It reflects the current, working UI (inline progress, exports, toggles) and targets scientist‑relevant features.

## Done (current state)
- Inline Live Analysis Progress
  - Chevron phases (Retrieval → Summaries → Answer) with completion ticks
  - Live retrieval progress bar (contexts_selected / evidence_k), indeterminate stripes before counts arrive
  - Transparency metrics: score min/mean/max; per-document counts (mini bars)
  - MMR (Maximum Marginal Relevance) (MVP):
    - Compact selected‑by‑score list (proxy based on selected evidence)
    - Live panel MMR block: selected diversity share, score histogram
    - Candidate vs selected overlay using temporary candidate parsing from logs
- Answer renders as Markdown
- Research Intelligence
  - Contradictions: heuristic + simple polarity‑based clustering across sources
  - Key insights, evidence summary, top evidence (by score)
  - Quality flags: Preprint and possible Retracted? per source (heuristic)
  - Diversity & recency: unique papers, preprint share, year histogram
  - Optional Critique (LLM‑based) under Configuration; works with any configured model via litellm; falls back to heuristic
 - Query rewrite (advanced)
   - LLM‑based decomposition of query (years/venues/fields)
   - Optional retrieval bias toggle applies filter hints to the rewritten query
   - Rewritten form and filters exported under `rewrite` in session JSON
   - UI shows original, rewritten query, and filters inline in Analysis Progress
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
1) Evidence curation enhancements
   - Evidence filtering controls (e.g., per‑doc caps, score cutoff sliders)
   - Source quality indicators (journal metrics proxy, venue reputation, open/retracted status)
   - Evidence conflicts view (cluster excerpts across docs; highlight opposing claims)

## Next priority
- True MMR (Maximum Marginal Relevance) visualization (hook‑based)
  - Integrate retrieval hooks (or upstream PR) to capture the full candidate set and the selected indices deterministically (no log parsing)
  - UI: candidate vs selected with score histogram and diversity summary (unique docs before/after)
  - Remove temporary heuristics once hooks are available; persist candidate/selected in exports

- Live analytics UI
  - Tool calls table (name, status, duration)
  - Score histogram
  - Pause streaming and compact mode for long runs
  - Disable Ask during query execution; restore automatically

- Exports polish
  - Enrich JSON with rewritten/original question, config toggles, and final metrics
  - Add structured event types and timestamps to JSONL; include rewritten query and answer metrics
  - Optionally append MMR candidate/selected sets when available

## Later
- Tool-call level traces and visualizations (if agent/tooling used in pipeline)
- Cost awareness (if available), with opt-in capture and display

## Technical notes
- Prefer structured callbacks over log scraping for progress/events
- Keep exports deterministic; redact or truncate long texts in traces
- Maintain local‑first defaults; cloud toggles must be explicit
