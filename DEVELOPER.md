# Developer Documentation

## Architecture Overview

### System Architecture

```mermaid
graph TB
    A[Gradio UI] --> B[Paper-QA Engine]
    B --> C[Document Processor]
    B --> D[Query Processor]
    B --> E[Evidence Retriever]
    
    C --> F[PDF Parser]
    C --> G[Text Chunker]
    C --> H[Embedding Generator]
    
    D --> I[Question Analyzer]
    D --> J[Answer Generator]
    
    E --> K[Vector Search]
    E --> L[Relevance Scoring]
    
    H --> M[Ollama Embeddings]
    J --> N[LLM Provider]
    K --> O[Vector Index]
    
    N --> P[Local Ollama]
    N --> Q[Azure OpenAI]
    N --> R[AWS Bedrock]
    N --> S[OpenRouter]
```

### Data Flow

```mermaid
sequenceDiagram
    participant U as User
    participant G as Gradio UI
    participant P as Paper-QA
    participant E as Embeddings
    participant L as LLM
    participant I as Index
    
    U->>G: Upload PDF
    G->>P: Copy to papers directory
    P->>G: Document ready
    
    U->>G: Ask Question
    G->>P: Query with Docs.aquery() over in-memory corpus
    P->>E: Generate embeddings
    E->>I: Search vectors
    I->>P: Return evidence
    P->>L: Generate answer
    L->>P: Return answer
    P->>G: Display results
    G->>U: Show answer + sources
```

### Component Architecture

```mermaid
graph LR
    subgraph "Frontend Layer"
        A[Gradio Interface]
        B[File Upload]
        C[Question Input]
        D[Results Display]
    end
    
    subgraph "Application Layer"
        E[Config Manager]
        F[Settings Handler]
        G[Status Tracker]
    end
    
    subgraph "Core Engine"
        H[Paper-QA Docs.aquery()]
        I[Document Storage]
        J[Query Processing]
    end
    
    subgraph "Provider Layer"
        K[Ollama Provider]
        L[Azure Provider]
        M[Bedrock Provider]
        N[OpenRouter Provider]
    end
    
    A --> E
    B --> I
    C --> J
    E --> F
    F --> H
    H --> K
    H --> L
    H --> M
    H --> N
```

## Technical Implementation

### Core Components

#### 1. Gradio UI (`src/ui/paperqa2_ui.py`)
- **Purpose**: Web interface for document upload and question answering
- **Key Functions**:
  - `process_uploaded_files_async()`: Handle file uploads, copy to `papers/`, and index into an in-memory `Docs` corpus
  - `process_question_async()`: Query the in-memory corpus with `Docs.aquery(...)` (aligned with CLI behavior)
  - Live Analysis Progress: emits retrieval/summary/answer phase events via a background queue and renders:
    - Chevron phase badges (Retrieval/Summaries/Answer)
    - Retrieval progress bar (contexts_selected / evidence_k)
    - Transparency panel (scores min/mean/max, per‑doc counts, prompt size, elapsed, attempts)
  - `initialize_settings()`: Load and configure Paper-QA settings; applies research-intelligence defaults
  - Query rewrite (advanced):
    - `llm_decompose_query(question, settings) -> Dict[str, Any]`: Calls the configured LLM (via litellm) to produce `{ rewritten, filters { years, venues, fields } }`. Runs on a dedicated asyncio loop with `asyncio.run_coroutine_threadsafe` to avoid loop-binding issues. Defensive JSON parsing strips code fences and falls back gracefully.
    - UI toggles: `use_llm_rewrite`, `bias_retrieval`. When biasing, filter hints are appended to the rewritten string for retrieval.
    - `app_state["rewrite_info"]` stores original/rewritten/filters/bias flags; exported in `session_data.rewrite`.
  - Evidence curation:
    - UI controls: `score_cutoff`, `per_doc_cap`, `max_sources`
    - Applied as: cutoff and max_sources on `settings.answer` pre-query; `per_doc_cap` post-query to prune contexts per source
    - `app_state["curation"]` persisted to `session_data.curation` for exports
  - Critique rendering: `_render_markdown_inline` converts minimal markdown (links, bold, italics, code) for critique bullets
  - MMR visualization:
    - Selected evidence histogram and diversity share from `contexts`
    - Candidate overlay parsed heuristically from retrieval logs (temporary until hooks expose candidates). Events: `mmr` and `mmr_candidates` update the live panel.

#### 2. Configuration Manager (`src/config_manager.py`)
- **Purpose**: Manage different LLM/embedding configurations
- **Key Functions**:
  - `load_config()`: Load JSON configuration files
  - `get_settings()`: Convert config to Paper-QA Settings object
  - `list_configs()`: List available configurations

