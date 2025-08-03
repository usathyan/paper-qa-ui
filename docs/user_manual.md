# Paper-QA Enhanced Interface - User Manual

## 🎯 Overview

The Paper-QA Enhanced Interface is a powerful tool for querying scientific papers and clinical trials using advanced AI capabilities. It provides multiple search methods, detailed agent insights, and comprehensive configuration options.

## 🚀 Quick Start

### 1. Installation & Setup

```bash
# Clone the repository
git clone <repository-url>
cd paper-qa-ui

# Install dependencies
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Launch the Interface

```bash
# Start the web interface
make ui

# Or use the CLI
python scripts/paper_qa_cli.py "Your question here" --method public
```

## 🔍 Search Methods

### 1. **Public Sources** (Recommended)
- Searches public scientific databases
- Best for general research questions
- No local files required

### 2. **Local Papers**
- Searches your local PDF files
- Requires paper directory setup
- Good for proprietary or offline documents

### 3. **Combined**
- Searches both public sources and local papers
- Most comprehensive results
- Requires paper directory

### 4. **Semantic Scholar API**
- Direct API queries to Semantic Scholar
- Fast results for specific papers
- Rate-limited but reliable

### 5. **Clinical Trials** ⭐ NEW
- Searches clinicaltrials.gov database
- Combines with local papers if available
- Perfect for medical research questions

### 6. **Clinical Trials Only** ⭐ NEW
- Searches only clinicaltrials.gov
- No local papers or public sources
- Focused medical research results

## 🎛️ Configuration Options

### Available Configurations

1. **default** - Balanced performance and accuracy
2. **agent_optimized** - Enhanced agent tool-calling
3. **comprehensive** - Maximum information retrieval
4. **clinical_trials** - Optimized for medical research
5. **clinical_trials_only** - Clinical trials only

### Configuration Features

- **LLM Models**: Choose from various AI models
- **Search Parameters**: Adjust search depth and breadth
- **Agent Behavior**: Customize tool usage and reasoning
- **Output Format**: Control answer length and detail level

## 💻 CLI Usage

### Basic Commands

```bash
# Query public sources
python scripts/paper_qa_cli.py "What causes Alzheimer's disease?" --method public

# Query clinical trials
python scripts/paper_qa_cli.py "What treatments exist for ulcerative colitis?" --method clinical_trials

# Query local papers
python scripts/paper_qa_cli.py "What does this paper say about PICALM?" --method local --paper-dir ./papers

# Save results to file
python scripts/paper_qa_cli.py "Your question" --method public --output results.json
```

### Advanced Options

```bash
# Use specific configuration
python scripts/paper_qa_cli.py "Question" --method clinical_trials --config clinical_trials_only

# Combine multiple sources
python scripts/paper_qa_cli.py "Question" --method combined --paper-dir ./papers --config comprehensive
```

## 🌐 Web Interface

### Main Features

1. **Question Input**: Enter your research question
2. **Method Selection**: Choose search method
3. **Configuration**: Select AI configuration
4. **Real-time Results**: See answers and sources
5. **Status Monitoring**: Track agent progress

### Quick Examples

The interface includes pre-built examples:
- Alzheimer's disease treatments
- PICALM and amyloid beta clearance
- Clinical trials for ulcerative colitis
- Genetic risk factors for Parkinson's

### Configuration Tab

- **Load Configurations**: Switch between preset configurations
- **Custom Settings**: Modify individual parameters
- **Save Changes**: Store custom configurations
- **Restart Required**: Apply changes with server restart

## 📊 Understanding Results

### Answer Section
- **Formatted Response**: Clean, readable answers
- **Citations**: In-line references to sources
- **Evidence**: Supporting information from papers

### Sources Section
- **Papers Searched**: Number of documents processed
- **Evidence Retrieved**: Relevant text passages found
- **Agent Performance**: Tool usage and processing steps
- **Search Method**: Which approach was used

### Status Section
- **Processing Status**: Real-time updates
- **Error Messages**: Clear error reporting
- **Completion Time**: Performance metrics

## 🔧 Advanced Features

### Clinical Trials Integration ⭐ NEW

The system now supports querying clinical trials from clinicaltrials.gov:

```python
# Using the API
from src.paper_qa_core import PaperQACore

core = PaperQACore('clinical_trials')
result = await core.query_clinical_trials("What drugs treat ulcerative colitis?")
```

**Benefits:**
- Access to 400,000+ clinical trials
- Real-time trial data
- Medical-grade information
- FDA-approved treatments

### Agent Insights

Monitor the AI agent's thinking process:
- **Tool Calls**: See which tools are used
- **Search Steps**: Track paper discovery
- **Evidence Gathering**: Monitor information retrieval
- **Answer Generation**: Understand reasoning

### Configuration Management

- **Preset Configurations**: Optimized for different use cases
- **Custom Settings**: Fine-tune every parameter
- **Environment Variables**: Secure API key management
- **Configuration Validation**: Automatic error checking

## 🚨 Troubleshooting

### Common Issues

1. **Rate Limiting**
   - Use rate-limited configurations
   - Implement delays between queries
   - Monitor API usage

2. **Configuration Errors**
   - Check environment variables
   - Validate configuration files
   - Restart server after changes

3. **Paper Loading Issues**
   - Verify file paths
   - Check PDF format compatibility
   - Ensure sufficient disk space

### Error Messages

- **"object.__init__() takes exactly one argument"**: Known paper-qa library issue, doesn't affect functionality
- **"429 Too Many Requests"**: Rate limiting, wait and retry
- **"Module not found"**: Check virtual environment activation

## 📈 Performance Tips

### Optimization Strategies

1. **Choose Right Method**
   - Use "public" for general questions
   - Use "clinical_trials" for medical research
   - Use "local" for specific documents

2. **Configuration Selection**
   - "default" for balanced performance
   - "comprehensive" for maximum detail
   - "agent_optimized" for complex reasoning

3. **Query Formulation**
   - Be specific and clear
   - Include key terms
   - Use medical terminology for clinical queries

## 🔒 Security & Privacy

### Data Handling
- **Local Processing**: Papers processed locally
- **API Security**: Secure API key management
- **No Data Storage**: Queries not permanently stored
- **Privacy Compliance**: HIPAA-compliant for medical data

### Best Practices
- Keep API keys secure
- Use environment variables
- Monitor usage limits
- Regular security updates

## 📚 Additional Resources

### Documentation
- [Developer Guide](DEVELOPER.md) - Technical implementation details
- [Architecture](Architecture.md) - System design and components
- [API Reference](API.md) - Programmatic interface

### Examples
- [PICALM Research](examples/picalm_research.md) - Alzheimer's disease research
- [Clinical Trials](examples/clinical_trials.md) - Medical research examples
- [Configuration Examples](examples/configurations.md) - Setup examples

### Support
- [GitHub Issues](https://github.com/usathyan/paper-qa-ui/issues) - Bug reports and feature requests
- [Discussions](https://github.com/usathyan/paper-qa-ui/discussions) - Community support
- [Wiki](https://github.com/usathyan/paper-qa-ui/wiki) - Additional documentation

---

**Last Updated**: January 2025  
**Version**: 2.0.0  
**Paper-QA Version**: 5.27.0 