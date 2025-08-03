# Paper-QA Architecture

## Overview

This document describes the technical architecture of the Paper-QA project, which provides a clean, focused implementation of Paper-QA using OpenRouter.ai with Google Gemini 2.5 Flash Lite model and Ollama's nomad-embed-text for embeddings.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │    │   Paper-QA      │    │   Output        │
│                 │    │   Core          │    │                 │
│ - Questions     │───▶│ - Query Engine  │───▶│ - Answers       │
│ - Paper Files   │    │ - Embeddings    │    │ - Citations     │
│ - Config        │    │ - LLM Interface │    │ - Sources       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Local Papers  │    │   Public APIs   │    │   Streaming     │
│                 │    │                 │    │                 │
│ - PDF Files     │    │ - Semantic      │    │ - Console       │
│ - Indexes       │    │   Scholar       │    │ - Rich UI       │
│ - Embeddings    │    │ - Crossref      │    │ - Files         │
└─────────────────┘    │ - OpenAlex      │    └─────────────────┘
                       └─────────────────┘
```

### Core Components

#### 1. Paper-QA Core (`src/paper_qa_core.py`)

The central component that orchestrates all Paper-QA operations:

- **PaperQACore Class**: Main interface for all Paper-QA operations
- **Query Functions**: Three main query types (local, public, combined)
- **Error Handling**: Robust error handling with tenacity retry logic
- **Streaming Support**: Real-time response streaming

**Key Methods:**
```python
class PaperQACore:
    async def query_local_papers(question, paper_directory, callbacks)
    async def query_public_sources(question, callbacks)
    async def query_combined(question, paper_directory, callbacks)
```

#### 2. Configuration Management (`src/config_manager.py`)

Manages all configuration aspects of the system:

- **ConfigManager Class**: Handles JSON configuration files
- **Environment Setup**: Loads and validates environment variables
- **Configuration Validation**: Ensures required settings are present
- **Dynamic Configuration**: Supports runtime configuration changes

**Configuration Structure:**
```json
{
  "llm": "openrouter/google/gemini-2.5-flash-lite",
  "embedding": "ollama/nomad-embed-text",
  "agent": {
    "agent_type": "ToolSelector",
    "search_count": 8,
    "timeout": 500.0
  },
  "answer": {
    "evidence_k": 10,
    "answer_max_sources": 5
  }
}
```

#### 3. Streaming System (`src/streaming.py`)

Provides real-time response streaming capabilities:

- **StreamingCallback Base Class**: Abstract base for all streaming callbacks
- **ConsoleStreamingCallback**: Simple console output
- **RichStreamingCallback**: Rich-formatted output with progress
- **ProgressStreamingCallback**: Progress bar with status updates
- **FileStreamingCallback**: File output with timestamps
- **MultiStreamingCallback**: Combines multiple streaming methods

**Usage Example:**
```python
callback = create_multi_callback(
    console=True,
    progress=True,
    file="output.txt"
)
```

#### 4. Utilities (`src/utils.py`)

Common utility functions and helpers:

- **File Operations**: JSON save/load, directory management
- **System Status**: Ollama and OpenRouter.ai health checks
- **Result Management**: Save and format query results
- **Question Management**: PICALM research questions

## Data Flow

### 1. Local Papers Query Flow

```
User Question → PaperQACore → Docs Object → Local PDFs → Embeddings → LLM → Answer
     │              │              │            │            │         │
     ▼              ▼              ▼            ▼            ▼         ▼
Streaming      Configuration   Paper Index   nomad-embed   Gemini    Citations
Callbacks         Settings      Tantivy       -text        2.5 Flash
```

### 2. Public Sources Query Flow

```
User Question → PaperQACore → Agent System → Search Tools → Public APIs → LLM → Answer
     │              │              │             │             │         │
     ▼              ▼              ▼             ▼             ▼         ▼
Streaming      Configuration   ToolSelector   Semantic      Gemini    Citations
Callbacks         Settings      Agent         Scholar      2.5 Flash
```

### 3. Combined Query Flow

```
User Question → PaperQACore → Local Query → Public Query → Result Merge → Final Answer
     │              │              │             │              │
     ▼              ▼              ▼             ▼              ▼
