# PaperQA Discovery

A web-based interface for [PaperQA2](https://github.com/Future-House/paper-qa), a high-accuracy retrieval augmented generation (RAG) system for scientific papers.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 16+
- [Ollama](https://ollama.ai/) installed and running
- [UV](https://docs.astral.sh/uv/) package manager

### Installation

1. **Clone and setup environment:**
```bash
git clone <repository-url>
cd paper-qa-ui
uv venv --python 3.11
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
```

2. **Install Ollama models:**
```bash
ollama pull gemma3:latest
ollama pull nomic-embed-text:latest
```

3. **Configure environment:**
```bash
# Create .env file with your API keys (optional for public search)
echo 'OPENROUTER_API_KEY="your_key_here"' > .env
```

4. **Start the system:**
```bash
make run
```

The system will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🏗️ Architecture

### Current Configuration
- **LLM**: Ollama with Gemma3 (local, no rate limits)
- **Embeddings**: Ollama with Nomic Embed Text
- **Public Search**: OpenRouter.ai (optional, requires API key)
- **Frontend**: React with TypeScript
- **Backend**: FastAPI with PaperQA2 integration

### System Components
- **Document Management**: Upload, list, and delete PDF papers
- **Query Processing**: Advanced agentic PaperQA queries with tool selection
- **Source Selection**: Local papers, public domain, or both
- **Real-time Feedback**: Enhanced thinking details and reasoning transparency

## 📚 Usage

### Adding Papers
1. Upload PDF files through the web interface
2. Papers are automatically processed and indexed
3. Use "Local Papers Only" for queries about your documents

### Querying
1. **Local Papers**: Questions about uploaded documents
2. **Public Domain**: Questions requiring external research (needs API keys)
3. **All Sources**: Combines local and public sources

### Example Queries
- "What is machine learning?" (works with local papers)
- "What is the primary biological function of the FOXA1 gene?" (requires public search)

## 🔧 Configuration

### LLM Providers
The system supports multiple LLM configurations:

```python
# Default: Ollama (local, no rate limits)
settings = get_settings()  # Uses Ollama

# OpenRouter.ai (cloud, requires API key)
settings = get_settings(use_gemma=False, use_ollama=False)

# Google Gemma via OpenRouter
settings = get_settings(use_gemma=True, use_ollama=False)
```

### Environment Variables
```bash
# Required for OpenRouter.ai
OPENROUTER_API_KEY=your_key_here

# Optional for public search
SEMANTIC_SCHOLAR_API_KEY=your_key_here
CROSSREF_API_KEY=your_key_here
```

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check if PaperQA is installed
uv pip install paper-qa

# Verify virtual environment
source .venv/bin/activate
python -c "import paperqa; print('OK')"
```

**Rate limiting errors:**
- Switch to Ollama: `settings = get_settings(use_ollama=True)`
- Or get API keys for OpenRouter.ai

**Papers not loading:**
- Check file format (PDF only)
- Verify Ollama server is running: `curl http://localhost:11434/api/tags`

**Frontend build errors:**
```bash
cd frontend
npm install
npm start
```

### Health Check
Visit http://localhost:8000/health to check system status.

## 📖 API Documentation

Comprehensive API documentation is available at http://localhost:8000/docs when the backend is running.

### Key Endpoints
- `POST /api/query` - Submit questions
- `POST /api/upload` - Upload PDF papers
- `GET /api/papers` - List loaded papers
- `DELETE /api/papers/{name}` - Delete a paper
- `GET /health` - System health check

## 🔄 Development

### Project Structure
```
paper-qa-ui/
├── api/                 # FastAPI backend
│   ├── main.py         # Main application
│   └── config.py       # LLM configurations
├── frontend/           # React frontend
│   └── src/
│       └── components/
│           └── Query.tsx
├── uploaded_papers/    # User uploaded documents
└── docs/              # Documentation
```

### Development Commands
```bash
# Start backend only
make backend

# Start frontend only
make frontend

# Start both
make run

# Stop all services
make stop

# Clean and restart
make clean && make run
```

## 🚧 Current Limitations

1. **Public Search**: Requires external API keys for full functionality
2. **Streaming**: Thinking details are captured but not streamed in real-time
3. **Rate Limits**: OpenRouter.ai free tier has strict limits
4. **Processing Time**: Agentic queries take longer but provide better reasoning

## 🔮 Future Enhancements

- [x] ✅ Implement agentic query mode for better reasoning
- [ ] Real-time streaming of thinking process
- [ ] Enhanced public search with better API integration
- [ ] Document preprocessing and metadata extraction
- [ ] Multi-language support

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📚 References

- [PaperQA2 GitHub Repository](https://github.com/Future-House/paper-qa)
- [PaperQA2 Documentation](https://futurehouse.gitbook.io/futurehouse-cookbook)
- [Ollama Documentation](https://ollama.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
