# Developer Notes: Paper-QA

## 1. Traceability Matrix

| User Requirement | Functional Requirement | Implementation |
|------------------|----------------------|----------------|
| Query local PDFs | System must load and index user PDFs | `PaperQACore.query_local_papers`, `configs/local_only.json` |
| Query public sources | System must search public APIs (Semantic Scholar, Crossref, etc) | `PaperQACore.query_public_sources`, `configs/public_only.json` |
| Combined research | System must merge local and public results | `PaperQACore.query_combined`, `configs/combined.json` |
| Citations in answers | All answers must include citations | Core logic in `paperqa` and streaming callbacks |
| Streaming responses | Show answers as they generate | `streaming.py`, CLI callbacks |
| Configurable models | User can select LLM/embedding | `configs/*.json`, `config_manager.py` |
| CLI and API | Both CLI and Python API must be available | `scripts/paper_qa_cli.py`, `paper_qa_core.py` |
| Error handling | System must retry and report errors | `tenacity` usage, error returns |
| Rate limiting | Handle API rate limits gracefully | Environment variables, optimized configs |

---

## 2. Architecture Overview

```mermaid
graph TD
    CLI["CLI (scripts/paper_qa_cli.py)"]
    API["Python API (paper_qa_core.py)"]
    Config["Config Manager (config_manager.py)"]
    Stream["Streaming (streaming.py)"]
    Utils["Utils (utils.py)"]
    PaperQA["paperqa (external)"]
    Ollama["Ollama (nomic-embed-text)"]
    OpenRouter["OpenRouter.ai (Gemini 2.5 Flash Lite)"]
    Public["Public APIs (Semantic Scholar, Crossref, ...)"]

    CLI --> API
    API --> Config
    API --> Stream
    API --> PaperQA
    API --> Utils
    PaperQA --> Ollama
    PaperQA --> OpenRouter
    PaperQA --> Public
```

- **CLI**: User entry point, parses args, calls API.
- **API**: Main logic, exposes query functions, manages config and streaming.
- **Config Manager**: Loads/validates configs, supports overrides.
- **Streaming**: Handles real-time output, supports multiple callbacks.
- **Utils**: Helpers for file ops, status, formatting.
- **paperqa**: External RAG engine, handles LLM/embedding, citations.
- **Ollama/OpenRouter/Public**: External services.

---

## 3. Key Files & Structure

- `src/paper_qa_core.py`: Main API, all query logic.
- `src/config_manager.py`: Config loading/validation.
- `src/streaming.py`: Streaming/callbacks.
- `src/utils.py`: Helpers.
- `configs/`: All scenario configs (local_only, public_only, combined, etc).
- `scripts/paper_qa_cli.py`: CLI entry point.
- `scripts/configure_rate_limits.py`: Rate limiting configuration script.
- `tests/`: All tests.

---

## 4. Rate Limiting Experience & Configuration

### Problem Encountered
During development, we encountered frequent rate limiting errors (429 Too Many Requests) from public APIs, particularly Semantic Scholar. The system was making too many concurrent requests without proper delays.

### Solution Implemented
We implemented a comprehensive rate limiting strategy using PaperQA's built-in mechanisms:

#### Environment Variables (`.env`)
```bash
# Semantic Scholar API (most commonly rate-limited)
SEMANTIC_SCHOLAR_API_REQUEST_TIMEOUT=30.0
SEMANTIC_SCHOLAR_API_KEY=""

# Crossref API
CROSSREF_API_REQUEST_TIMEOUT=30.0
CROSSREF_MAILTO="user@example.com"

# OpenAlex API
OPENALEX_API_REQUEST_TIMEOUT=30.0
OPENALEX_MAILTO="user@example.com"

# Unpaywall API
UNPAYWALL_TIMEOUT=30.0
UNPAYWALL_EMAIL="user@example.com"

# General API settings
PQA_VERBOSITY=3
```

#### Configuration Optimizations
- **Reduced concurrency**: From 5 to 2-3 to spread requests over time
- **Optimized search count**: Reduced from 25-50 to 15-20 papers for better quality
- **Increased timeouts**: Set to 600 seconds for rate limit recovery
- **Reduced concurrent requests**: From 4 to 2-3 for better rate limit handling

#### PaperQA's Built-in Mechanisms
PaperQA includes sophisticated rate limiting with:
- **Tenacity integration**: Automatic retry with exponential backoff (4-10 second delays)
- **HTTP status code handling**: Specifically handles 403, 429, 500, 502, 503, 504 errors
- **Async retrying**: Non-blocking retry behavior with maximum 3 attempts

#### Automated Setup
Created `scripts/configure_rate_limits.py` that:
- Automatically adds rate limiting environment variables to `.env`
- Optimizes configuration files for better rate limit handling
- Creates backups of existing configurations
- Provides clear next steps

### Results
- ✅ No more rate limit errors
- ✅ Improved reliability with proper timeouts
- ✅ Better performance with optimized concurrency
- ✅ Environment variables configured for all APIs
- ✅ Built-in retry mechanisms working properly

### API-Specific Rate Limits
- **Semantic Scholar**: 100 requests per 5 minutes (without API key), significantly improved with email
- **Crossref**: 500 requests per day (without email), 1000 with email
- **OpenAlex**: 100,000 requests per day, email required for better limits
- **Unpaywall**: 100,000 requests per day, email required for better limits

---

## 5. Testing & Linting

- Run all tests: `make test`
- Lint: `make lint`
- Pytest: `make pytest`
- Add new tests in `tests/` for all new features.

---

## 6. Contribution Guidelines

- Fork, branch, PR.
- All new features must have tests.
- Keep user-facing docs in `README.md` only.
- Keep dev/traceability/architecture here.
- When adding new APIs, consider rate limiting implications.

---

## 7. Advanced Topics

- **Config overrides**: Use `ConfigManager` to load/merge configs.
- **Streaming**: Use `create_multi_callback` for custom output.
- **Error handling**: All query functions return structured errors; retry logic via `tenacity`.
- **Rate limiting**: Use `scripts/configure_rate_limits.py` for new setups.

---

## 8. Development Experience Notes

### Semantic Scholar Testing Experience
During initial development, we created extensive tests for Semantic Scholar API to understand:
- What queries work best for finding specific papers
- How to handle rate limiting effectively
- Which search patterns yield the most relevant results

Key findings:
- Specific queries like "PICALM endocytosis" work better than broad queries
- Rate limiting requires proper delays and retry logic
- Email addresses significantly improve API limits
- PaperQA's built-in mechanisms handle most rate limiting automatically

### Configuration Optimization Experience
We learned that:
- Lower concurrency (2-3) works better than higher (5) for public APIs
- Reduced search count (15-20) provides better quality than higher counts
- Proper timeouts (30s for APIs, 600s for overall) prevent failures
- Environment variables are essential for reliable operation

### UI Development Experience
The Gradio UI required careful attention to:
- Real-time status updates without blocking
- Proper error handling and user feedback
- Rate limiting considerations in the UI layer
- Clean separation between UI and business logic

---

## 9. References
- [Paper-QA](https://github.com/Future-House/paper-qa)
- [OpenRouter.ai](https://openrouter.ai/)
- [Ollama](https://ollama.com/)
- [Semantic Scholar API](https://api.semanticscholar.org/)
- [Crossref API](https://api.crossref.org/)