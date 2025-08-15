# Paper-QA UI: Developer Documentation

This document provides comprehensive technical documentation for maintainers and developers working on Paper-QA UI.

## System Architecture

### Overview

Paper-QA UI is a modern web interface built on top of the [Paper-QA](https://github.com/Future-House/paper-qa) library, providing high-accuracy Retrieval Augmented Generation (RAG) capabilities for scientific documents.

### Core Components

- **Frontend**: Gradio 5.x with modern web UI and real-time updates
- **Backend**: Paper-QA v5.27.0+ with PDF parsing and RAG pipeline
- **Configuration**: Centralized JSON-based configuration management
- **Execution Model**: Dedicated asyncio event loop for all LLM/embedding I/O

### Data Flow

1. **Document Upload**: PDF files uploaded via Gradio interface
2. **Document Processing**: Files copied to `papers/` directory and indexed into in-memory `Docs` corpus
3. **Question Processing**: User questions processed by querying the in-memory corpus (`Docs.aquery`)
4. **Evidence Retrieval**: Relevant document sections retrieved using embeddings
5. **Answer Generation**: LLM generates answers with citations
6. **Response Display**: Formatted results shown in web interface

## Setup and Launch

### Prerequisites

- Python 3.11+
- Ollama running for local models (default setup)
- Optional: Cloud LLM API keys for external providers

### Installation

```bash
# Setup environment and dependencies
make setup

# Start the UI
make ui

# Access at http://localhost:7860
```

### Environment Configuration

- Default configuration uses optimized Ollama setup
- External providers configured via `configs/*.json` and `.env` file
- API keys managed through environment variables

## Core Implementation

### File Structure

```
src/
├── ui/
│   ├── paperqa2_ui.py          # Main UI implementation
│   ├── prompts.py              # LLM prompts for query rewriting
│   └── config_ui.py            # Configuration UI components
├── config_manager.py           # JSON config loading and Settings conversion
├── cli/                        # Command-line interfaces
└── utils.py                    # Utility functions
```

### Threading and Execution Model

- **Dedicated asyncio event loop**: Runs in background thread for all LLM/embedding I/O
- **Thread-safe execution**: All Paper-QA async calls scheduled via `asyncio.run_coroutine_threadsafe`
- **Single-query lock**: Prevents client contention and ensures stability

### State Management

```python
app_state = {
    "docs": None,                    # In-memory Docs corpus
    "settings": None,                # Current Paper-QA Settings
    "uploaded_docs": [],             # List of processed documents
    "status_tracker": None,          # Real-time status updates
    "rewrite_info": None,            # Query rewrite information
    "rewrite_debug": None,           # Debug info for rewrite process
    "session_data": None,            # Current session data
    "ui_toggles": {},                # UI display toggles
    "curation": {},                  # Evidence curation settings
}
```

## Query Processing Pipeline

### Document Intake

```python
async def process_uploaded_files_async(files: List[str]) -> Tuple[str, str]:
    """
    1. Handle Gradio file objects (different types across versions)
    2. Copy files to papers/ directory with duplicate detection
    3. Index documents using Docs.aadd()
    4. Update status tracker with progress
    """
```

### Question Processing

```python
async def process_question_async(question: str, config_name: str) -> Tuple[str, str, str, str]:
    """
    1. Initialize settings with research-oriented defaults
    2. Apply query rewriting if enabled
    3. Execute Docs.aquery() against in-memory corpus
    4. Generate formatted response with evidence and metadata
    """
```

### Query Rewriting System

The system supports both heuristic and LLM-based query rewriting:

#### LLM-Based Rewriting

```python
async def llm_decompose_query(question: str, settings: Settings) -> Dict[str, Any]:
    """
    Uses configured LLM to rewrite query and extract filters.
    
    Returns:
    {
        "rewritten": str,
        "filters": {
            "years": [int, int] | null,
            "venues": string[],
            "fields": string[],
            "species": string[],
            "study_types": string[],
            "outcomes": string[]
        }
    }
    """
```

#### Prompts System

External prompts in `src/ui/prompts.py`:

- `REWRITE_SYSTEM_PROMPT`: Instructs LLM on rewriting approach
- `REWRITE_USER_TEMPLATE`: Template for user query with JSON schema
- `QUOTE_EXTRACTION_SYSTEM_PROMPT`: For evidence quote extraction
- `QUOTE_EXTRACTION_USER_TEMPLATE`: Template for quote extraction

#### Heuristic Fallback

```python
def rewrite_query(question: str, settings: Settings) -> str:
    """
    Lightweight local rewriting:
    - Remove polite fillers ("please", "kindly")
    - Convert "what is/are" to "summarize"
    - Normalize whitespace and punctuation
    """
```

### Evidence Curation

The system provides multiple levels of evidence control:

#### Curation Controls

- **Score cutoff**: `answer.evidence_relevance_score_cutoff` (0.0-1.0)
- **Max sources**: `answer.answer_max_sources` (total sources limit)
- **Per-document cap**: Post-selection pruning per source

#### Implementation

```python
# Settings mutation on initialization
settings.answer.evidence_relevance_score_cutoff = 0
settings.answer.evidence_k = 15  # Higher for richer evidence
settings.answer.answer_max_sources = 10
settings.answer.get_evidence_if_no_contexts = True
settings.answer.group_contexts_by_question = True
settings.answer.answer_filter_extra_background = True
```

## Configuration System

### Configuration Profiles

The system supports multiple configuration profiles in `configs/`:

#### Optimized Ollama (Default)

```json
{
  "llm": "ollama/llama3.2",
  "embedding": "ollama/nomic-embed-text",
  "answer": {
    "evidence_k": 15,
    "answer_max_sources": 10,
    "max_concurrent_requests": 2,
    "get_evidence_if_no_contexts": true,
    "group_contexts_by_question": true,
    "answer_filter_extra_background": true
  },
  "temperature": 0.2
}
```

#### OpenRouter Integration

```json
{
  "llm": "openrouter/anthropic/claude-3.5-sonnet",
  "embedding": "ollama/nomic-embed-text",
  "llm_config": {
    "api_key": "${OPENROUTER_API_KEY}",
    "base_url": "https://openrouter.ai/api/v1"
  }
}
```

### Settings Initialization

```python
def initialize_settings(config_name: str = "optimized_ollama") -> Settings:
    """
    1. Load JSON configuration from configs/
    2. Convert to Paper-QA Settings object
    3. Apply research-oriented defaults
    4. Validate configuration
    """
```

## UI Components and Flow

### Main Interface Structure

The UI follows a three-panel layout:

- **Left Panel**: Configuration, upload, and controls
- **Center Panel**: Question input, rewrite interface, and run controls
- **Right Panel**: Results display (answer, sources, intelligence, metadata)

### Research Intelligence Features

#### Contradiction Detection

- **Heuristic antonym detection**: Cross-document analysis
- **Polarity clustering**: Verb→polarity mapping with entity grouping
- **Conflict visualization**: Entity-based grouping with source counts

#### Quality Indicators

- **Source flags**: Preprint detection (arXiv, bioRxiv, medRxiv)
- **Retraction detection**: Title-based heuristics
- **Venue information**: Journal/conference display when available

#### MMR Visualization

- **Selected diversity**: Score histograms and diversity metrics
- **Candidate overlay**: Comparison of candidates vs selected evidence
- **Transparency metrics**: Detailed retrieval and selection statistics

## Performance and Optimization

### Local Processing Optimizations

- **Ollama integration**: Optimized for single-user local workloads
- **Concurrent request limiting**: `max_concurrent_requests = 1` for stability
- **Memory management**: Efficient in-memory document indexing
- **Resource cleanup**: Proper cleanup of temporary resources

### Evidence Retrieval Optimizations

- **MMR search**: Maximum Marginal Relevance for diverse evidence selection
- **Relevance scoring**: Multi-stage evidence ranking
- **Source tracking**: Complete citation and provenance information
- **Caching**: Efficient vector storage and retrieval

## Error Handling

### Robust File Processing

- **Gradio compatibility**: Handles different file object types across versions
- **Duplicate detection**: SHA-256 based deduplication
- **Error recovery**: Graceful handling of processing failures
- **Progress tracking**: Real-time status updates with error reporting

### Network Resilience

- **Connection retry**: Automatic retry with exponential backoff
- **Timeout handling**: Configurable timeouts for long operations
- **Fallback options**: Multiple provider configurations for reliability
- **Loop management**: Proper asyncio loop handling to prevent conflicts

## Testing and Development

### Test Suite

```bash
# Run all tests
make test

# Code quality
make format                # Code formatting
make lint                  # Linting and style checks
make type-check            # Static type checking
```

### Development Workflow

1. **Setup**: `make setup` for environment initialization
2. **Development**: `make ui` for live development
3. **Testing**: `make test` before commits
4. **Debugging**: Enable debug logging for troubleshooting

## Troubleshooting

### Common Issues and Solutions

#### Ollama Connection Issues

**Problem**: `Connection refused` or model not found errors

**Solutions**:
1. Verify Ollama is running: `ollama serve`
2. Check model availability: `ollama list`
3. Download required models: `ollama pull llama3.2`

#### Performance Issues

**Problem**: Slow response times or timeouts

**Solutions**:
1. Reduce `evidence_k` to 10-12 (default is 15+)
2. Set `max_concurrent_requests: 1`
3. Lower `answer_max_sources` to 5-7
4. Increase timeout values in configuration

#### Memory Issues

**Problem**: Out of memory during processing

**Solutions**:
1. Reduce `chunk_size` in parsing settings
2. Lower `num_ctx` for models with limited VRAM
3. Use smaller models for resource-constrained environments
4. Monitor system resources during processing

#### Configuration Issues

**Problem**: Settings not applied or JSON parsing errors

**Solutions**:
1. Validate JSON syntax in configuration files
2. Restart application after configuration changes
3. Check file paths and permissions
4. Review logs for specific error messages

### Debug Tools and Utilities

```bash
# Environment status check
make check-env

# Clean data for fresh start
make clean-data        # Preserves papers/
make clean-all-data    # Complete reset

# Kill hanging processes
make kill-server
```

## Roadmap and Future Development

### Completed Features

- ✅ Analysis Progress with live updates and transparency metrics
- ✅ MMR visualization with candidate/selected comparison
- ✅ Research Intelligence: contradictions, insights, evidence summary
- ✅ Source quality flags and reputation indicators
- ✅ LLM-based query rewriting with filter extraction
- ✅ Evidence curation controls and preview
- ✅ Export functionality (JSON/CSV/JSONL/ZIP)
- ✅ Comprehensive error handling and recovery

### High Priority Next Steps

#### Evidence Curation Enhancements

- **Real-time preview refinements**: Apply cutoff adjustments to histograms
- **Venue quality indicators**: Enhanced reputation scoring when metadata available
- **Conflicts drill-down**: Expandable polarity-grouped excerpts

#### MMR Visualization Improvements

- **Hook-based candidate capture**: Replace log parsing with deterministic hooks
- **Enhanced diversity metrics**: More sophisticated diversity measurements
- **Export integration**: Include candidate/selected sets in exports

#### Live Analytics

- **Tool calls monitoring**: Real-time operation tracking
- **Performance dashboard**: Comprehensive metrics display
- **Pause/resume functionality**: Control over long-running operations

### Technical Debt and Improvements

- **Async/await consistency**: Full migration to async patterns
- **Type safety**: Enhanced type annotations throughout
- **Test coverage**: Comprehensive test suite expansion
- **Documentation**: API documentation generation
- **Performance profiling**: Systematic optimization opportunities

## Conclusion

Paper-QA UI provides a robust, user-friendly interface for scientific document analysis with a focus on transparency, accuracy, and reproducibility. The architecture balances performance with usability while maintaining extensibility for future enhancements.

For additional support or contributions, please refer to the project repository and community resources.
