# Paper-QA UI

A modern Gradio web interface for [Paper-QA](https://github.com/Future-House/paper-qa), enabling high-accuracy Retrieval Augmented Generation (RAG) on scientific documents with citations.

## 🚀 Features

- **📚 Document Upload**: Upload PDF papers and automatically index them
- **❓ Question Interface**: Ask questions about uploaded documents
- **📝 Answer Display**: Get formatted answers with proper citations
- **📚 Evidence Sources**: See which parts of documents were used
- **⚙️ Configuration**: Choose between different model configurations
- **🔄 Real-time Status**: Live updates during processing
- **🧹 Clear Functionality**: Reset and start fresh

## 🎯 Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed and running
- Optional: OpenRouter API key for cloud LLMs

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd paper-qa-ui
   make setup
   ```

2. **Configure environment** (optional):
   ```bash
   # Edit .env file to add your OpenRouter API key
   cp env.template .env
   # Edit .env and add: OPENROUTER_API_KEY=your_key_here
   ```

3. **Start the UI**:
   ```bash
   make ui
   ```

4. **Access the interface**:
   - Open your browser to: http://localhost:7860
   - Upload PDF documents
   - Ask questions about the documents

## 🛠️ Usage

### Web Interface

1. **Upload Documents**: Use the file upload to add PDF papers
2. **Process Documents**: Click "Process Documents" to index them
3. **Ask Questions**: Enter questions about the uploaded papers
4. **View Results**: See answers, sources, and processing information

### Configuration Options

The UI supports multiple configurations:

- **`optimized_ollama`** (Default): Local Ollama with performance tuning
- **`openrouter_ollama`**: OpenRouter LLM + Ollama embeddings
- **`ollama`**: Pure local Ollama setup
- **`clinical_trials`**: Includes clinical trials search capability

### CLI Usage

For command-line usage:

```bash
# Test CLI functionality
make test-cli

# Run CLI example
make cli-example

# Direct CLI usage
python scripts/paper_qa_cli.py "What is this paper about?"
```

## 🧪 Testing

Run comprehensive tests:

```bash
# Test UI functionality
make test-ui-functionality

# Test file upload
make test-file-upload

# Test complete workflow
make test-complete-workflow

# Test CLI
make test-cli
```

## 📁 Project Structure

```
paper-qa-ui/
├── src/
│   ├── paperqa2_ui.py      # Main Gradio UI application
│   ├── config_manager.py   # Configuration management
│   └── __init__.py
├── configs/                 # Configuration files
│   ├── optimized_ollama.json
│   ├── openrouter_ollama.json
│   ├── ollama.json
│   └── clinical_trials.json
├── scripts/                # Utility scripts
│   ├── run_gradio_ui.py
│   ├── paper_qa_cli.py
│   └── test_*.py
├── papers/                 # Uploaded documents
├── indexes/                # Paper-QA indexes
└── Makefile               # Build and management commands
```

## ⚙️ Configuration

### Optimized Ollama Configuration

The default configuration (`optimized_ollama`) is tuned for performance:

- **LLM**: `ollama/llama3.2`
- **Embedding**: `ollama/nomic-embed-text`
- **Evidence K**: 20
- **Max Sources**: 7
- **Concurrent Requests**: 1
- **Temperature**: 0.2

### Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key (optional)

## 🔧 Development

### Setup Development Environment

```bash
make setup
```

### Run Tests

```bash
make test-ui-functionality
make test-file-upload
make test-complete-workflow
```

### Clean Up

```bash
make clean-data      # Clean session data
make clean-all-data  # Clean all data including papers
make kill-server     # Kill hanging server processes
```

## 🐛 Troubleshooting

### Common Issues

1. **Port 7860 in use**:
   ```bash
   make kill-server
   make ui
   ```

2. **Ollama not running**:
   ```bash
   ollama serve
   ```

3. **Missing models**:
   ```bash
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

4. **File upload errors**: The UI now properly handles Gradio file objects and duplicate files.

### Logs

Check the terminal output for detailed logs. The UI provides real-time status updates during processing.

## 📊 Performance

The optimized configuration provides:
- **Fast indexing**: Efficient document processing
- **Accurate retrieval**: 20 evidence sources with relevance scoring
- **Local processing**: No external API calls required (with Ollama)
- **Real-time feedback**: Live status updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test-ui-functionality`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Paper-QA](https://github.com/Future-House/paper-qa) - The core RAG engine
- [Ollama](https://ollama.com/) - Local LLM runner
- [Gradio](https://gradio.app/) - Web interface framework
- [LiteLLM](https://github.com/BerriAI/litellm) - LLM abstraction layer