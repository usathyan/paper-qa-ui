# PaperQA Discovery - Developer Documentation

This document provides comprehensive technical information for developers working on the PaperQA Discovery project.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Development Setup](#development-setup)
- [Frontend Development](#frontend-development)
- [Backend Development](#backend-development)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing Guidelines](#contributing-guidelines)

## Project Overview

PaperQA Discovery is a full-stack web application that provides an intuitive interface for the PaperQA2 scientific paper question-answering system. The project consists of:

- **Frontend**: React 18 + TypeScript application with modern UI/UX
- **Backend**: FastAPI + PaperQA2 Python application with comprehensive API documentation
- **AI Models**: OpenRouter.ai integration for LLM functionality with Ollama for embeddings

### Key Technologies

- **Frontend**: React 18, TypeScript, CSS3, Modern UI components
- **Backend**: FastAPI, PaperQA2, LiteLLM, Pydantic, Enhanced documentation
- **AI**: OpenRouter.ai (LLM), Ollama (embeddings)
- **Package Management**: uv (Python), npm (Node.js)
- **Development**: Hot reloading, TypeScript compilation, Health monitoring

## Architecture

### System Architecture

```
┌─────────────────┐    HTTP/JSON    ┌─────────────────┐
│   React App     │ ◄─────────────► │   FastAPI       │
│   (Port 3000)   │                 │   (Port 8000)   │
└─────────────────┘                 └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   PaperQA2      │
                                    │   Engine        │
                                    └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   OpenRouter.ai │
                                    │   (LLM) +       │
                                    │   Ollama        │
                                    │   (Embeddings)  │
                                    └─────────────────┘
```

### Frontend Architecture

```
frontend/src/
├── components/          # React components
│   ├── Query.tsx       # Main query interface with source selection
│   └── Library.tsx     # Document management (if needed)
├── App.tsx             # Main application component
├── index.tsx           # Application entry point
└── App.css             # Global styles
```

### Backend Architecture

```
api/
├── main.py             # FastAPI application with enhanced documentation
├── config.py           # LiteLLM configuration with OpenRouter.ai
├── uploaded_papers/    # Document storage directory
└── ...

src/paperqa/            # PaperQA2 core library
├── agents/             # Agent implementations
├── clients/            # External API clients
├── configs/            # Configuration presets
└── ...
```

## Development Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **uv** package manager: `pip install uv`
- **Ollama** (for embeddings)
- **OpenRouter API Key** (for LLM functionality)

### Initial Setup

1. **Clone and navigate to project**
   ```bash
   git clone https://github.com/Future-House/paper-qa-ui.git
   cd paper-qa-ui
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   uv pip install -e .
   ```

3. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Configure environment variables**
   ```bash
   # Create .env file
   echo "OPENROUTER_API_KEY=your_openrouter_api_key_here" > .env
   ```

5. **Start Ollama for embeddings**
   ```bash
   ollama pull nomic-embed-text:latest
   ```

### Development Commands

```bash
# Start both frontend and backend
make run

# Start only backend
make backend

# Start only frontend
make frontend

# Stop all services
make stop

# Clean up
make clean
```

## Frontend Development

### Project Structure

```
frontend/
├── public/             # Static assets
├── src/
│   ├── components/     # React components
│   ├── App.tsx         # Main app component
│   ├── index.tsx       # Entry point
│   └── App.css         # Global styles
├── package.json        # Dependencies
└── tsconfig.json       # TypeScript config
```

### Key Components

#### Query.tsx
- Main query interface with source selection
- Real-time processing with loading states
- Error handling and user feedback
- Thinking transparency display

#### App.tsx
- Application routing and layout
- Global state management
- API integration

### Development Workflow

1. **Start development server**
   ```bash
   cd frontend
   npm start
   ```

2. **Code changes**
   - Hot reloading enabled
   - TypeScript compilation
   - ESLint warnings in console

3. **Testing**
   ```bash
   npm test
   ```

## Backend Development

### Project Structure

```
api/
├── main.py             # FastAPI application
├── config.py           # LiteLLM configuration
└── uploaded_papers/    # Document storage

src/paperqa/            # PaperQA2 core
├── agents/             # Agent implementations
├── clients/            # External API clients
├── configs/            # Configuration presets
└── ...
```

### Key Features

#### Enhanced API Documentation
- Comprehensive Swagger documentation
- Detailed field descriptions and examples
- Error handling documentation
- Health check endpoints

#### LiteLLM Configuration
- OpenRouter.ai integration
- Proper model naming with provider prefixes
- Streaming and caching fixes
- Environment validation

#### Health Monitoring
- System status endpoints
- Environment validation
- Service availability checks

### Development Workflow

1. **Start backend server**
   ```bash
   make backend
   ```

2. **API documentation**
   - Available at http://localhost:8000/docs
   - Health check at http://localhost:8000/health

3. **Testing endpoints**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Test query
   curl -X POST http://localhost:8000/api/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What is PaperQA?", "source": "public"}'
   ```

## API Documentation

### Enhanced Schema Documentation

The backend provides comprehensive API documentation with:

- **Detailed endpoint descriptions**
- **Field-level documentation with examples**
- **Request/response examples**
- **Error handling documentation**
- **Processing time estimates**

### Key Endpoints

#### System Endpoints
- `GET /` - Basic API information
- `GET /health` - System health check

#### Paper Management
- `POST /api/upload` - Upload PDF papers
- `GET /api/papers` - List uploaded papers
- `DELETE /api/papers/{docname}` - Delete papers
- `POST /api/load-papers` - Bulk load papers

#### Question Answering
- `POST /api/query` - Main query endpoint

### Response Models

All endpoints use properly documented Pydantic models with:
- Field descriptions and examples
- Validation constraints
- Type safety
- Comprehensive error handling

## Configuration

### Environment Variables

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional (for public search)
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_key
CROSSREF_API_KEY=your_crossref_key
```

### LiteLLM Configuration

The system supports multiple LLM configurations:

```python
# OpenRouter with GLM-4.5-Air (default)
settings = get_settings()

# OpenRouter with Google Gemma
settings = get_settings(use_gemma=True)

# Local Ollama (embeddings only)
settings = get_settings(use_ollama=True)
```

### Model Options

- **Default**: `openrouter/z-ai/glm-4.5-air:free`
- **Alternative**: `openrouter/google/gemma-3n-e2b-it:free`
- **Embeddings**: `ollama/nomic-embed-text:latest`

## Testing

### Backend Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src/paperqa

# Run specific test file
pytest tests/test_paperqa.py
```

### Frontend Testing

```bash
cd frontend
npm test
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Test query with public search
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is PaperQA?", "source": "public"}'
```

## Deployment

### Production Setup

1. **Environment configuration**
   ```bash
   # Set production environment variables
   export OPENROUTER_API_KEY=your_production_key
   export ENVIRONMENT=production
   ```

2. **Build frontend**
   ```bash
   cd frontend
   npm run build
   ```

3. **Start production server**
   ```bash
   # Use production WSGI server
   uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

```dockerfile
# Example Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### Common Issues

1. **OpenRouter API Key Issues**
   ```bash
   # Check environment variable
   echo $OPENROUTER_API_KEY
   
   # Verify key format
   # Should start with: sk-or-v1-
   ```

2. **Ollama Connection Issues**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Start Ollama if needed
   ollama serve
   ```

3. **Rate Limit Issues**
   ```bash
   # OpenRouter free tier has rate limits
   # Wait between requests or upgrade to paid tier
   ```

4. **Port Conflicts**
   ```bash
   # Check port usage
   lsof -i :3000
   lsof -i :8000
   ```

### Debug Tools

- **Health Check**: `curl http://localhost:8000/health`
- **API Documentation**: http://localhost:8000/docs
- **Backend Logs**: Monitor console output for detailed logs
- **Frontend DevTools**: Browser developer tools for frontend debugging

### Performance Optimization

- **Document Processing**: Optimize chunking and indexing
- **Caching**: Implement proper caching strategies
- **Rate Limiting**: Handle API rate limits gracefully
- **Memory Management**: Monitor memory usage for large document collections

## Contributing Guidelines

### Code Style

- **Python**: Follow PEP 8 guidelines
- **TypeScript**: Use strict TypeScript configuration
- **React**: Follow React best practices
- **Documentation**: Maintain comprehensive docstrings

### Development Process

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**
   - Follow coding standards
   - Add tests for new features
   - Update documentation

3. **Test changes**
   ```bash
   # Backend tests
   pytest
   
   # Frontend tests
   cd frontend && npm test
   ```

4. **Submit pull request**
   - Clear description of changes
   - Include tests
   - Update documentation

### Documentation Standards

- **API Documentation**: Use Pydantic Field descriptions
- **Code Comments**: Clear, concise comments
- **README Updates**: Keep main documentation current
- **Architecture Documentation**: Maintain system design docs

### Testing Requirements

- **Unit Tests**: For all new functionality
- **Integration Tests**: For API endpoints
- **Frontend Tests**: For React components
- **End-to-End Tests**: For critical user flows

---

For more detailed information, see:
- [BACKEND_SCHEMA.md](BACKEND_SCHEMA.md) - API documentation
- [Architecture.md](Architecture.md) - System architecture
- [configs.md](configs.md) - Configuration options 