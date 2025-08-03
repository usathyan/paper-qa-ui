# Paper-QA: Scientific Paper Question Answering

## What is Paper-QA?
Paper-QA lets you ask research questions and get answers with citations from your own PDF papers and public sources (like Semantic Scholar, Crossref, OpenAlex). It uses state-of-the-art AI models for both language and embeddings, and is designed for scientists, students, and anyone who needs reliable, cited answers from the literature.

---

## Features
- **Ask questions about your own PDFs**
- **Include public sources for broader answers**
- **Citations for every answer**
- **Fast, streaming responses**
- **No vendor lock-in: uses OpenRouter.ai (Google Gemini 2.5 Flash Lite) and Ollama (nomic-embed-text)**
- **CLI and programmatic API**

---

## Requirements
- Python 3.11+
- [Ollama](https://ollama.com/) running locally (for embeddings)
- [OpenRouter.ai](https://openrouter.ai/) API key (for LLM)
- PDF papers (optional, for local research)

---

## Quick Start

1. **Clone the repo and enter the directory:**
   ```sh
   git clone <your-repo-url>
   cd paper-qa-ui
   ```

2. **Run the setup script:**
   ```sh
   make setup
   ```
   This will:
   - Create a virtual environment
   - Install all dependencies
   - Pull the required Ollama model
   - Set up directories and a `.env` file

3. **Add your OpenRouter API key:**
   - Edit `.env` and set `OPENROUTER_API_KEY=...`

4. **Add your PDF papers:**
   - Place PDFs in the `papers/` directory
   
   **Download initial papers (optional):**
   
   The papers directory contains sample research papers for testing. Since these are large files, they're not included in the git repository. You can:
   
   **Option 1: Use your own PDFs**
   - Place any PDF research papers in the `papers/` directory
   
   **Option 2: Download sample papers from public sources**
   ```sh
   # Create papers directory if it doesn't exist
   mkdir -p papers
   
   # Download sample papers from public repositories
   # (Replace these URLs with actual public paper URLs)
   curl -L -o papers/sample_paper_1.pdf "https://example.com/sample_paper_1.pdf"
   curl -L -o papers/sample_paper_2.pdf "https://example.com/sample_paper_2.pdf"
   ```
   
   **Option 3: Get papers from Semantic Scholar/PubMed**
   - Use the public sources feature to search for papers on your topic of interest
   - The system can access papers from Semantic Scholar, Crossref, and OpenAlex
   
   For testing, you can start with any PDF research papers you have locally.
   
   > **Note:** PDF files are excluded from the git repository (see `.gitignore`) to keep the repository size manageable. This is why the papers directory appears empty when cloned.

5. **Run a demo:**
   ```sh
   make run
   ```

6. **Or run the web interface:**
   ```sh
   make ui
   ```
   This will start a Gradio web interface at http://localhost:7860

---

## Usage

### Ask a Question (CLI)
```sh
# Ask about your local papers
make run-query QUESTION="What are the main findings of this research?" METHOD=local

# Ask about public sources
make run-query QUESTION="What are recent developments in machine learning?" METHOD=public

# Ask about both local and public sources
make run-query QUESTION="How does this research compare to current literature?" METHOD=combined
```
- `METHOD` can be `local`, `public`, or `combined`

### Web Interface (Gradio)
```sh
make ui
```
Then open http://localhost:7860 in your browser for a user-friendly web interface.

### Programmatic Use (Python)
```python
from paper_qa_core import PaperQACore

# Initialize with default configuration
core = PaperQACore(config_name="default")

# Query your local papers
result = await core.query_local_papers(
    "What are the key conclusions of this research?", 
    paper_directory="papers/"
)

# Query public sources
result = await core.query_public_sources(
    "What are the latest trends in this field?"
)

# Query both sources
result = await core.query_combined(
    "How does this research fit into the broader context?",
    paper_directory="papers/"
)
```
See `scripts/example_local.py` for more examples.

### Example Questions for Any Research Papers
- "What is the main research question being addressed?"
- "What methodology was used in this study?"
- "What are the key findings and conclusions?"
- "What are the limitations of this research?"
- "How does this work contribute to the field?"
- "What future research directions are suggested?"

---

## Troubleshooting
- **Ollama not running?** Start it with `ollama serve`.
- **Missing API key?** Set `OPENROUTER_API_KEY` in `.env`.
- **Model errors?** Ensure you have the correct model names in your config files.
- **Still stuck?** See `DEVELOPER.md` or open an issue.

---

## License
MIT
