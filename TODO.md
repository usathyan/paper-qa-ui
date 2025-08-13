# Research Analytics & Agent Progress Visualization (Roadmap)

This document tracks the work to add rich, live analytics and visualizations for Paper-QA agentic progress in the UI.

## Goals
- Real-time, high-signal visibility into the analysis pipeline: retrieval, ranking, summarization, answer generation
- Show what the agent is doing (tools, steps, timings, costs) and why (evidence scores, diversity, contradictions)
- Zero extra hallucinations: analytics derived from existing callbacks/metadata only
- Low overhead; must not slow queries noticeably

## Data sources (Paper-QA internals)
- `Docs.aget_evidence` / `Docs.aquery` callbacks: stream incremental status and evidence
- Agent path (`agent_query`) callbacks (optional for public/combined searches)
- `AnswerResponse.session` fields (if available): `contexts`, `steps`, `tools_used`, `papers_searched`, `cost`
- Context objects: `score`, `page`, `text.doc.title`, `text.doc.formatted_citation`
- Existing CLI `EnhancedStreamingCallback` in `src/paper_qa_core.py` (captures tool calls/steps)

## Instrumentation
- [ ] Create `src/tracing/progress_callback.py` capturing:
  - [ ] Step timeline (start/end timestamps, labels)
  - [ ] Tool calls (name, args summary, outcome)
  - [ ] Retrieval metrics (k fetched, MMR lambda, scores, min/mean/max)
  - [ ] Evidence chosen vs. candidates (indices, scores)
  - [ ] Costs/time (if available from `lmi`)
  - [ ] Errors/warnings (transport/timeouts)
- [ ] Implement a threadsafe async event bus:
  - [ ] `ProgressEvent` dataclass (type, timestamp, payload)
  - [ ] `asyncio.Queue` for UI streaming
  - [ ] Back-pressure + max buffer with drop-old policy
- [ ] Wire callbacks into:
  - [ ] `Docs.aget_evidence` (retrieval phase)
  - [ ] `Docs.aquery` (answer phase)
  - [ ] Agent path (optional) if using `agent_query`

## UI (Gradio) – Analysis Progress panel
- [x] Embed live Analysis Progress directly under the question (inline), replacing separate tab
- [ ] Live components:
  - [x] Basic phase indicators (badges): Retrieval, Summaries, Answer
  - [x] Progress bar: contexts retrieved/selected vs. target (`evidence_k`)
  - [ ] Tool calls table: name, status, duration
  - [ ] Score histogram: distribution of candidate scores (Plotly or lightweight SVG)
  - [ ] MMR selection view: show selected vs. discarded candidates
  - [ ] Costs/time: running totals (if `lmi` provides)
  - [ ] Errors: surfaced inline when retries/backoff occur
- [x] Auto-scroll to Answer on completion
- [ ] Compact mode for long runs
- [ ] Toggle to pause streaming (reduce UI overhead)

### Additional UX/Insights Enhancements
- [ ] "Trace / Thinking" panel showing agent steps and tools (separate tab), sourced from callbacks (tool name, args summary, output, duration)
- [ ] "LLM Critique" optional pass that evaluates the final answer for contradictions/consistency and citation adequacy (uses OpenRouter when configured)
- [ ] Drill‑down for each evidence item: open full paragraph context and jump-to-page indicator (if available)

## Storage & export
- [ ] JSONL trace per session under `data/traces/{session_id}.jsonl`
- [ ] Export buttons:
  - [ ] Download JSON (answer + contexts + scores + timeline)
  - [ ] Download CSV (contexts w/ scores)
  - [ ] Download Trace (JSONL of agent/tool events)

## Config & toggles
- [ ] `analytics.enabled` (default true)
- [ ] `analytics.capture_costs` (default true if available; degrades gracefully)
- [ ] `analytics.max_events` (default 5,000)
- [ ] Privacy: redact long text in events; emit snippets only
- [ ] `critique.enabled` (default off), `critique.model` (e.g., `openrouter/google/gemini-2.5-flash-lite`), `critique.max_tokens`, `critique.cost_guard`

