# Paper-QA UI: User Guide 

This repo is a UI built on top of open source tools to help scientists with their literature synthesis. It assumes you have [sourced](https://github.com/Future-House/paper-qa/tree/main?tab=readme-ov-file#where-do-i-get-papers), and downloaded the journals and articles needed to conduct your analysis. It assumes familiarity with literature review workflows and scientific evaluation.
This repo only provides a visual interface that exposes the many features available with [Paper QA](https://github.com/Future-House/paper-qa) project, and adds a few more features not part of it.

***PaperQA has a lot more features than what is exposed via this user interface. I have made significant assumptions in making this as practical and usable as possible based on my limited knowledge and experinece in understanding the research workflow.***


## Getting Started
- Clone this repo
- Build: `make setup`
- Start: `make ui`
- Access: http://localhost:7860
- Requirements: Python 3.11+, [Ollama](https://ollama.com/) running for local models (default). Optional cloud LLMs via OpenRouter/others if configured.


## Screenshot of what the UI looks like

<p align="center">
  <img src="./screenshot.png" alt="Paper-QA UI" width="1000" />
</p>

## Demo Video

Watch the UI in action! This screen recording demonstrates the complete workflow from document upload to answer generation.

[![Paper-QA UI Demo Video](https://img.youtube.com/vi/GX6vTlS29ps/maxresdefault.jpg)](https://youtu.be/GX6vTlS29ps)

<p align="center">
  <strong>🎥 Click the image above to watch the demo video on YouTube</strong>
</p>

# User Guide
## 1. Document intake
- Upload PDFs via the left panel (Project/Corpus) section.
- The app copies files to `./papers/` and indexes them into an in-memory `Docs` corpus.
- Indexing runs immediately after upload; status appears in the left panel. 
- Contact me if you need the ability to add other sources, and indexes


## 2. Configuration

### 2.1 Query Builder: Select configuration
- Selection of a configuration profile for LLM, embeddings and more. Defaults to a local Ollama setup.
- You can find more details about configuration aspects in the [developer notes](./docs/DEVELOPER.md)

### 2.2 Run Critique (checkbox)
- Adds a post-answer critique block.
- Output: short list of potential issues (unsupported claims, strong language). Does not alter the answer.

### 2.3 Curaton Controls
- Relevance score cutoff (slider):
  - Sets `answer.evidence_relevance_score_cutoff`.
  - Values below cutoff are discarded during evidence selection.
- Per-document evidence cap (number):
  - After retrieval, caps the number of excerpts per source to this value.
  - If 0, no cap is applied post-retrieval.
- Max sources included (number):
  - Sets `answer.answer_max_sources` when > 0.

### 2.4 Display Toggles
- Show source flags (Preprint/Retracted?):
  - When enabled, source badges are shown for excerpts with heuristic flags (preprint servers; likely retraction markers in titles).
- Show evidence conflicts:
  - When enabled, a clustered conflicts list appears under Research Intelligence.

### 2.5 Saved Queries
- This section is a placeholder for future feature. This is not implemented yet.
- Contact me if you need this feature

### 2.6 Export
- Export JSON: dumps session data `{question, answer, contexts, metrics, rewrite?, curation?}`.
- Export CSV: contexts (doc/page/score/text).
- Export Trace (JSONL): event stream when available.
- Export Bundle (ZIP): all of the above together.


## 3. Tab Structure and Content

The UI is organized into 5 main tabs that provide different views of the analysis:

### 3.1 Plan & Retrieval Tab
- **Question Input**: Enter your research question
- **Rewrite Button**: Uses LLM to rewrite your query. It uses an LLM with predefined prompts to help clarify the question
- **Query Used**: Editable field showing the final query used for retrieval
- **Analysis Progress**: Real-time progress with chevron indicators
  - Shows elapsed time and spinner while running
  - Chevron phases: Plan & Retrieval → Evidence → Research Intel → Answer
  - Progress updates as each phase completes

### 3.2 Evidence Tab
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

### 3.3 Conflicts Tab
- **Evidence Quality Issues**: Flags for preprints, retractions, and other quality concerns
- **Relevance Conflicts**: Shows evidence pieces with high score variance from same source
- **Key Insights**: Analysis of evidence patterns including:
  - Evidence density per source
  - Strength of evidence base
  - Coverage breadth
  - Source diversity metrics

### 3.4 Research Intel Tab
- **Potential Contradictions**: Cross-document antonym detection and polarity clustering
- **Quality Flags**: Source-level quality indicators
- **Diversity & Recency**: Year distribution histogram and source diversity metrics
- **Critique**: LLM-generated assessment of answer quality and support

### 3.5 Answer Tab
- **Answer Display**: Formatted final answer to your question

## 4. Default behaviors and assumptions

The UI has been streamlined by removing several toggles and making opinionated defaults. These decisions optimize for the most common research workflows:

### 4.1 Assumptions and Features 

#### Rewrite prompt
This feature adds additional filters extracted by the LLM during rewrite (like years, venues, fields, species, study types, outcomes) and appends them as text hints to the final query used for retrieval.

**Example:**
- Original question: `"What is the role of PICALM in Alzheimer's?"`
- LLM rewrite: `"PICALM role Alzheimer's disease"`
- Extracted filters: `{years: [2020, 2024], fields: ["neurodegeneration"], species: ["human"]}`
- **Final enhanced query**: `"PICALM role Alzheimer's disease (years 2020-2024; fields neurodegeneration; species human)"`

#### General Behavior
- Answers include extracted quotes from sources for better traceability.
- Rewriting and biasing affect retrieval text; they do not prune documents by themselves; they steer the selection.
- Score cutoff and max sources are applied in `Settings` before selection.
- Per-document cap is applied after selection to control over-representation.
- Flags and conflicts are heuristic, not metadata-backed unless you provide metadata in your sources.
- JSON contains: `question`, `answer`, `contexts`, `processing_time`, `documents_searched`, `metrics`, and optionally `rewrite`, `curation`, and `trace`.

## 5. Operational constraints
- One active query at a time (single-query lock).
- Local-first by default; external services only if configured.
- No background streaming of source documents; all processing is local unless otherwise set in configuration.
- If Ollama is not running, local configs will fail; start with `ollama serve`.
- If a port is occupied, run `make kill-server` then `make ui`.
- If API keys are missing for cloud LLMs, use the default local config or set keys in `.env`.

