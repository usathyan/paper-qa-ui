# 📚 Paper-QA User Manual

Welcome to Paper-QA! This comprehensive guide will help you understand and use all the features of our enhanced research paper question-answering system.

## 🚀 Quick Start

### 1. Starting the Application
```bash
# Start the web interface
make ui

# Or run directly
python3 scripts/run_gradio_ui.py
```

### 2. Accessing the Interface
- Open your browser to: `http://localhost:7860`
- You'll see a tabbed interface with two main sections:
  - **🔍 Query Papers** - Ask questions about research papers
  - **⚙️ Configure** - Customize system settings

## 🔍 Query Papers Tab

### Overview
The Query Papers tab is your main interface for asking questions about research papers. It provides multiple search methods and detailed insights into how the AI processes your questions.

### Input Section

#### **Question Field**
- **Purpose**: Enter your research question
- **Tips**: 
  - Be specific and use scientific terminology
  - Include key concepts and terms
  - For complex questions, break them into parts

#### **Search Method Selection**
Choose from four different search approaches:

| Method | Description | Best For |
|--------|-------------|----------|
| **Public** | Searches online sources (Semantic Scholar, Crossref) | General research questions, finding recent papers |
| **Local** | Searches only your uploaded PDF papers | Questions about specific papers you have |
| **Combined** | Searches both local and public sources | Comprehensive research, when you want both perspectives |
| **Semantic Scholar** | Direct API search using optimized patterns | Specific topics like PICALM, endocytosis, Alzheimer's |

#### **Configuration Selection**
Choose from pre-configured settings:

| Configuration | Description | Use Case |
|---------------|-------------|----------|
| **Default** | Balanced settings for general use | Most questions, good starting point |
| **Local Only** | Optimized for local papers | When working with your own PDF collection |
| **Public Only** | Optimized for online sources | When searching for recent research |
| **Combined** | Optimized for mixed sources | When you want comprehensive coverage |

#### **Papers Directory (Optional)**
- **Purpose**: Specify path to your PDF papers
- **Default**: `./papers`
- **Usage**: Only needed for local or combined searches

#### **Max Sources**
- **Purpose**: Control how many sources to include in answers
- **Range**: 1-50
- **Default**: 10
- **Tip**: Higher values give more comprehensive answers but may be slower

### Output Section

#### **Answer Display**
- Shows the AI-generated answer to your question
- Includes citations and references
- Automatically truncated if too long (with option to see full text)

#### **Sources Information**
- Displays count of sources found
- Shows which search method was used

#### **Status Updates**
- Real-time feedback on query progress
- Error messages and success confirmations

### Enhanced Information Sections

#### **🤖 Agent Thinking Process**
This section shows you exactly how the AI processed your question:

**Agent Steps:**
- Step-by-step breakdown of what the AI did
- Timestamps for each action
- Tool usage and decision points

**Tool Calls:**
- Paper search operations
- Evidence gathering activities
- Answer generation processes

**Context Updates:**
- Real-time status updates
- Information about what was found

**Summary:**
- Total steps taken
- Number of tool calls made
- Overall processing efficiency

#### **📚 Detailed Context Information**
Shows the specific information the AI used to answer your question:

**For Each Context:**
- **Citation**: Source paper information
- **Score**: Relevance score (0-10)
- **Paper Details**: Title, authors, year, DOI
- **Text Excerpt**: The specific text used (truncated for display)

#### **⚙️ Agent Metadata**
Technical details about the AI's configuration and session:

**Configuration:**
- Agent type used
- Search parameters
- Evidence settings
- Timeout values

**Session Information:**
- Session ID and status
- Cost tracking (if applicable)
- Tools used during processing
- Number of papers searched

## ⚙️ Configure Tab

### Overview
The Configure tab gives you complete control over how Paper-QA works. You can customize every aspect of the system without editing configuration files manually.

### Configuration Management

#### **Loading Configurations**
1. **Select Configuration File**: Choose from available configs
2. **Click "📂 Load Configuration"**: Populates all fields with current settings
3. **Review Current Settings**: See what's currently configured

#### **Saving Changes**
1. **Modify Settings**: Adjust any parameters as needed
2. **Click "💾 Save Configuration"**: Saves changes with automatic backup
3. **Restart Required**: You'll be prompted to restart the server

### Configuration Sections

#### **🔧 General Settings**

**LLM Model**
- **Purpose**: Main AI model for answering questions
- **Options**: Various OpenRouter and Ollama models
- **Default**: `openrouter/google/gemini-2.5-flash-lite`

**Summary LLM Model**
- **Purpose**: AI model for creating summaries
- **Default**: Same as main LLM model

**Embedding Model**
- **Purpose**: Model for converting text to vectors for search
- **Default**: `ollama/nomic-embed-text`

