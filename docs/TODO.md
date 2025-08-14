# Paper-QA UI Roadmap

## Done (current state)
- Analysis Progress with chevrons, live retrieval progress, transparency metrics
- MMR (MVP): selected diversity share, score histogram, candidate vs selected overlay (log-parsed)
- Research Intelligence: contradictions (heuristic + clustering), insights, evidence summary, top evidence; conflicts list
- Source flags (Preprint/Retracted?)
- Critique: heuristic + optional LLM; markdown rendering and numbering normalization
- Query rewrite (LLM-based) and retrieval bias via filter hints; inline original/rewritten/filters
- Evidence Curation controls: score cutoff, per‑doc cap, max sources; curation preview; exports include rewrite/curation
- UI toggles: show flags, show conflicts
- Stability: dedicated async IO loop; single-query lock; local-first defaults
- Exports: JSON/CSV/JSONL; ZIP bundle
- Docs updated (README user guide; DEVELOPER notes)

## Next (high priority)
1) Evidence curation (phase 2)
   - Real-time preview refinements (apply cutoff into counts/histograms)
   - Per‑source quality indicators (venue string, simple reputation proxy when metadata present)
   - Conflicts drill‑down (click to expand polarity‑grouped excerpts)

## UX redesign (phased plan)
- Phase 1 (end-to-end minimal)
  - Plan tab: side-by-side Original/Rewritten; Generate rewrite (LLM); Accept rewrite overwrites Query Used
  - Filters: chips for years/venues/fields; apply as Bias mode only (append to query string)
  - Retrieval: scope chips, progress (selected/evidence_k), cutoff count, recent events
  - Evidence: simple list with title/citation, year/page/score, snippet; include/exclude; show flags
  - Conflicts: basic clustered list by entity (no expansion)
  - Synthesis: answer + critique; inline citations
  - Export: include rewrite, curation, toggles

- Phase 2 (curation + conflicts)
  - Hard filter mode (enforce constraints at selection) alongside Bias mode
  - Evidence cards: per‑doc cap inline control; venue/journal line (when metadata present)
  - Conflicts: expandable items; show up to N polarity‑grouped excerpts; minimal modal for full context
  - Cutoff-aware histograms in Retrieval panel; display potential impact before apply

- Phase 3 (analytics + ergonomics)
  - Live analytics: tool-calls table (name/status/duration); pause streaming; compact mode
  - Saved queries: snapshot rewrite + facets + curation + toggles; load & run
  - Snapshot diff: list changed filters/curation vs previous

- Phase 4 (MMR + exports)
  - True MMR hooks: capture candidate and selected deterministically; remove log parsing
  - UI: candidate vs selected with diversity summary; persist to exports
  - Exports polish: structured JSONL event types/timestamps; enriched JSON with rewrite/curation/metrics

- Out of scope for phases above (consider later)
  - Ontology pickers with external APIs (NCIt/BioPortal) beyond local suggestions
  - Detailed venue reputation scoring beyond simple proxies when metadata absent

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
