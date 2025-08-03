# PaperQA Discovery API - Enhanced Backend Schema Documentation

## Overview

The PaperQA Discovery API has been significantly enhanced with comprehensive documentation, improved error handling, and fixes for LiteLLM configuration issues. This document provides detailed explanations of the API schema, endpoints, and configuration improvements.

## API Documentation Enhancements

### 1. Comprehensive Swagger Documentation

The API now includes detailed documentation for all endpoints with:

- **Detailed descriptions** for each endpoint and model
- **Field-level documentation** with examples and constraints
- **Request/response examples** for all operations
- **Error handling documentation** with specific error codes
- **Processing time estimates** for different operations
- **Use case explanations** for each endpoint

### 2. Enhanced Pydantic Models

All Pydantic models now include:

```python
class Query(BaseModel):
    """
    Query request model for asking questions about scientific papers.
    
    This model defines the structure for submitting questions to the PaperQA system.
    The system will search through the specified sources to find relevant information
    and provide evidence-based answers.
    """
    query: str = Field(
        ...,
        description="The question or query to ask about scientific papers",
        example="What are the latest developments in KRAS inhibitors for cancer treatment?",
        min_length=1,
        max_length=1000
    )
    source: Literal["local", "public", "all"] = Field(
        default="all",
        description="""
        The search source to use for answering the query:
        
        - **local**: Only search through uploaded PDF papers in the system
        - **public**: Only search public domain research (requires external API keys)
        - **all**: Search both local papers and public domain research (recommended)
        """,
        example="all"
    )
```

### 3. API Endpoint Categories

Endpoints are now organized into logical categories:

- **System**: Health checks and basic API information
- **Paper Management**: Upload, list, delete, and load papers
- **Question Answering**: Main query functionality

## LiteLLM Configuration Fixes

### Issues Addressed

Based on the [GitHub issue #904](https://github.com/Future-House/paper-qa/issues/904), the following LiteLLM configuration issues have been resolved:

1. **Streaming Configuration**: The `stream` parameter was causing compatibility issues
2. **Caching Configuration**: The `cache` parameter was not accepting boolean values
3. **Model Provider Identification**: Proper model naming with provider prefixes

### Configuration Improvements

#### 1. Disabled Streaming
```python
"litellm_params": {
    "model": "openrouter/z-ai/glm-4.5-air:free",
    "api_key": os.getenv("OPENROUTER_API_KEY"),
    "api_base": "https://openrouter.ai/api/v1",
    "stream": False,  # Disable streaming to avoid compatibility issues
    "timeout": 600,   # 10 minute timeout
    "max_retries": 3, # Retry failed requests
}
```

#### 2. Proper Model Naming
```python
# Correct format with provider prefix
"model": "openrouter/z-ai/glm-4.5-air:free"
# Instead of incorrect: "model": "z-ai/glm-4.5-air:free"
```

#### 3. Enhanced Error Handling
```python
def validate_environment():
    """
    Validate that required environment variables and services are available.
    """
    validation_results = {
        "openrouter_api_key": False,
        "ollama_server": False,
        "messages": []
    }
    
    # Check OpenRouter API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key and openrouter_key.startswith("sk-or-"):
        validation_results["openrouter_api_key"] = True
    else:
        validation_results["messages"].append("OPENROUTER_API_KEY not found or invalid")
    
    # Check if Ollama server is running
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            validation_results["ollama_server"] = True
        else:
            validation_results["messages"].append("Ollama server not responding properly")
    except Exception as e:
        validation_results["messages"].append(f"Ollama server not accessible: {str(e)}")
    
    return validation_results
```

## API Endpoints

### System Endpoints

#### GET `/`
Root endpoint providing basic API information.

**Response:**
```json
{
  "message": "PaperQA Discovery API",
  "version": "2.0.0",
  "description": "A powerful scientific paper question-answering system",
  "documentation": "/docs",
  "health_check": "/health",
  "endpoints": {
    "upload_paper": "/api/upload",
    "list_papers": "/api/papers",
    "delete_paper": "/api/papers/{docname}",
    "load_papers": "/api/load-papers",
    "query": "/api/query"
  }
}
```

#### GET `/health`
Health check endpoint for system monitoring.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "papers_loaded": 5,
  "environment": {
    "openrouter_api_key": true,
    "ollama_server": true
  },
  "messages": []
}
```

### Paper Management Endpoints

#### POST `/api/upload`
Upload a PDF paper to the system.

**Features:**
- File size validation (max 50MB)
- File type validation (PDF only)
- Automatic text extraction and embedding generation
- Error handling with file cleanup

**Request:**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@research_paper.pdf"
```

**Response:**
```json
{
  "message": "Successfully uploaded research_paper.pdf"
}
```

#### GET `/api/papers`
Get list of all loaded papers.

