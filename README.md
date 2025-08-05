# Paper-QA UI

Upload PDF documents and ask questions to get answers with citations from your documents.

## Setup

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.com/) installed and running

### Installation
```bash
git clone <repository-url>
cd paper-qa-ui
make setup
```

### Environment Configuration

Copy the template and configure your API keys:
```bash
cp env.template .env
# Edit .env with your API keys
```

## Usage

### Start the UI
```bash
make ui
```
Open http://localhost:7860

### Document Processing Workflow

1. **Upload Documents**: Upload PDF files using the file upload
2. **Automatic Processing**: Documents are automatically copied to the papers directory
3. **Ask Questions**: Use the question interface to query your documents

### User Flow

```
📁 Upload PDF documents
    ↓ (automatic processing)
✅ Documents copied to papers directory
    ↓
❓ Ask questions (immediately available)
```

### Example Questions
- "What is the main finding of this research?"
- "What methodology was used?"
- "What are the limitations mentioned?"
- "What conclusions were drawn?"

## Configurations

### Local Processing (Default)
- **Config**: `optimized_ollama`
- **LLM**: Ollama llama3.2
- **Embedding**: Ollama nomic-embed-text
- **Setup**: No API keys required

### Azure OpenAI
- **Config**: `azure_openai`
- **LLM**: Azure GPT-4
- **Embedding**: Ollama nomic-embed-text
- **Setup**: Add to `.env`:
  ```
  AZURE_OPENAI_API_KEY=your_key
  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
  ```

### Amazon Bedrock
- **Config**: `amazon_bedrock`
- **LLM**: Claude 3 Sonnet
- **Embedding**: Ollama nomic-embed-text
- **Setup**: Add to `.env`:
  ```
  AWS_ACCESS_KEY_ID=your_key
  AWS_SECRET_ACCESS_KEY=your_secret
  AWS_REGION=us-east-1
  ```

### OpenRouter
- **Config**: `openrouter_ollama`
- **LLM**: Various models via OpenRouter
- **Embedding**: Ollama nomic-embed-text
- **Setup**: Add to `.env`:
  ```
  OPENROUTER_API_KEY=your_key
  ```

## CLI Usage

```bash
# Test CLI
make test-cli

# Run example
make cli-example

# Direct usage
python scripts/paper_qa_cli.py "What is this paper about?"
```

## Troubleshooting

### Port Issues
```bash
make kill-server
make ui
```

### Ollama Issues
```bash
ollama serve
ollama pull llama3.2
ollama pull nomic-embed-text
```

### Missing Models
```bash
ollama list  # Check available models
ollama pull <model_name>  # Download missing models
```

### Document Processing Issues
- **Documents not processing**: Check if Ollama is running
- **Processing stuck**: Try refreshing the page and re-uploading
- **Connection errors**: Restart Ollama with `ollama serve`