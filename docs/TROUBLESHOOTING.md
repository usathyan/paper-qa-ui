# Troubleshooting Guide

This guide addresses common issues when using Paper-QA, especially with local LLMs (Ollama).

## 🤖 Local LLM Issues

### JSON Parsing Errors

**Problem**: `TypeError("GenerateAnswer.gen_answer() got an unexpected keyword argument 'question'")`

**Cause**: Local LLMs often fail to generate proper JSON output or follow the correct schema.

**Solution**: 
1. Set `"use_json": false` in your prompts configuration
2. Update your config file:

```json
{
  "prompts": {
    "use_json": false,
    // ... other prompt settings
  }
}
```

### Timeout Errors

**Problem**: Requests timeout or hang indefinitely

**Cause**: Local models are slower than cloud APIs, especially with large context windows.

**Solutions**:
1. Reduce `max_concurrent_requests` to 1
2. Lower `search_count` in agent settings
3. Reduce `answer_max_sources` to 5-7
4. Increase timeout values

```json
{
  "answer": {
    "max_concurrent_requests": 1,
    "answer_max_sources": 7
  },
  "agent": {
    "search_count": 10,
    "timeout": 900.0
  }
}
```

### Model Not Found

**Problem**: `Could not find cost for model ollama/llama3.2`

**Cause**: Model not downloaded or Ollama not running

**Solutions**:
1. Ensure Ollama is running: `ollama serve`
2. Download the model: `ollama pull llama3.2`
3. Check available models: `ollama list`

### Poor Answer Quality

**Problem**: Answers are inconsistent or irrelevant

**Solutions**:
1. Adjust temperature to 0.2 for consistency
2. Increase context window (`num_ctx: 32768`)
3. Use better models (Llama 3.1 70B > Llama 3.2 > Mixtral)
4. Adjust repetition penalty (`repeat_penalty: 1.1`)

## ⚙️ Configuration Issues

### Settings Not Applied

**Problem**: Changes to configuration files don't take effect

**Solutions**:
1. Restart the application after config changes
2. Check JSON syntax in config files
3. Ensure config file path is correct
4. Clear any cached settings

### Paper Directory Issues

**Problem**: Papers not found or indexed

**Solutions**:
1. Check `paper_directory` path in config
2. Ensure papers are in PDF format
3. Set `recurse_subdirectories: true` to include subfolders
4. Rebuild index if needed

## 🔧 Performance Optimization

### Slow Response Times

**Optimizations**:
1. Use smaller models for faster responses
2. Reduce `evidence_k` to 10-15
3. Set `max_concurrent_requests: 1`
4. Use SSD storage for indexes
5. Increase system RAM if possible

### Memory Issues

**Solutions**:
1. Reduce `chunk_size` in parsing settings
2. Lower `num_ctx` for models with limited VRAM
3. Use models that fit in your GPU memory
4. Close other applications to free memory

## 🧪 Testing Your Setup

### Run Configuration Test

Use the built-in status check:

```bash
make status
make check-env
```

This will test:
- Ollama connection
- Model availability
- Configuration validation
- Paper-QA integration
- Data directory status

### Clean Data Issues

If you're experiencing corrupted indexes or session problems:

```bash
make clean-data      # Clean session data (preserves papers/)
make clean-all-data  # Complete reset (removes papers/)
```

### Manual Testing

1. **Test Ollama Connection**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Test Model Response**:
   ```bash
   curl -X POST http://localhost:11434/api/generate \
     -H "Content-Type: application/json" \
     -d '{"model": "llama3.2", "prompt": "Hello", "stream": false}'
   ```

3. **Test Paper-QA Integration**:
   ```python
   from src.paper_qa_core import PaperQACore
   
   core = PaperQACore("your_config")
   result = await core.query_local_papers("What is machine learning?")
   print(result["success"])
   ```

## 📊 Recommended Configurations

### High-Performance Setup (24GB+ VRAM)
```json
{
  "llm": "ollama/llama3.1:70b",
  "temperature": 0.2,
  "answer": {
    "evidence_k": 20,
    "answer_max_sources": 7,
    "max_concurrent_requests": 1
  },
  "prompts": {
    "use_json": false
  }
}
```

### Balanced Setup (8-16GB VRAM)
```json
{
  "llm": "ollama/llama3.2",
  "temperature": 0.2,
  "answer": {
    "evidence_k": 15,
    "answer_max_sources": 5,
    "max_concurrent_requests": 1
  },
  "prompts": {
    "use_json": false
  }
}
```

### Lightweight Setup (4-8GB VRAM)
```json
{
  "llm": "ollama/phi3",
  "temperature": 0.1,
  "answer": {
    "evidence_k": 10,
    "answer_max_sources": 3,
    "max_concurrent_requests": 1
  },
  "prompts": {
    "use_json": false
  }
}
```

## 🆘 Getting Help

### Debug Information

When reporting issues, include:
1. Configuration file contents
2. Error messages and stack traces
3. System specifications (RAM, GPU, OS)
4. Ollama version and model names
5. Test results from `make status` and `make check-env`

### Common Error Messages

| Error | Likely Cause | Solution |
|-------|-------------|----------|
| `TypeError: unexpected keyword argument` | JSON parsing issue | Set `"use_json": false` |
| `Could not find cost for model` | Model not available | Download model with `ollama pull` |
| `Timeout` | Model too slow | Reduce concurrent requests |
| `Connection refused` | Ollama not running | Start with `ollama serve` |

### Resources

- [Paper-QA GitHub Discussions](https://github.com/Future-House/paper-qa/discussions)
- [Ollama Documentation](https://ollama.ai/docs)
- [Local LLM Performance Guide](https://github.com/Future-House/paper-qa/discussions/753) 