**Response:**
```json
[
  {
    "docname": "KRAS Inhibitors in Cancer Treatment: A Comprehensive Review",
    "citation": "Smith, J. et al. (2024). KRAS Inhibitors in Cancer Treatment. Nature Reviews Cancer, 24(3), 156-172."
  }
]
```

#### DELETE `/api/papers/{docname}`
Delete a specific paper from the system.

**Features:**
- Irreversible operation
- Automatic cleanup of embeddings and indexes
- File removal from upload directory

#### POST `/api/load-papers`
Load all PDF papers from the upload directory.

**Features:**
- Bulk paper loading
- System initialization
- Recovery after system restart

### Question Answering Endpoints

#### POST `/api/query`
Main endpoint for asking questions about scientific papers.

**Request:**
```json
{
  "query": "What are the latest developments in KRAS inhibitors?",
  "source": "all"
}
```

**Response:**
```json
{
  "answer": "KRAS inhibitors have shown promising results...",
  "evidence": [
    {
      "context": "The study found that KRAS inhibitors showed 45% response rate...",
      "source": "KRAS_inhibitors_research_2024.pdf"
    }
  ],
  "sources": [
    {
      "docname": "KRAS Inhibitors in Cancer Treatment: A Comprehensive Review",
      "citation": "Smith, J. et al. (2024). KRAS Inhibitors in Cancer Treatment..."
    }
  ],
  "thinking_details": "Searching for KRAS inhibitors in uploaded papers..."
}
```

## Configuration Options

### Model Selection

The system supports multiple LLM configurations:

```python
# OpenRouter with GLM-4.5-Air (default)
settings = get_settings()

# OpenRouter with Google Gemma
settings = get_settings(use_gemma=True)

# Local Ollama
settings = get_settings(use_ollama=True)
```

### Environment Variables

Required environment variables:

```bash
# OpenRouter API key for cloud LLM
OPENROUTER_API_KEY=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

# Optional: External API keys for public search
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key
CROSSREF_API_KEY=your_crossref_key
```

## Error Handling

### HTTP Status Codes

- **200**: Success
- **400**: Bad Request (invalid file type, size, or parameters)
- **404**: Not Found (paper not found)
- **500**: Internal Server Error (processing failures)

### Error Response Format

```json
{
  "detail": "Detailed error message explaining what went wrong"
}
```

## Performance Considerations

### Processing Times

- **Local queries**: 10-30 seconds
- **Public queries**: 30-60 seconds  
- **All sources**: 30-90 seconds
- **Paper upload**: 5-15 seconds per paper

### File Size Limits

- **Maximum file size**: 50MB
- **Recommended**: Under 20MB for optimal processing speed
- **Supported format**: PDF only

## Monitoring and Debugging

### Health Check

Use the `/health` endpoint to monitor system status:

```bash
curl http://localhost:8000/health
```

### Logging

The system provides detailed logging:

- **LiteLLM**: Set to WARNING level to reduce noise
- **PaperQA**: Set to DEBUG level to show thinking process
- **Custom handlers**: Capture thinking details for transparency

### Environment Validation

The system automatically validates:

- OpenRouter API key presence and format
- Ollama server accessibility
- Required environment variables

## Best Practices

### 1. Query Optimization

- Use specific, focused questions
- Choose appropriate search source (local/public/all)
- Consider processing time for complex queries

### 2. File Management

- Keep uploaded papers organized
- Use descriptive filenames
- Monitor disk space for embeddings

### 3. Error Handling

- Always check HTTP status codes
- Handle timeout scenarios (120-second timeout)
- Implement retry logic for transient failures

### 4. Security

- Validate file uploads
- Sanitize query inputs
- Monitor API usage

## Troubleshooting

### Common Issues

1. **"LLM Provider NOT provided"**: Check model naming with provider prefix
2. **"Paper not found"**: Verify paper exists and is properly loaded
3. **"Ollama server not accessible"**: Ensure Ollama is running on port 11434
4. **"OpenRouter API key not configured"**: Set OPENROUTER_API_KEY environment variable

### Debug Steps

1. Check health endpoint: `curl http://localhost:8000/health`
2. Verify environment: Check environment validation results
3. Test paper loading: Use `/api/load-papers` endpoint
4. Check logs: Monitor backend console output

## Future Enhancements

### Planned Improvements

1. **Streaming Support**: Re-enable streaming once LiteLLM compatibility is resolved
2. **Caching**: Implement proper caching for improved performance
3. **Authentication**: Add API key authentication for production use
4. **Rate Limiting**: Implement request rate limiting
5. **Metrics**: Add detailed performance metrics and monitoring

### Configuration Flexibility

The system is designed to easily support:

- Additional LLM providers
- Custom embedding models
- Different document formats
- Enhanced search algorithms

## References

- [PaperQA GitHub Repository](https://github.com/Future-House/paper-qa)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [GitHub Issue #904 - LiteLLM Configuration](https://github.com/Future-House/paper-qa/issues/904) 