**Temperature**
- **Purpose**: Controls randomness in AI responses
- **Range**: 0.0 (deterministic) to 2.0 (very random)
- **Default**: 0.0 (consistent answers)

**Verbosity Level**
- **Purpose**: Controls logging detail
- **Range**: 0 (silent) to 5 (very verbose)
- **Default**: 3

#### **🤖 Agent Settings**

**Agent LLM Model**
- **Purpose**: AI model for the agent that coordinates searches
- **Default**: Same as main LLM model

**Agent Type**
- **Options**: ToolSelector, Task
- **Default**: ToolSelector
- **Description**: How the agent organizes its work

**Search Count**
- **Purpose**: Number of papers to search for
- **Range**: 1-100
- **Default**: 20

**Timeout (seconds)**
- **Purpose**: Maximum time for agent to complete work
- **Range**: 30-3600 seconds
- **Default**: 600 (10 minutes)

**Pre-search**
- **Purpose**: Run search before invoking agent
- **Default**: True
- **Benefit**: Faster results for simple questions

**Wipe Context on Failure**
- **Purpose**: Clear context if answer generation fails
- **Default**: True
- **Benefit**: Prevents stuck states

**Agent Evidence Count**
- **Purpose**: Number of evidence pieces for agent
- **Range**: 1-50
- **Default**: 5

**Return Paper Metadata**
- **Purpose**: Include paper details in results
- **Default**: True
- **Benefit**: More detailed source information

#### **📁 Index Settings**

**Paper Directory**
- **Purpose**: Where your PDF papers are stored
- **Default**: `./papers`

**Index Directory**
- **Purpose**: Where search indexes are stored
- **Default**: `./indexes`

**Recurse Subdirectories**
- **Purpose**: Search subfolders for papers
- **Default**: True

**Concurrency**
- **Purpose**: Number of simultaneous file operations
- **Range**: 1-10
- **Default**: 3

**Sync with Paper Directory**
- **Purpose**: Keep index updated with paper changes
- **Default**: False
- **Benefit**: Automatic updates but slower performance

#### **📝 Answer Settings**

**Evidence K**
- **Purpose**: Number of evidence pieces to retrieve
- **Range**: 1-100
- **Default**: 20

**Detailed Citations**
- **Purpose**: Include full citation information
- **Default**: True

**Evidence Retrieval**
- **Purpose**: Enable evidence gathering
- **Default**: True

**Relevance Score Cutoff**
- **Purpose**: Minimum relevance for evidence
- **Range**: 0-10
- **Default**: 1

**Evidence Summary Length**
- **Purpose**: Length of evidence summaries
- **Default**: "about 150 words"

**Skip Evidence Summary**
- **Purpose**: Skip generating evidence summaries
- **Default**: False

**Max Sources**
- **Purpose**: Maximum sources in answer
- **Range**: 1-50
- **Default**: 15

**Max Answer Attempts**
- **Purpose**: Maximum attempts to generate answer
- **Range**: 1-10
- **Default**: 3

**Answer Length**
- **Purpose**: Target length for answers
- **Default**: "about 500 words"

**Max Concurrent Requests**
- **Purpose**: Maximum simultaneous API calls
- **Range**: 1-10
- **Default**: 3

**Filter Extra Background**
- **Purpose**: Remove irrelevant background information
- **Default**: False

**Get Evidence if No Contexts**
- **Purpose**: Retrieve evidence even without contexts
- **Default**: True

**Group Contexts by Question**
- **Purpose**: Organize contexts by question
- **Default**: False

#### **📄 Parsing Settings**

**Chunk Size**
- **Purpose**: Size of text chunks for processing
- **Range**: 1000-10000
- **Default**: 5000

**Page Size Limit**
- **Purpose**: Maximum page size for processing
- **Range**: 100000-5000000
- **Default**: 1280000

**PDF Block Parsing**
- **Purpose**: Use block parsing for PDFs
- **Default**: False

**Use Document Details**
- **Purpose**: Include document metadata
- **Default**: True

**Overlap**
- **Purpose**: Overlap between text chunks
- **Range**: 0-1000
- **Default**: 250

**Disable Document Validation**
- **Purpose**: Skip document validation
- **Default**: False

**Defer Embedding**
- **Purpose**: Delay embedding generation
- **Default**: False

**Chunking Algorithm**
- **Options**: simple_overlap, recursive_character, markdown
- **Default**: simple_overlap

#### **💬 Prompt Settings**

**Use JSON**
- **Purpose**: Use JSON format for prompts
- **Default**: True

**Summary Prompt**
- **Purpose**: Template for summarization
- **Default**: Standard summarization template

**QA Prompt**
- **Purpose**: Template for question answering
- **Default**: Standard QA template