Streaming      Configuration   Local Papers  Public APIs   Combined
Callbacks         Settings      + Embeddings  + Search      Results
```

## Technology Stack

### Core Dependencies

- **Paper-QA**: Main RAG framework
- **OpenRouter.ai**: LLM provider (Google Gemini 2.5 Flash Lite)
- **Ollama**: Local embedding model (nomad-embed-text)
- **Tenacity**: Retry logic and error handling
- **Rich**: Rich console output and formatting
- **Pydantic**: Data validation and settings management

### External Services

#### OpenRouter.ai
- **Model**: Google Gemini 2.5 Flash Lite
- **API**: REST API with authentication
- **Rate Limits**: Configurable based on plan
- **Features**: Streaming, function calling, reasoning

#### Ollama
- **Model**: nomad-embed-text
- **API**: Local HTTP API (localhost:11434)
- **Features**: Local embeddings, no rate limits
- **Performance**: Fast, private, offline-capable

#### Public APIs (No Authentication Required)
- **Semantic Scholar**: Research paper search and metadata
- **Crossref**: DOI resolution and paper metadata
- **OpenAlex**: Academic paper database
- **Unpaywall**: Open access information

## Configuration Architecture

### Configuration Hierarchy

```
1. Environment Variables (.env)
2. Configuration Files (configs/*.json)
3. Default Settings (paper-qa defaults)
4. Runtime Overrides (programmatic)
```

### Configuration Types

#### 1. Default Configuration (`configs/default.json`)
- Base configuration for all operations
- Balanced settings for general use
- OpenRouter.ai + Ollama setup

#### 2. OpenRouter.ai Configuration (`configs/openrouter.json`)
- OpenRouter.ai specific settings
- API configuration and authentication
- Model-specific parameters

#### 3. Ollama Configuration (`configs/ollama.json`)
- Ollama embedding model settings
- Local API configuration
- Model parameters

#### 4. Scenario Configurations
- **Local Only** (`configs/local_only.json`): Optimized for local papers
- **Public Only** (`configs/public_only.json`): Optimized for public sources
- **Combined** (`configs/combined.json`): Optimized for mixed sources

## Error Handling and Resilience

### Retry Strategy

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
```

### Error Categories

1. **Network Errors**: API timeouts, connection failures
2. **Rate Limiting**: API quota exceeded
3. **Authentication Errors**: Invalid API keys
4. **Model Errors**: LLM/embedding model failures
5. **File System Errors**: Paper loading, index issues

### Graceful Degradation

- **Local Fallback**: Use local papers when public APIs fail
- **Model Fallback**: Switch to alternative models if primary fails
- **Partial Results**: Return partial answers when possible
- **Error Reporting**: Comprehensive error messages and logging

## Performance Considerations

### Optimization Strategies

1. **Embedding Caching**: Cache embeddings to avoid recomputation
2. **Index Management**: Efficient paper indexing and retrieval
3. **Concurrent Processing**: Parallel API calls where possible
4. **Streaming**: Real-time response generation
5. **Memory Management**: Efficient handling of large paper collections

### Resource Requirements

- **CPU**: Moderate (embedding generation, text processing)
- **Memory**: Variable (depends on paper collection size)
- **Storage**: Variable (paper files, indexes, embeddings)
- **Network**: Low for local, high for public queries

## Security Considerations

### Data Privacy

- **Local Processing**: Papers processed locally with Ollama
- **No Data Storage**: No user data stored on external servers
- **API Key Management**: Secure environment variable handling
- **Network Security**: HTTPS for all external API calls

### Access Control

- **Local Files**: Standard file system permissions
- **API Keys**: Environment variable protection
- **No Authentication**: No user accounts or sessions

## Monitoring and Observability

### Logging

- **Verbosity Levels**: 0-3 (minimal to detailed)
- **Structured Logging**: JSON format for machine processing
- **Performance Metrics**: Query duration, success rates
- **Error Tracking**: Comprehensive error logging

### Health Checks

- **Ollama Status**: Local embedding service health
- **OpenRouter.ai Status**: External LLM service health
- **Configuration Validation**: Settings verification
- **System Resources**: Memory, disk space monitoring

## Testing Strategy

### Test Types

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction testing
3. **End-to-End Tests**: Full workflow testing
4. **Performance Tests**: Load and stress testing

### Test Coverage

- **Core Functions**: All main query functions
- **Configuration**: Settings loading and validation
- **Streaming**: Real-time response handling
- **Error Handling**: Retry logic and error recovery
- **System Status**: Health check functionality

## Deployment Considerations

### Environment Setup

1. **Python Environment**: Python 3.11+ with virtual environment
2. **Ollama Installation**: Local Ollama server with nomad-embed-text
3. **API Keys**: OpenRouter.ai API key configuration
4. **Paper Directory**: Local PDF collection setup

### Production Considerations

- **Resource Scaling**: Handle large paper collections
- **Backup Strategy**: Paper collection and index backup
- **Monitoring**: System health and performance monitoring
- **Updates**: Regular dependency and model updates

## Future Enhancements

### Planned Features

1. **Web Interface**: React-based web UI
2. **Advanced Analytics**: Query analytics and insights
3. **Multi-language Support**: Non-English paper processing
4. **Collaborative Features**: Shared paper collections
5. **Advanced Search**: Semantic search capabilities

### Technical Improvements

1. **Vector Database**: Replace Tantivy with dedicated vector DB
2. **Model Optimization**: Quantized models for better performance
3. **Caching Layer**: Redis-based caching for frequent queries
4. **Microservices**: Service-oriented architecture
5. **Containerization**: Docker deployment support 