## Agent & Search Controls (enable/visibility in UI)
- [ ] Surface agent tool configuration in UI (read-only if using local-only):
  - [ ] Ensure tools include: `paper_search`, `gather_evidence`, `gen_answer`, `reset`, `complete`, `clinical_trials_search`
- [ ] Toggle: `agent.should_pre_search`
- [ ] Sliders/inputs: `agent.search_count`, `agent.agent_evidence_n`, `agent.timeout`
- [ ] Switches: `agent.wipe_context_on_answer_failure`, `agent.return_paper_metadata`
- [ ] Display current agent tool list in the UI (for transparency)

## Evidence Controls (advanced)
- [ ] UI slider: `texts_index_mmr_lambda` (diversity in MMR search)
- [ ] Slider: `answer.evidence_k` (default high, let user dial down)
- [ ] Slider: `answer.answer_max_sources`
- [ ] Number: `answer.evidence_relevance_score_cutoff` (defaults to 0)
- [ ] Toggles: `answer.group_contexts_by_question`, `answer.answer_filter_extra_background`, `answer.get_evidence_if_no_contexts`
- [ ] Formatting: `answer.evidence_detailed_citations`, `answer.evidence_summary_length`, `answer.evidence_skip_summary`

## Retrieval & Indexing
- [ ] Add UI workflow to build/rebuild Tantivy indexes (wrap `src/cli/index_docs.py`)
- [ ] Options: recurse, sync, concurrency, batch_size, index name/dir
- [ ] Add UI to query existing index (wrap `src/cli/query_index.py`):
  - [ ] Support `--pre_evidence` (pre-gather summaries) toggle
  - [ ] Evidence_k override and include_citations
- [ ] Optional: save “answers” index for AnswerResponses (opt-in)

## Metadata Enrichment (optional, off by default)
- [ ] UI toggle: `parsing.use_doc_details` to enable Crossref/SemanticScholar/OpenAlex enrichment
- [ ] Validate env/API keys; show explicit warning about network calls
- [ ] Graceful fallback to local-only if keys/timeouts missing

## Streaming / Trace
- [ ] Use callbacks to capture streaming tokens, tool calls, and agent steps (wire to Trace panel)
- [ ] Render tool call arguments summary + outcome status + durations
- [ ] Link tool events to retrieved evidence when possible

## Implementation plan (milestones)
1) Instrumentation (1–2 days)
- New callback and event bus; log basic phases + retrieval counts
- Hook into `Docs.aquery` and `aget_evidence` and emit events

2) Minimal UI (1 day)
- Add panel with timeline + progress bar + live evidence table

3) Enriched analytics (1–2 days)
- Score histogram, MMR selection overlay, costs/time if available
- Error/retry surfaces

3b) Optional LLM Critique (0.5–1 day)
- Add post‑answer critique step (guarded by toggle) to flag inconsistencies/unsupported claims
- Display a concise critique summary with links to implicated evidence items

4) Export and persistence (0.5 day)
- JSON/CSV download and optional JSONL trace files

5) Polish (0.5 day)
- Performance tuning; throttling; toggles; doc updates

