# Paper-QA Project Restart Plan

## Project Overview
This project aims to create a clean, focused implementation of Paper-QA using OpenRouter.ai with Google Gemini 2.5 Flash Lite model and Ollama's nomad-embed-text for embeddings. The project will focus on three main scenarios: local paper research, public source research, and combined research, specifically targeting PICALM and Alzheimer's Disease research questions.

## Phase 1: Basic Paper-QA Setup with CLI

### 1.1 Environment Setup
- [ ] Create new virtual environment using `uv venv --python 3.11`
- [ ] Install paper-qa with required dependencies
- [ ] Configure OpenRouter.ai API key for Google Gemini 2.5 Flash Lite
- [ ] Setup Ollama with nomad-embed-text model
- [ ] Configure Semantic Scholar and Crossref (no API keys required)
- [ ] Create `.env` file with necessary configurations
- [ ] Test basic CLI functionality

### 1.2 Configuration Files
- [ ] Create `configs/` directory with JSON configuration files
- [ ] Setup configuration for OpenRouter.ai integration
- [ ] Configure embedding model settings for Ollama
- [ ] Setup retry mechanisms with tenacity for API rate limits
- [ ] Create development and production configurations

### 1.3 Basic CLI Testing
- [ ] Test paper loading from local directory
- [ ] Test basic query functionality
- [ ] Verify streaming responses work
- [ ] Test agentic capabilities
- [ ] Validate citation generation

## Phase 2: Programmatic Interface Development

### 2.1 Core Functions
- [ ] Create `paper_qa_core.py` with main functions:
  - `query_local_papers(question, paper_dir)`
  - `query_public_sources(question)`
  - `query_combined(question, paper_dir)`
- [ ] Implement streaming response handlers
- [ ] Add error handling and retry logic
- [ ] Create result formatting utilities

### 2.2 Configuration Management
- [ ] Create `config_manager.py` for dynamic configuration
- [ ] Implement settings validation
- [ ] Add configuration presets for different scenarios
- [ ] Create environment variable management

### 2.3 Testing Framework
- [ ] Create comprehensive test suite
- [ ] Test all three scenarios (local, public, combined)
- [ ] Validate streaming functionality
- [ ] Test error handling and retry mechanisms

## Phase 3: PICALM and Alzheimer's Disease Research Scenarios

### 3.1 Sample Questions Development
Create three variants of PICALM/Alzheimer's questions:

1. **Basic Research Question**: "What is the role of PICALM in Alzheimer's disease pathogenesis?"
2. **Mechanistic Question**: "How does PICALM interact with amyloid-beta and tau proteins in Alzheimer's disease?"
3. **Therapeutic Question**: "What are the potential therapeutic targets related to PICALM in Alzheimer's disease treatment?"

### 3.2 Paper Collection
- [ ] Download relevant PICALM/Alzheimer's research papers
- [ ] Organize papers in `papers/picalm_alzheimer/` directory
- [ ] Create paper metadata manifest
- [ ] Validate paper quality and relevance

### 3.3 Scenario Testing
- [ ] **Local Papers Only**: Test with downloaded papers
- [ ] **Public Sources Only**: Test with Semantic Scholar/Crossref
- [ ] **Combined Approach**: Test with both local and public sources
- [ ] Compare response quality and citation accuracy

## Phase 4: Advanced Features

### 4.1 Streaming Implementation
- [ ] Implement real-time response streaming
- [ ] Add progress indicators for long queries
- [ ] Create callback system for streaming events
- [ ] Add response chunking and formatting

### 4.2 Agentic Capabilities
- [ ] Configure advanced agent settings
- [ ] Implement multi-step reasoning
- [ ] Add evidence gathering tools
- [ ] Create citation verification system

### 4.3 Performance Optimization
- [ ] Implement caching for embeddings
- [ ] Add concurrent processing for multiple queries
- [ ] Optimize memory usage for large paper collections
- [ ] Add performance monitoring

## Technical Specifications

### Dependencies
```toml
[project]
dependencies = [
    "paper-qa[dev]",
    "python-dotenv>=1.1.1",
    "tenacity>=8.0.0",
    "rich>=13.0.0",
    "httpx>=0.24.0",
    "pydantic>=2.10.1",
    "pydantic-settings>=2.0.0"
]
```

### Environment Variables
```bash
# .env file
OPENROUTER_API_KEY=your_openrouter_api_key
PQA_HOME=/path/to/paper-qa/data
PAPER_DIRECTORY=/path/to/papers
INDEX_DIRECTORY=/path/to/indexes
```

### Configuration Structure
```
configs/
├── default.json          # Default settings
├── openrouter.json       # OpenRouter.ai specific settings
├── ollama.json          # Ollama embedding settings
├── local_only.json      # Local papers only
├── public_only.json     # Public sources only
└── combined.json        # Combined approach
```

## File Structure
```
paper-qa-ui/
├── configs/              # Configuration files
├── papers/              # Local paper collection
│   └── picalm_alzheimer/
├── src/                 # Source code
│   ├── paper_qa_core.py
│   ├── config_manager.py
│   ├── streaming.py
│   └── utils.py
├── tests/               # Test files
├── scripts/             # Utility scripts
├── .env                 # Environment variables
├── pyproject.toml       # Project configuration
├── README.md           # Project documentation
├── Architecture.md     # Technical architecture
└── plan.md             # This file
```

## Success Criteria

### Phase 1 Success
- [ ] CLI works with OpenRouter.ai and Ollama
- [ ] Basic paper loading and querying functional
- [ ] Streaming responses working
- [ ] Citations generated correctly

### Phase 2 Success
- [ ] All three query functions working
- [ ] Configuration management functional
- [ ] Error handling robust
- [ ] Tests passing

### Phase 3 Success
- [ ] PICALM questions answered accurately
- [ ] Local vs public vs combined comparisons complete
- [ ] Response quality validated
- [ ] Citations verified

### Phase 4 Success
- [ ] Real-time streaming working
- [ ] Agentic capabilities enhanced
- [ ] Performance optimized
- [ ] Production ready

## Risk Mitigation

### Technical Risks
- **API Rate Limits**: Implement tenacity retry logic
- **Model Availability**: Have fallback models configured
- **Memory Issues**: Implement chunking and caching
- **Network Issues**: Add offline mode for local papers

### Quality Risks
- **Response Accuracy**: Implement citation verification
- **Streaming Reliability**: Add error recovery mechanisms
- **Configuration Complexity**: Create preset configurations

## Timeline
- **Week 1**: Phase 1 - Basic setup and CLI
- **Week 2**: Phase 2 - Programmatic interface
- **Week 3**: Phase 3 - PICALM scenarios
- **Week 4**: Phase 4 - Advanced features and optimization

## Next Steps
1. Review and approve this plan
2. Begin Phase 1 implementation
3. Set up development environment
4. Create initial configuration files
5. Test basic functionality 