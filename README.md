# Paper-QA UI: User Guide (Data Scientists)

This document describes exactly how to operate the UI, what each control does, how outputs are computed, and what to expect. It assumes familiarity with literature review workflows and scientific evaluation.

## 1. Launch
- Start: `make ui`
- Access: http://localhost:7860
- Requirements: Python 3.11+, Ollama running for local models (default). Optional cloud LLMs via OpenRouter/others if configured.

## 2. Document intake
- Upload PDFs via the left panel.
- The app copies files to `./papers/` and indexes them into an in-memory `Docs` corpus.
- Indexing runs immediately after upload; status appears in the left panel. No separate build step is required.

## 3. Query path
- The UI queries the in-memory `Docs` corpus using `Docs.aquery(question, settings)`. This is the same retrieval/answer path used by the CLI.
- All LLM/embedding calls run on a dedicated asyncio loop (background thread) to avoid event loop conflicts.

## 4. Configuration (left panel)

### 4.1 Configuration dropdown
- Selects a configuration profile for LLM and embeddings. Defaults to a local Ollama setup.
- Changes reinitialize settings.

### 4.2 Run Critique (checkbox)
- Adds a post-answer critique block.
- Implementation: heuristic + optional LLM-based critique; non-blocking.
- Output: short list of potential issues (unsupported claims, strong language). Does not alter the answer.

### 4.3 Query Options
- Rewrite query (experimental):
  - Rewrites the question prior to retrieval.
  - When enabled, “Rewritten query” and “Rewritten from” (original) appear above the Analysis Progress.
- Use LLM rewrite (advanced):
  - Invokes an LLM to return `{ rewritten, filters: { years, venues, fields } }`.
  - Filters are displayed inline (e.g., `years 2018-2024; venues Nature, PNAS; fields neurodegeneration`).
- Bias retrieval using filters:
  - Appends filter hints to the rewritten text. This biases retrieval without changing internal ranking logic.

### 4.4 Evidence Curation (beta)
- Relevance score cutoff (slider):
  - Sets `answer.evidence_relevance_score_cutoff`.
  - Values below cutoff are discarded during evidence selection.
- Per-document evidence cap (number):
  - After retrieval, caps the number of excerpts per source to this value.
  - If 0, no cap is applied post-retrieval.
- Max sources included (number):
  - Sets `answer.answer_max_sources` when > 0.

### 4.5 Display Toggles
- Show source flags (Preprint/Retracted?):
  - When enabled, source badges are shown for excerpts with heuristic flags (preprint servers; likely retraction markers in titles).
- Show evidence conflicts:
  - When enabled, a clustered conflicts list appears under Research Intelligence.

### 4.6 Export
- Export JSON: dumps session data `{question, answer, contexts, metrics, rewrite?, curation?}`.
- Export CSV: contexts (doc/page/score/text).
- Export Trace (JSONL): event stream when available.
- Export Bundle (ZIP): all of the above together.

## 5. Ask Questions (right panel)

### 5.1 Analysis Progress
- Header shows elapsed seconds and spinner while running.
- “Rewritten from” and “Rewritten query” appear if rewriting is enabled.
- Chevron phases: Retrieval, Summaries, Answer. Phases mark completion.
- Retrieval progress bar: `contexts_selected / evidence_k`. Indeterminate until counts arrive.
- Curation preview: shows current curation settings and estimated contexts after per-doc cap.
- Transparency block reports: embed latency, candidate count (if logged), MMR lambda (if logged), selection stats (min/mean/max), per-doc counts, prompt metrics, answer timing/attempts.
- MMR block: histogram of candidate vs selected scores; selected diversity share; counts.

### 5.2 Answer
- Markdown answer produced by the model from selected evidence.

### 5.3 Evidence Sources
- Table of excerpts: citation/title, page, score, snippet.
- Heuristic flags:
  - Preprint: arXiv/bioRxiv/medRxiv detected in source string.
  - Retracted?: the source string contains a retraction marker.

### 5.4 Research Intelligence
- Potential contradictions (heuristic + polarity clustering): cross-document antonyms and simple claim polarity agreement/disagreement.
- Evidence conflicts (clustered): list of entities with the number of sources exhibiting mixed polarity; shows up to 4 source names per entity. Controlled by the display toggle.
- Key insights: salient statements from the answer or first snippets.
- Evidence summary: excerpts per document.
- Top evidence (by score): tabular top contexts.

### 5.5 Metadata
- Processing time, number of documents included, evidence sources count, and a coarse confidence proxy.

## 6. Notes on behavior
- Rewriting and biasing affect retrieval text; they do not prune documents by themselves; they steer the selection.
- Score cutoff and max sources are applied in `Settings` before selection.
- Per-document cap is applied after selection to control over-representation.
- Flags and conflicts are heuristic, not metadata-backed unless you provide metadata in your sources.

## 7. Session export contents
- JSON contains: `question`, `answer`, `contexts`, `processing_time`, `documents_searched`, `metrics`, and optionally `rewrite`, `curation`, and `trace`.

## 8. Operational constraints
- One active query at a time (single-query lock).
- Local-first by default; external services only if configured.
- No background streaming of source documents; all processing is local unless otherwise set in configuration.

## 9. Troubleshooting
- If Ollama is not running, local configs will fail; start with `ollama serve`.
- If a port is occupied, run `make kill-server` then `make ui`.
- If API keys are missing for cloud LLMs, use the default local config or set keys in `.env`.
