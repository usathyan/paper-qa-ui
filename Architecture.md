# Paper-QA UI Architecture

## Overview

Paper-QA UI is a modern web interface built on top of the [Paper-QA](https://github.com/Future-House/paper-qa) library, providing high-accuracy Retrieval Augmented Generation (RAG) capabilities for scientific documents. The system is designed to work with both local (Ollama) and cloud (OpenRouter) LLM providers.

## System Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Gradio UI     │    │   Paper-QA      │    │   LLM Providers │
│                 │    │   Engine        │    │                 │
│ • File Upload   │◄──►│ • Document      │◄──►│ • Ollama        │
│ • Question      │    │   Indexing      │    │ • OpenRouter    │
│   Interface     │    │ • Evidence      │    │ • Local Models  │
│ • Answer        │    │   Retrieval     │    │                 │
│   Display       │    │ • Answer        │    └─────────────────┘
│ • Status        │    │   Generation    │
│   Updates       │    └─────────────────┘
└─────────────────┘
```

### Data Flow

1. **Document Upload**: PDF files uploaded via Gradio interface
2. **Document Processing**: Files copied to `papers/` directory and indexed into an in-memory `Docs` corpus
3. **Question Processing**: User questions processed by querying the in-memory corpus (`Docs.aquery`)
4. **Evidence Retrieval**: Relevant document sections retrieved using embeddings
5. **Answer Generation**: LLM generates answers with citations
6. **Response Display**: Formatted results shown in web interface

## Technical Implementation

### Frontend (Gradio)

- **Framework**: Gradio 5.39.0
- **Interface**: Modern web UI with real-time updates
- **File Handling**: Robust file upload with duplicate detection
- **Status Tracking**: Live status updates during processing

### Backend (Paper-QA)

- **Core Engine**: Paper-QA v5.27.0
- **Document Processing**: PDF parsing and chunking
- **Embedding**: Vector embeddings for semantic search
- **RAG Pipeline**: Evidence retrieval and answer generation

### Configuration Management

- **ConfigManager**: Centralized configuration loading
- **Settings**: Pydantic-based configuration validation
- **Multiple Profiles**: Support for different LLM/embedding combinations

## Key Features

### Document Management

```python
# Document upload and indexing
async def process_uploaded_files_async(files: List[str]) -> Tuple[str, str]:
    # Handle Gradio file objects
    # Copy files to papers directory
    # Index documents with Paper-QA
    # Return status updates
```

### Question Processing

```python
# Question answering pipeline
async def process_question_async(question: str, config_name: str) -> Tuple[str, str, str, str]:
    # Initialize settings with research-intelligence defaults
    # Query in-memory Docs corpus (Docs.aquery)
    # Generate answer with evidence and metadata
    # Format response
```

### Configuration System

```python
# Configuration loading
def initialize_settings(config_name: str = "optimized_ollama") -> Settings:
    # Load JSON configuration
    # Convert to Paper-QA Settings
    # Validate configuration
    # Return initialized settings
```

## Configuration Profiles

### Optimized Ollama (Default)

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

### OpenRouter + Ollama

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

## Performance Optimizations

### Local Processing

- **Ollama Integration**: Local LLM processing for privacy and speed
- **Embedding Caching**: Efficient vector storage and retrieval
- **Concurrent Processing**: Optimized for single-user workloads

### Evidence Retrieval

- **MMR Search**: Maximum Marginal Relevance for diverse evidence
- **Relevance Scoring**: Evidence ranked by relevance to question
- **Source Tracking**: Full citation and source information

### Memory Management

- **Document Indexing**: Efficient storage of document chunks
- **Session Management**: Clean state management between sessions
- **Resource Cleanup**: Proper cleanup of temporary resources

## Error Handling

### Robust File Processing

- **Gradio Compatibility**: Handles different Gradio file object types
- **Duplicate Detection**: Prevents duplicate file processing
- **Error Recovery**: Graceful handling of processing failures

### Network Resilience

- **Connection Retry**: Automatic retry for network failures
- **Timeout Handling**: Configurable timeouts for long operations
- **Fallback Options**: Multiple configuration options for reliability

## Security Considerations

### Local Processing

- **No Data Leakage**: Local processing keeps documents private
- **API Key Management**: Secure handling of external API keys
- **File Validation**: Input validation for uploaded files

### Access Control

- **Local Access**: UI accessible only on localhost by default
- **Network Isolation**: Optional network access for sharing
- **Session Isolation**: Separate processing sessions per user

## Monitoring and Logging

### Status Tracking

```python
class StatusTracker:
    """Real-time status updates during processing."""
    def add_status(self, status: str):
        # Add timestamped status update
        # Update UI display
        # Log to console
```

### Performance Metrics

- **Processing Time**: Track document indexing and query times
- **Evidence Quality**: Monitor evidence retrieval effectiveness
- **User Feedback**: Real-time status updates for user experience

## Deployment

### Local Development

```bash
# Setup environment
make setup

# Start UI
make ui

# Run tests
make test-ui-functionality
```

### Production Considerations

- **Resource Requirements**: Adequate RAM for document indexing
- **Storage**: Sufficient disk space for document storage
- **Network**: Optional external API access for cloud LLMs

## Future Enhancements

### Planned Features

- **Batch Processing**: Support for multiple document uploads
- **Advanced Search**: Full-text search capabilities
- **Export Options**: Export results in various formats
- **User Management**: Multi-user support with authentication

### Performance Improvements

- **Caching**: Intelligent caching of frequently accessed data
- **Parallel Processing**: Multi-threaded document processing
- **Optimized Embeddings**: Better embedding models and strategies

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Use `make kill-server` to clear ports
2. **Ollama Issues**: Verify Ollama is running and models are available
3. **File Upload Errors**: Check file format and size limits
4. **Memory Issues**: Monitor system resources during processing

### Debug Tools

- **Test Scripts**: Comprehensive test suite for all components
- **Logging**: Detailed logging for troubleshooting
- **Status Updates**: Real-time feedback during operations

## Conclusion

The Paper-QA UI provides a robust, user-friendly interface for scientific document analysis. The architecture balances performance, usability, and reliability while supporting both local and cloud-based processing options. The modular design allows for easy extension and customization to meet specific use cases. 