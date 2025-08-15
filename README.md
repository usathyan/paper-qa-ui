# Paper-QA UI: User Guide (Data Scientists)

This document describes exactly how to operate the UI, what each control does, how outputs are computed, and what to expect. It assumes familiarity with literature review workflows and scientific evaluation.

## 1. Launch
- Start: `make ui`
- Access: http://localhost:7860
- Requirements: Python 3.11+, Ollama running for local models (default). Optional cloud LLMs via OpenRouter/others if configured.

## Screenshot of what the UI looks like

<p align="center">
  <img src="./screenshot.png" alt="Paper-QA UI" width="1000" />
</p>

## Demo Video

Watch the UI in action! This screen recording demonstrates the complete workflow from document upload to answer generation.

<p align="center">
  <video width="1000" controls>
    <source src="./docs/screen-recording.mp4" type="video/mp4">
    Your browser does not support the video tag.
  </video>
</p>

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
- Rewrite query:
  - Rewrites the question prior to retrieval.
  - When enabled, "Rewritten query" and "Rewritten from" (original) appear above the Analysis Progress.
- Use LLM rewrite:
  - Invokes an LLM to return `{ rewritten, filters: { years, venues, fields } }`.
  - Filters are displayed inline (e.g., `years 2018-2024; venues Nature, PNAS; fields neurodegeneration`).
- Bias retrieval using filters:
  - Appends filter hints to the rewritten text. This biases retrieval without changing internal ranking logic.

Clarification: identical rewritten text
- If "Use LLM rewrite" is OFF, the local heuristic rewriter only removes polite prefixes, converts leading "what is/are …" to "summarize …", and normalizes punctuation. Queries that do not match those patterns will remain unchanged.
- If "Use LLM rewrite" is ON but a local-only config is selected (e.g., `optimized_ollama`) or the provider is not reachable, the system falls back to the heuristic, which may result in no change.
- If an API-backed config is active (e.g., OpenRouter) and the model returns the same string (considering it already optimal), the rewritten text may legitimately equal the original.

### 4.4 Evidence Curation
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

## 5. Tab Structure and Content

The UI is organized into 5 main tabs that provide different views of the analysis:

### 5.1 Plan & Retrieval Tab
- **Question Input**: Enter your research question
- **Rewrite Button**: Uses LLM to rewrite and extract filters
- **Query Used**: Editable field showing the final query used for retrieval
- **Analysis Progress**: Real-time progress with chevron indicators
  - Shows elapsed time and spinner while running
  - Chevron phases: Plan & Retrieval → Evidence → Research Intel → Answer
  - Progress updates as each phase completes

### 5.2 Evidence Tab
- **Dynamic Summary**: Shows real-time metrics including:
  - Total evidence pieces selected
  - Evidence above relevance cutoff
  - Venues/journals detected
  - Preprint share percentage
  - Year distribution
  - Diversity score
- **Facets Panel**: Filter controls for years, venues, and fields
- **Evidence Summary**: Statistical overview of evidence sources
- **Evidence Sources**: Table of excerpts with citation, page, score, and snippet
- **Top Evidence (by score)**: Scrollable list of top 8 most relevant evidence pieces

### 5.3 Conflicts Tab
- **Evidence Quality Issues**: Flags for preprints, retractions, and other quality concerns
- **Relevance Conflicts**: Shows evidence pieces with high score variance from same source
- **Key Insights**: Analysis of evidence patterns including:
  - Evidence density per source
  - Strength of evidence base
  - Coverage breadth
  - Source diversity metrics

### 5.4 Research Intel Tab
- **Potential Contradictions**: Cross-document antonym detection and polarity clustering
- **Quality Flags**: Source-level quality indicators
- **Diversity & Recency**: Year distribution histogram and source diversity metrics
- **Critique**: LLM-generated assessment of answer quality and support

### 5.5 Answer Tab
- **Answer Display**: Formatted answer with consistent HTML styling
- **Clean Interface**: No placeholder text or unnecessary elements

## 6. Default behaviors and assumptions

The UI has been streamlined by removing several toggles and making opinionated defaults. These decisions optimize for the most common research workflows:

### 6.1 Always-enabled features

#### Smart Filter Biasing
This feature takes the filters extracted by the LLM during rewrite (like years, venues, fields, species, study types, outcomes) and appends them as text hints to the final query used for retrieval.

**Example:**
- Original question: `"What is the role of PICALM in Alzheimer's?"`
- LLM rewrite: `"PICALM role Alzheimer's disease"`
- Extracted filters: `{years: [2020, 2024], fields: ["neurodegeneration"], species: ["human"]}`
- **Final enhanced query**: `"PICALM role Alzheimer's disease (years 2020-2024; fields neurodegeneration; species human)"`

This enhancement improves retrieval precision by providing contextual hints to the search system, helping it find more relevant and targeted papers. This was previously the "Bias retrieval using filters" toggle.

#### Quote Extraction
- **Quote extraction**: All answers include extracted quotes from sources for better traceability. This was previously a toggle.

### 6.2 Removed UI complexity
- **LiteLLM debug logs**: No longer exposed in UI (reduces clutter)
- **File logging toggle**: Simplified to essential logging only
- **Tab switching automation**: Plan and Retrieval consolidated into single tab
- **Separate Analysis Progress tab**: Progress now streams inline for better UX
- **Status display panels**: Removed redundant session log and processing info sections
- **Placeholder text**: Cleaned up unnecessary placeholder messages throughout UI

These assumptions work well for 95% of research queries. For advanced customization, see the Developer documentation.

## 7. Notes on behavior
- Rewriting and biasing affect retrieval text; they do not prune documents by themselves; they steer the selection.
- Score cutoff and max sources are applied in `Settings` before selection.
- Per-document cap is applied after selection to control over-representation.
- Flags and conflicts are heuristic, not metadata-backed unless you provide metadata in your sources.

## 8. Session export contents
- JSON contains: `question`, `answer`, `contexts`, `processing_time`, `documents_searched`, `metrics`, and optionally `rewrite`, `curation`, and `trace`.

## 9. Operational constraints
- One active query at a time (single-query lock).
- Local-first by default; external services only if configured.
- No background streaming of source documents; all processing is local unless otherwise set in configuration.

## 10. Troubleshooting
- If Ollama is not running, local configs will fail; start with `ollama serve`.
- If a port is occupied, run `make kill-server` then `make ui`.
- If API keys are missing for cloud LLMs, use the default local config or set keys in `.env`.

