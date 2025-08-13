# Paper-QA UI

Drug-discovery friendly question answering over your PDFs, with transparent retrieval, rich evidence, and scientist-ready summaries.

## Setup

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com/) installed and running

### Installation
```bash
git clone <repository-url>
cd paper-qa-ui
make setup
```

### Environment Configuration

Copy the template and configure your API keys:
```bash
cp env.template .env
# Edit .env with your API keys
```

## Usage

### Start the UI
```bash
make ui
```
Open http://localhost:7860

### Document Processing Workflow

1. **Upload Documents**: Upload PDF files using the file upload
2. **Automatic Processing & Indexing**: Documents are copied to the `papers/` directory and immediately indexed into an in-memory `Docs` corpus
3. **Ask Questions**: Use the question interface to query your documents via the in-memory corpus (same path as CLI)

### User Flow

```
📁 Upload PDF documents
    ↓ (auto copy + indexing)
✅ Documents copied and indexed
    ↓
❓ Ask questions (runs Docs.aquery over your corpus)
```

### Example Questions
- "What is the main finding of this research?"
- "What methodology was used?"
- "What are the limitations mentioned?"
- "What conclusions were drawn?"

## What you’ll see in the UI

- Live Analysis Progress (inline, under the question)
  - Chevron phases: Retrieval → Summaries → Answer. Each turns green when done.
  - Retrieval progress bar: contexts_selected / evidence_k (updates live; indeterminate stripes before counts arrive)
  - Transparency panel (scientist‑oriented quick facts):
    - Retrieval: embedding latency (sec), candidate/evidence collection
    - Evidence selection: how many excerpts were selected, cutoff, score min/mean/max
    - Per‑document evidence counts with mini bars (top 5 sources by excerpts)
    - Prompt building: number of sources included, approximate prompt size (characters)
    - Answer generation: elapsed time and attempts used

- Answer
  - Natural language answer composed from the selected evidence
  - Tip: Look for precise claims tied to strong evidence; re‑ask to narrow/expand scope

- Evidence Sources (by excerpt)
  - For each excerpt: source (citation/title), page, score (higher = closer match), and snippet
  - Interpretation: Multiple excerpts from different sources suggest convergence; mixed scores can indicate nuance

- Research Intelligence
  - Potential contradictions (heuristic): quick flags where sources appear to disagree
  - Key insights: salient statements/summaries pulled from answer/evidence
  - Evidence summary: number of excerpts per document
  - Top evidence (by score): compact table of the strongest excerpts
  - Optional Critique: post‑answer sanity check highlighting potentially unsupported or overly strong claims (toggle under Configuration)

- Metadata
  - Processing time, documents searched, evidence count, a coarse confidence proxy


### Screenshot
<p align="center">
  <img src="./screenshot.png" alt="Paper-QA UI screenshot" width="900" />
  <br/>
  <em>Inline Live Analysis Progress with chevron phases, transparency metrics, and dark‑mode‑safe panels.</em>
</p>

### Interpreting metrics 
- Score min/mean/max: Distribution of retrieval scores for selected excerpts. Higher min/mean suggest stronger alignment
- Per‑document counts: A quick guide to contribution. Skews can reveal over‑representation; drill into lower‑represented but high‑score sources for diversity
- Prompt size (approximate): Indicator of context packed into the model prompt; very large prompts can increase latency
- Attempts and elapsed: If attempts > 1, the system retried to stabilize quality; elapsed helps anticipate workload scaling
 - Critique: A non-binding diagnostic to guide further reading; it does not alter the answer

## Configurations

### Local Processing (Default)
- **Config**: `optimized_ollama`
- **LLM**: Ollama llama3.2
- **Embedding**: Ollama nomic-embed-text
- **Setup**: No API keys required

### Azure OpenAI
- **Config**: `azure_openai`
- **LLM**: Azure GPT-4
- **Embedding**: Ollama nomic-embed-text
- **Setup**: Add to `.env`:
  ```
  AZURE_OPENAI_API_KEY=your_key
  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
  ```

### Amazon Bedrock
- **Config**: `amazon_bedrock`
- **LLM**: Claude 3 Sonnet
- **Embedding**: Ollama nomic-embed-text
- **Setup**: Add to `.env`:
  ```
  AWS_ACCESS_KEY_ID=your_key
  AWS_SECRET_ACCESS_KEY=your_secret
  AWS_REGION=us-east-1
  ```

### OpenRouter
- **Config**: `openrouter_ollama`
- **LLM**: Various models via OpenRouter
- **Embedding**: Ollama nomic-embed-text
- **Setup**: Add to `.env`:
  ```
  OPENROUTER_API_KEY=your_key
  ```

## CLI Usage

```bash
# Test CLI
make test-cli

# Run example
make cli-example

# Direct usage
python -m src.cli.simple_local_qa "What is this paper about?" --files papers/your.pdf --verbosity 2 --stream
# Alternative CLI (agent-style)
python -m src.cli.paper_qa_cli "What is this paper about?"
```

## Research-Intelligence Defaults (Enabled)

These defaults are applied in both the UI and CLI to surface richer, better-organized evidence and reduce low-signal answers:

- **Pre-search and metadata**: agent pre-search enabled; return paper metadata
- **More evidence**: `evidence_k ≥ 15`, `answer_max_sources ≥ 10`, retries enabled
- **Better organization**: `group_contexts_by_question` on; extra background filtered
- **Grounded retrieval**: `get_evidence_if_no_contexts` on; low relevance cutoff (`0`)
- **Local-first**: external metadata providers disabled by default for speed and determinism

Tip: On very small machines, you can lower `evidence_k` and set `max_concurrent_requests: 1` in your config for latency.

## Theming and dark mode
- The app ships with a modern theme and dark‑mode‑aware custom sections
- You can force a theme via URL: add `?__theme=dark` or `?__theme=light` to the address

## What’s new in this release
- Inline Live Analysis Progress with chevron phases and a retrieval progress bar
- Transparency panel with scientist‑relevant metrics (scores, counts, prompt size, timing)
- Research Intelligence section with contradictions, insights, evidence summary, and Top evidence
- Robust local‑first execution: a dedicated async loop and single‑query lock for stability
- Dark‑mode‑safe styling across Status, Analysis, Answer, Sources, Research Intelligence, and Metadata

## Troubleshooting

### Port Issues
```bash
make kill-server
make ui
```

### Ollama Issues
```bash
ollama serve
ollama pull llama3.2
ollama pull nomic-embed-text
```

### Missing Models
```bash
ollama list  # Check available models
ollama pull <model_name>  # Download missing models
```

### Document Processing Issues
- **Documents not processing**: Check if Ollama is running
- **Processing stuck**: Try refreshing the page and re-uploading
- **Connection errors**: Restart Ollama with `ollama serve`