## Progress
- [x] Switched tests to mypy (ruff + mypy in `make test`)
- [x] Fixed typing in `utils`, `config_manager`, `config_ui`, CLI imports
- [x] Added post-answer Research Intelligence panel (contradictions, insights, evidence summary, top evidence with scores)
- [x] Inline "Analysis Progress" panel under question with live logs (Phase 1 MVP)
- [x] Moved Top evidence table to Research Intelligence (removed from live panel)
- [x] Auto-scroll to Answer after analysis completes
- [x] Dark-mode compliance via shared CSS classes across Status, Analysis, Answer, Sources, Metadata, and Research Intelligence
- [x] Phase badges (Retrieval, Summaries, Answer) with completion ticks
- [x] Retrieval progress bar (contexts_selected / evidence_k)
- [x] Transparency panel: evidence selection stats (score min/mean/max) and per-document counts (mini bar viz)
- [x] Answer metrics: elapsed, sources included, approximate prompt size, attempts
- [x] Hide legacy Processing Status block in UI (to be removed later)
- [x] Dedicated background asyncio loop for all LLM/embedding I/O to prevent loop-close/binding errors; single-query lock
- [x] Replaced deprecated `gr.utils.escape_html` with `html.escape`
- [x] Spinner + elapsed time heartbeat; dynamic auto-expanding progress panel (no scroll)
- [ ] Remaining mypy/typing cleanups (tests, UI helpers, CLI return annotations)

## Acceptance criteria
- Live panel shows phase/timeline updates while answering
- Evidence table updates incrementally with source/score/page/snippet
- Histogram shows candidate score distribution for the current query
- MMR selection visualization shows at least top-N selected vs discarded
- No UI stalls; CPU overhead < 5% of total time on typical workload
- Exported JSON contains answer, contexts with scores, and the event timeline
- (If critique enabled) A critique summary appears post‑answer with specific flags and references

## Open questions
- Availability of per-step costs with Ollama-only setups (often unknown); if not available, show time only
- Granularity from Paper-QA callbacks: do we need to upstream tiny hooks (PR) for more structured retrieval events?
- How to correlate tool logs with retrieval outcomes when using the agent path only

## Risks
- Over-instrumentation can slow down queries; mitigate by throttling UI updates
- Event loop contention (already mitigated with isolated loop + single-query lock)
- Model streaming variability (local models may be bursty)
- Critique step adds latency/cost; ship disabled by default and warn when turned on

## Potential future enhancements (transparency & scientist‑relevant metrics)
- Answer assembly transparency panel (high-level, non-intrusive):
  - Query embedding & retrieval: embed latency, fetch_k, MMR lambda, candidate count, score min/mean/max
  - Evidence selection: contexts_selected vs evidence_k, score stats, per-doc counts, elapsed
  - Summaries synthesis (if used): summaries count, latency, token estimates
  - Prompt building: prompt length (chars/tokens), sources included, max_sources
  - Answer generation: attempts/retries, latency per attempt, token usage/cost (if available)
  - Post-processing: sources used, final contexts, postproc time

- Additional scientist‑relevant metrics:
  - Source contribution breakdown: evidence share per paper/journal
  - Recency distribution (years) of selected evidence; median age
  - Diversity indices: number of unique papers, journals, and authors
  - Agreement/contradiction rate across sources (simple antonym/negation heuristics)
  - Evidence span length distribution (tokens/chars) and coverage per paper
  - Domain/entity coverage (keywords/MeSH terms/GO terms) frequency
  - Confidence calibration proxy: score percentile of selected vs candidates
  - MMR effect: redundancy reduction vs diversity (before/after stats)
  - Retrieval cache hits (if any), local vs remote model usage mix

- Visualizations to consider (lightweight first):
  - Timeline/stepper with per-phase durations
  - Progress bar (contexts_selected vs evidence_k)
  - Histograms: evidence scores; years of publication
  - Bar charts: evidence per document/journal; top entities/keywords
  - Scatter: score vs page number; score vs year
  - Box/violin plots for score distributions across documents
  - Simple Sankey: candidates → selected evidence (counts)
  - Donut chart: contribution share by source
  - Inline sparklines (SVG) for scores over ranked candidates

- Implementation notes:
  - Start with Plotly charts embedded via Gradio components; fall back to SVG for zero‑dep
  - Throttle UI updates; compute heavy stats after retrieval completes
  - Make metrics optional via settings (analytics.enabled) to avoid overhead
