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
   ```sh
   # Create papers directory if it doesn't exist
   mkdir -p papers
   
   # Download the 4 included research papers
   curl -L -o papers/Alzheimer_Pathogenesis_2021.pdf "https://github.com/usathyan/paper-qa-ui/raw/main/papers/Alzheimer_Pathogenesis_2021.pdf"
   curl -L -o papers/PICALM_Mechanisms_2020.pdf "https://github.com/usathyan/paper-qa-ui/raw/main/papers/PICALM_Mechanisms_2020.pdf"
   curl -L -o papers/Alzheimer_GWAS_2019.pdf "https://github.com/usathyan/paper-qa-ui/raw/main/papers/Alzheimer_GWAS_2019.pdf"
   curl -L -o papers/PICALM_Alzheimer_Review_2021.pdf "https://github.com/usathyan/paper-qa-ui/raw/main/papers/PICALM_Alzheimer_Review_2021.pdf"
   ```
   
   These papers focus on Alzheimer's disease research and PICALM mechanisms, providing a good starting point for testing the system.

5. **Run a demo:**
   ```sh
   make run
   ```

---

## Usage

### Ask a Question (CLI)
```sh
make run-query QUESTION="What is the role of PICALM in Alzheimer's disease?" METHOD=public
```
- `METHOD` can be `local`, `public`, or `combined`

### Programmatic Use (Python)
```python
from paper_qa_core import PaperQACore
core = PaperQACore(config_name="default")
result = await core.query_local_papers("What is ...?", paper_directory="papers/")
```
See `scripts/example_local.py` for more.

---

## Troubleshooting
- **Ollama not running?** Start it with `ollama serve`.
- **Missing API key?** Set `OPENROUTER_API_KEY` in `.env`.
- **Model errors?** Ensure you have the correct model names in your config files.
- **Still stuck?** See `DEVELOPER.md` or open an issue.

---

## License
MIT