**Select Prompt**
- **Purpose**: Template for paper selection
- **Default**: Standard selection template

**System Prompt**
- **Purpose**: System instructions for AI
- **Default**: Standard system instructions

## 🎯 Best Practices

### Asking Effective Questions

1. **Be Specific**: Instead of "Tell me about Alzheimer's", ask "What are the latest findings on PICALM's role in Alzheimer's disease endocytosis?"

2. **Use Scientific Terms**: Include relevant terminology like "clathrin-mediated endocytosis", "amyloid beta clearance"

3. **Specify Scope**: Mention if you want recent papers, specific mechanisms, or comprehensive reviews

4. **Break Complex Questions**: For multi-part questions, consider asking them separately

### Choosing the Right Method

- **Public**: For general research, recent findings, broad topics
- **Local**: When you have specific papers you want to analyze
- **Combined**: For comprehensive research requiring both perspectives
- **Semantic Scholar**: For specific topics with known successful search patterns

### Configuration Optimization

- **For Speed**: Reduce search count, increase concurrency, use pre-search
- **For Quality**: Increase evidence K, lower relevance cutoff, enable detailed citations
- **For Local Papers**: Use local_only configuration, enable sync with paper directory
- **For Online Research**: Use public_only configuration, increase max sources

## 🔧 Troubleshooting

### Common Issues

**"No relevant information found"**
- Try rephrasing your question
- Use "combined" method instead of "public"
- Add more specific terms
- Check if your papers directory is correct (for local searches)

**Slow Performance**
- Reduce search count
- Increase concurrency
- Use pre-search option
- Check your internet connection (for public searches)

**Configuration Not Working**
- Make sure to restart the server after saving changes
- Check that the configuration file exists
- Verify all required fields are filled

**Rate Limiting Errors**
- Wait a few minutes before trying again
- Consider getting an API key for higher limits
- Use local search methods if available

### Getting Help

1. **Check Status Messages**: The interface provides detailed status updates
2. **Review Agent Thinking**: See exactly what the AI is doing
3. **Examine Contexts**: Understand what information was found
4. **Check Configuration**: Ensure settings are appropriate for your use case

## 📊 Understanding Results

### Answer Quality Indicators

- **High Relevance Scores**: Contexts with scores >7 are very relevant
- **Multiple Sources**: More sources generally mean more comprehensive answers
- **Recent Papers**: Check publication dates for current information
- **Citation Quality**: Look for papers with high citation counts

### Interpreting Agent Thinking

- **More Steps**: Complex questions require more processing
- **Tool Calls**: Shows what search and retrieval operations were performed
- **Context Updates**: Real-time progress of information gathering
- **Session Metadata**: Performance and cost tracking information

## 🚀 Advanced Features

### Custom Configurations

Create custom configurations for specific use cases:

1. **Research Focus**: Optimize for specific research areas
2. **Performance Tuning**: Balance speed vs. quality
3. **Cost Optimization**: Minimize API usage
4. **Quality Focus**: Maximize answer quality and detail

### Prompt Customization

Modify prompts to:
- Change answer style (more technical, more accessible)
- Focus on specific aspects (methods, results, conclusions)
- Adjust citation format
- Customize summary length and style

### Batch Processing

For multiple questions:
1. Use consistent configuration
2. Keep track of which method works best
3. Consider using local search for related questions
4. Save successful configurations for reuse

## 📈 Performance Tips

### For Faster Results
- Use pre-search option
- Reduce search count for simple questions
- Increase concurrency for local searches
- Use appropriate configuration profiles

### For Better Quality
- Increase evidence K
- Lower relevance score cutoff
- Enable detailed citations
- Use combined method for comprehensive coverage

### For Cost Efficiency
- Use local searches when possible
- Optimize search count
- Use appropriate LLM models
- Monitor session costs in metadata

## 🔄 Workflow Examples

### Example 1: Literature Review
1. **Method**: Combined
2. **Configuration**: Default
3. **Question**: "What are the current theories on PICALM's role in Alzheimer's disease?"
4. **Follow-up**: Use local search for specific papers you have

### Example 2: Method Analysis
1. **Method**: Public
2. **Configuration**: Public Only
3. **Question**: "What experimental methods are used to study endocytosis in neurons?"
4. **Focus**: Check contexts for methodology details

### Example 3: Recent Findings
1. **Method**: Semantic Scholar
2. **Configuration**: Public Only
3. **Question**: "What are the latest findings on PICALM endocytosis mechanisms?"
4. **Review**: Check publication dates in contexts

This user manual covers all the features and functionality of Paper-QA. The system is designed to be both powerful and user-friendly, giving you complete control over how it works while providing detailed insights into the AI's thinking process. 