#### 3. Paper-QA Integration
- **ask() Function**: Main interface for querying documents (synchronous)
- **Settings Object**: Configuration for LLM, embeddings, and processing parameters
- **Document Storage**: Files stored in `./papers/` directory

### Configuration System

#### Configuration Structure
```json
{
  "llm": "provider/model",
  "embedding": "provider/model",
  "llm_config": {
    "api_key": "${ENV_VAR}",
    "api_base": "endpoint_url"
  },
  "embedding_config": {
    "api_base": "endpoint_url"
  },
  "answer": {
    "evidence_k": 20,
    "answer_max_sources": 7
  },
  "agent": {
    "index": {
      "paper_directory": "./papers"
    }
  }
}
```

#### Environment Variables
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region
- `OPENROUTER_API_KEY`: OpenRouter API key

### File Processing Pipeline

```mermaid
flowchart TD
    A[PDF Upload] --> B[File Validation]
    B --> C[Copy to Papers Directory]
    C --> D[Update UI Status]
    D --> E[Ready for Queries]
```

### Query Processing Pipeline

```mermaid
flowchart TD
    A[Question Input] --> B[Load Settings]
    B --> C[Query in-memory Docs corpus]
    C --> D[Paper-QA Retrieval]
    D --> E[Evidence Selection / Summaries]
    E --> F[Prompt Build + Answer Generation]
    F --> G[Format Response]
    G --> H[Display Results]
```

## Development Setup

### Prerequisites
```bash
# Install Python 3.11+
# Install Ollama
# Install uv package manager
```

### Local Development
```bash
# Clone repository
git clone <repository-url>
cd paper-qa-ui

# Setup environment
make setup

# Start development server
make ui

# Run tests
make test
```

### Testing
```bash
# Test basic functionality
make test

# Test CLI
make test-cli

# Run CLI example
make cli-example
```

## Debugging

### Common Issues

#### 1. File Upload Errors
```python
# Check Gradio file object handling
if hasattr(file_obj, 'name'):
    source_path = Path(file_obj.name)
else:
    source_path = Path(file_obj)
```

#### 2. Configuration Loading
```python
# Verify configuration loading
config_manager = ConfigManager()
config_dict = config_manager.load_config("config_name")
settings = Settings(**config_dict)
```

#### 3. Ollama Connection
```bash
# Check Ollama status
ollama list
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

#### 4. Port Conflicts
```bash
# Kill existing processes
make kill-server

# Check port usage
lsof -i :7860
```

### Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("paperqa").setLevel(logging.INFO)
logging.getLogger("litellm").setLevel(logging.WARNING)
```

### Debug Tools
```bash
# Test specific components
python scripts/test_complete_workflow.py

# Check environment
make check-env
```

## Code Structure

### Key Files
- `src/ui/paperqa2_ui.py`: Main Gradio UI application
- `src/config_manager.py`: Configuration management
- `src/paper_qa_core.py`: CLI functionality
- `configs/*.json`: Configuration profiles
- `scripts/test_complete_workflow.py`: Main test script
- `src/cli/paper_qa_cli.py`: CLI interface
- `scripts/kill_server.py`: Process management
- `Makefile`: Build and management commands

### Configuration Files
- `optimized_ollama.json`: Local processing (default)
- `azure_openai.json`: Azure OpenAI integration
- `amazon_bedrock.json`: AWS Bedrock integration
- `openrouter_ollama.json`: OpenRouter integration
- `clinical_trials.json`: Clinical trials search
- `ollama.json`: Basic Ollama setup

## Performance Optimization

### Local Processing
- Use Ollama for both LLM and embeddings
- Optimize chunk size and overlap settings
- Configure evidence retrieval parameters (defaults enable pre-search, higher evidence_k, grouping, retries)

### Cloud Processing
- Use local embeddings with cloud LLMs
- Configure API timeouts and retries
- Monitor API usage and costs

### Memory Management
- Process documents in batches
- Clean up temporary resources
- Monitor memory usage during indexing

## Security Considerations

### Local Processing
- No data leaves local machine
- Secure API key management
- Input validation for uploaded files

### Cloud Processing
- Secure API key storage
- Network security for API calls
- Data privacy compliance

## Deployment

### Local Deployment
```bash
make ui
# Access at http://localhost:7860
```

### Production Considerations
- Resource requirements (RAM, CPU)
- Storage for documents and indexes
- Network access for cloud providers
- Security and access control

## Contributing

### Development Workflow
1. Fork repository
2. Create feature branch
3. Make changes
4. Run tests
5. Submit pull request

### Code Standards
- Follow Python PEP 8
- Add type hints
- Include docstrings
- Write tests for new features

### Testing Requirements
- All new features must have tests
- UI functionality must be tested
- Configuration changes must be validated
- Performance impact must be assessed