# PaperQA Discovery Configuration Guide

## Overview

This guide provides configuration examples for different LLM providers that can be used with PaperQA Discovery. The system is designed to work with any LiteLLM-compatible provider, allowing you to switch between local (Ollama) and cloud-based AI services.

## Current Configuration (Ollama - Local)

The current setup uses Ollama with local models:

```python
# Current settings in api/main.py
settings = Settings(
    llm="ollama/gemma3:latest",
    summary_llm="ollama/gemma3:latest", 
    embedding="ollama/nomic-embed-text:latest",
    llm_config={
        "model_list": [
            {
                "model_name": "ollama/gemma3:latest",
                "litellm_params": {
                    "model": "ollama/gemma3:latest",
                    "api_base": "http://localhost:11434"
                },
                "cost": 0.0,
                "input_cost_per_token": 0.0,
                "output_cost_per_token": 0.0
            }
        ]
    }
)
```

## Cloud Provider Configurations

### 1. Azure OpenAI Configuration

#### Azure OpenAI (Latest Models)

```python
# Environment Variables
export AZURE_OPENAI_API_KEY="your-azure-openai-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2024-02-15-preview"

# Configuration
settings = Settings(
    llm="azure/gpt-4o",
    summary_llm="azure/gpt-4o-mini",
    embedding="azure/text-embedding-ada-002",
    llm_config={
        "model_list": [
            {
                "model_name": "azure/gpt-4o",
                "litellm_params": {
                    "model": "gpt-4o",
                    "api_key": "your-azure-openai-key",
                    "api_base": "https://your-resource.openai.azure.com/",
                    "api_version": "2024-02-15-preview"
                },
                "cost": 0.005,  # $0.005 per 1K input tokens
                "input_cost_per_token": 0.000005,
                "output_cost_per_token": 0.000015
            },
            {
                "model_name": "azure/gpt-4o-mini",
                "litellm_params": {
                    "model": "gpt-4o-mini",
                    "api_key": "your-azure-openai-key",
                    "api_base": "https://your-resource.openai.azure.com/",
                    "api_version": "2024-02-15-preview"
                },
                "cost": 0.00015,  # $0.00015 per 1K input tokens
                "input_cost_per_token": 0.00000015,
                "output_cost_per_token": 0.0000006
            }
        ]
    },
    summary_llm_config={
        "model_list": [
            {
                "model_name": "azure/gpt-4o-mini",
                "litellm_params": {
                    "model": "gpt-4o-mini",
                    "api_key": "your-azure-openai-key",
                    "api_base": "https://your-resource.openai.azure.com/",
                    "api_version": "2024-02-15-preview"
                },
                "cost": 0.00015,
                "input_cost_per_token": 0.00000015,
                "output_cost_per_token": 0.0000006
            }
        ]
    },
    agent=AgentSettings(
        agent_llm="azure/gpt-4o",
        agent_llm_config={
            "model_list": [
                {
                    "model_name": "azure/gpt-4o",
                    "litellm_params": {
                        "model": "gpt-4o",
                        "api_key": "your-azure-openai-key",
                        "api_base": "https://your-resource.openai.azure.com/",
                        "api_version": "2024-02-15-preview"
                    },
                    "cost": 0.005,
                    "input_cost_per_token": 0.000005,
                    "output_cost_per_token": 0.000015
                }
            ]
        }
    )
)
```

#### Azure OpenAI (Previous Generation Models)

```python
# Environment Variables
export AZURE_OPENAI_API_KEY="your-azure-openai-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_VERSION="2023-12-01-preview"

# Configuration for GPT-4 and GPT-3.5
settings = Settings(
    llm="azure/gpt-4",
    summary_llm="azure/gpt-3.5-turbo",
    embedding="azure/text-embedding-ada-002",
    llm_config={
        "model_list": [
            {
                "model_name": "azure/gpt-4",
                "litellm_params": {
                    "model": "gpt-4",
                    "api_key": "your-azure-openai-key",
                    "api_base": "https://your-resource.openai.azure.com/",
                    "api_version": "2023-12-01-preview"
                },
                "cost": 0.03,  # $0.03 per 1K input tokens
                "input_cost_per_token": 0.00003,
                "output_cost_per_token": 0.00006
            },
            {
                "model_name": "azure/gpt-4-turbo",
                "litellm_params": {
                    "model": "gpt-4-turbo",
                    "api_key": "your-azure-openai-key",
                    "api_base": "https://your-resource.openai.azure.com/",
                    "api_version": "2023-12-01-preview"
                },
                "cost": 0.01,  # $0.01 per 1K input tokens
                "input_cost_per_token": 0.00001,
                "output_cost_per_token": 0.00003
            }
        ]
    },
    summary_llm_config={
        "model_list": [
            {
                "model_name": "azure/gpt-3.5-turbo",
                "litellm_params": {
                    "model": "gpt-3.5-turbo",
                    "api_key": "your-azure-openai-key",
                    "api_base": "https://your-resource.openai.azure.com/",
                    "api_version": "2023-12-01-preview"
                },
                "cost": 0.0015,  # $0.0015 per 1K input tokens
                "input_cost_per_token": 0.0000015,
                "output_cost_per_token": 0.000002
            }
        ]
    },
    agent=AgentSettings(
        agent_llm="azure/gpt-4",
        agent_llm_config={
            "model_list": [
                {
                    "model_name": "azure/gpt-4",
                    "litellm_params": {
                        "model": "gpt-4",
                        "api_key": "your-azure-openai-key",
                        "api_base": "https://your-resource.openai.azure.com/",
                        "api_version": "2023-12-01-preview"
                    },
                    "cost": 0.03,
                    "input_cost_per_token": 0.00003,
                    "output_cost_per_token": 0.00006
                }
            ]
        }
    )
)
```

### 2. Google Cloud (Gemini) Configuration

```python
# Environment Variables
export GOOGLE_API_KEY="your-gemini-api-key"

# Configuration
settings = Settings(
    llm="gemini/gemini-2.0-flash-exp",
    summary_llm="gemini/gemini-1.5-flash",
    embedding="gemini/embedding-001",
    llm_config={
        "model_list": [
            {
                "model_name": "gemini/gemini-2.0-flash-exp",
                "litellm_params": {
                    "model": "gemini-2.0-flash-exp",
                    "api_key": "your-gemini-api-key"
                },
                "cost": 0.00075,  # $0.00075 per 1M input tokens
                "input_cost_per_token": 0.00000075,
                "output_cost_per_token": 0.000003
            },
            {
                "model_name": "gemini/gemini-1.5-pro",
                "litellm_params": {
                    "model": "gemini-1.5-pro",
                    "api_key": "your-gemini-api-key"
                },
                "cost": 0.0035,  # $0.0035 per 1M input tokens
                "input_cost_per_token": 0.0000035,
                "output_cost_per_token": 0.0000105
            }
        ]
    },
    summary_llm_config={
        "model_list": [
            {
                "model_name": "gemini/gemini-1.5-flash",
                "litellm_params": {
                    "model": "gemini-1.5-flash",
                    "api_key": "your-gemini-api-key"
                },
                "cost": 0.000075,  # $0.000075 per 1M input tokens
                "input_cost_per_token": 0.000000075,
                "output_cost_per_token": 0.0000003
            }
        ]
    },
    agent=AgentSettings(
        agent_llm="gemini/gemini-2.0-flash-exp",
        agent_llm_config={
            "model_list": [
                {
                    "model_name": "gemini/gemini-2.0-flash-exp",
                    "litellm_params": {
                        "model": "gemini-2.0-flash-exp",
                        "api_key": "your-gemini-api-key"
                    },
                    "cost": 0.00075,
                    "input_cost_per_token": 0.00000075,
                    "output_cost_per_token": 0.000003
                }
            ]
        }
    )
)
```

### 3. Amazon Bedrock Configuration

```python
# Environment Variables
export AWS_PROFILE="your-aws-profile"
export AWS_DEFAULT_REGION="us-east-1"  # or your preferred region

# Configuration
settings = Settings(
    llm="bedrock/anthropic.claude-3-5-sonnet-20241022-v1:0",
    summary_llm="bedrock/anthropic.claude-3-haiku-20240307-v1:0",
    embedding="bedrock/amazon.titan-embed-text-v1",
    llm_config={
        "model_list": [
            {
                "model_name": "bedrock/anthropic.claude-3-5-sonnet-20241022-v1:0",
                "litellm_params": {
                    "model": "anthropic.claude-3-5-sonnet-20241022-v1:0",
                    "aws_profile": "your-aws-profile",
                    "aws_region": "us-east-1"
                },
                "cost": 0.003,  # $0.003 per 1K input tokens
                "input_cost_per_token": 0.000003,
                "output_cost_per_token": 0.000015
            },
            {
                "model_name": "bedrock/anthropic.claude-3-opus-20240229-v1:0",
                "litellm_params": {
                    "model": "anthropic.claude-3-opus-20240229-v1:0",
                    "aws_profile": "your-aws-profile",
                    "aws_region": "us-east-1"
                },
                "cost": 0.015,  # $0.015 per 1K input tokens
                "input_cost_per_token": 0.000015,
                "output_cost_per_token": 0.000075
            }
        ]
    },
    summary_llm_config={
        "model_list": [
            {
                "model_name": "bedrock/anthropic.claude-3-haiku-20240307-v1:0",
                "litellm_params": {
                    "model": "anthropic.claude-3-haiku-20240307-v1:0",
                    "aws_profile": "your-aws-profile",
                    "aws_region": "us-east-1"
                },
                "cost": 0.00025,  # $0.00025 per 1K input tokens
                "input_cost_per_token": 0.00000025,
                "output_cost_per_token": 0.00000125
            }
        ]
    },
    agent=AgentSettings(
        agent_llm="bedrock/anthropic.claude-3-5-sonnet-20241022-v1:0",
        agent_llm_config={
            "model_list": [
                {
                    "model_name": "bedrock/anthropic.claude-3-5-sonnet-20241022-v1:0",
                    "litellm_params": {
                        "model": "anthropic.claude-3-5-sonnet-20241022-v1:0",
                        "aws_profile": "your-aws-profile",
                        "aws_region": "us-east-1"
                    },
                    "cost": 0.003,
                    "input_cost_per_token": 0.000003,
                    "output_cost_per_token": 0.000015
                }
            ]
        }
    )
)
```

## Implementation Guide

### Step 1: Update Environment Variables

Create a `.env` file in your project root:

```bash
# .env file
# Choose one of the following configurations:

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# OR Google Gemini
GOOGLE_API_KEY=your-gemini-api-key

# OR Amazon Bedrock
AWS_PROFILE=your-aws-profile
AWS_DEFAULT_REGION=us-east-1

# External APIs (for public domain search)
SEMANTIC_SCHOLAR_API_KEY=your-semantic-scholar-key
CROSSREF_API_KEY=your-crossref-key
```

### Step 2: Update API Configuration

Create a new file `api/config.py`:

```python
# api/config.py
import os
from paperqa import Settings, AgentSettings
from dotenv import load_dotenv

load_dotenv()

def get_settings():
    """Get settings based on environment configuration"""
    
    # Check which provider to use
    if os.getenv("AZURE_OPENAI_API_KEY"):
        return get_azure_settings()
    elif os.getenv("GOOGLE_API_KEY"):
        return get_gemini_settings()
    elif os.getenv("AWS_PROFILE"):
        return get_bedrock_settings()
    else:
        return get_ollama_settings()  # Default fallback

def get_azure_settings():
    """Azure OpenAI configuration"""
    return Settings(
        llm="azure/gpt-4o",
        summary_llm="azure/gpt-4o-mini",
        embedding="azure/text-embedding-ada-002",
        llm_config={
            "model_list": [
                {
                    "model_name": "azure/gpt-4o",
                    "litellm_params": {
                        "model": "gpt-4o",
                        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                        "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
                        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
                    },
                    "cost": 0.005,
                    "input_cost_per_token": 0.000005,
                    "output_cost_per_token": 0.000015
                }
            ]
        },
        summary_llm_config={
            "model_list": [
                {
                    "model_name": "azure/gpt-4o-mini",
                    "litellm_params": {
                        "model": "gpt-4o-mini",
                        "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                        "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
                        "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
                    },
                    "cost": 0.00015,
                    "input_cost_per_token": 0.00000015,
                    "output_cost_per_token": 0.0000006
                }
            ]
        },
        agent=AgentSettings(
            agent_llm="azure/gpt-4o",
            agent_llm_config={
                "model_list": [
                    {
                        "model_name": "azure/gpt-4o",
                        "litellm_params": {
                            "model": "gpt-4o",
                            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
                            "api_base": os.getenv("AZURE_OPENAI_ENDPOINT"),
                            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
                        },
                        "cost": 0.005,
                        "input_cost_per_token": 0.000005,
                        "output_cost_per_token": 0.000015
                    }
                ]
            }
        ),
        index={"index_directory": "pqa_index"},
        verbosity=3
    )

def get_gemini_settings():
    """Google Gemini configuration"""
    return Settings(
        llm="gemini/gemini-2.0-flash-exp",
        summary_llm="gemini/gemini-1.5-flash",
        embedding="gemini/embedding-001",
        llm_config={
            "model_list": [
                {
                    "model_name": "gemini/gemini-2.0-flash-exp",
                    "litellm_params": {
                        "model": "gemini-2.0-flash-exp",
                        "api_key": os.getenv("GOOGLE_API_KEY")
                    },
                    "cost": 0.00075,
                    "input_cost_per_token": 0.00000075,
                    "output_cost_per_token": 0.000003
                }
            ]
        },
        summary_llm_config={
            "model_list": [
                {
                    "model_name": "gemini/gemini-1.5-flash",
                    "litellm_params": {
                        "model": "gemini-1.5-flash",
                        "api_key": os.getenv("GOOGLE_API_KEY")
                    },
                    "cost": 0.000075,
                    "input_cost_per_token": 0.000000075,
                    "output_cost_per_token": 0.0000003
                }
            ]
        },
        agent=AgentSettings(
            agent_llm="gemini/gemini-2.0-flash-exp",
            agent_llm_config={
                "model_list": [
                    {
                        "model_name": "gemini/gemini-2.0-flash-exp",
                        "litellm_params": {
                            "model": "gemini-2.0-flash-exp",
                            "api_key": os.getenv("GOOGLE_API_KEY")
                        },
                        "cost": 0.00075,
                        "input_cost_per_token": 0.00000075,
                        "output_cost_per_token": 0.000003
                    }
                ]
            }
        ),
        index={"index_directory": "pqa_index"},
        verbosity=3
    )

def get_bedrock_settings():
    """Amazon Bedrock configuration"""
    return Settings(
        llm="bedrock/anthropic.claude-3-5-sonnet-20241022-v1:0",
        summary_llm="bedrock/anthropic.claude-3-haiku-20240307-v1:0",
        embedding="bedrock/amazon.titan-embed-text-v1",
        llm_config={
            "model_list": [
                {
                    "model_name": "bedrock/anthropic.claude-3-5-sonnet-20241022-v1:0",
                    "litellm_params": {
                        "model": "anthropic.claude-3-5-sonnet-20241022-v1:0",
                        "aws_profile": os.getenv("AWS_PROFILE"),
                        "aws_region": os.getenv("AWS_DEFAULT_REGION", "us-east-1")
                    },
                    "cost": 0.003,
                    "input_cost_per_token": 0.000003,
                    "output_cost_per_token": 0.000015
                }
            ]
        },
        summary_llm_config={
            "model_list": [
                {
                    "model_name": "bedrock/anthropic.claude-3-haiku-20240307-v1:0",
                    "litellm_params": {
                        "model": "anthropic.claude-3-haiku-20240307-v1:0",
                        "aws_profile": os.getenv("AWS_PROFILE"),
                        "aws_region": os.getenv("AWS_DEFAULT_REGION", "us-east-1")
                    },
                    "cost": 0.00025,
                    "input_cost_per_token": 0.00000025,
                    "output_cost_per_token": 0.00000125
                }
            ]
        },
        agent=AgentSettings(
            agent_llm="bedrock/anthropic.claude-3-5-sonnet-20241022-v1:0",
            agent_llm_config={
                "model_list": [
                    {
                        "model_name": "bedrock/anthropic.claude-3-5-sonnet-20241022-v1:0",
                        "litellm_params": {
                            "model": "anthropic.claude-3-5-sonnet-20241022-v1:0",
                            "aws_profile": os.getenv("AWS_PROFILE"),
                            "aws_region": os.getenv("AWS_DEFAULT_REGION", "us-east-1")
                        },
                        "cost": 0.003,
                        "input_cost_per_token": 0.000003,
                        "output_cost_per_token": 0.000015
                    }
                ]
            }
        ),
        index={"index_directory": "pqa_index"},
        verbosity=3
    )

def get_ollama_settings():
    """Default Ollama configuration"""
    return Settings(
        llm="ollama/gemma3:latest",
        summary_llm="ollama/gemma3:latest",
        embedding="ollama/nomic-embed-text:latest",
        llm_config={
            "model_list": [
                {
                    "model_name": "ollama/gemma3:latest",
                    "litellm_params": {
                        "model": "ollama/gemma3:latest",
                        "api_base": "http://localhost:11434"
                    },
                    "cost": 0.0,
                    "input_cost_per_token": 0.0,
                    "output_cost_per_token": 0.0
                }
            ]
        },
        summary_llm_config={
            "model_list": [
                {
                    "model_name": "ollama/gemma3:latest",
                    "litellm_params": {
                        "model": "ollama/gemma3:latest",
                        "api_base": "http://localhost:11434"
                    },
                    "cost": 0.0,
                    "input_cost_per_token": 0.0,
                    "output_cost_per_token": 0.0
                }
            ]
        },
        agent=AgentSettings(
            agent_llm="ollama/gemma3:latest",
            agent_llm_config={
                "model_list": [
                    {
                        "model_name": "ollama/gemma3:latest",
                        "litellm_params": {
                            "model": "ollama/gemma3:latest",
                            "api_base": "http://localhost:11434"
                        },
                        "cost": 0.0,
                        "input_cost_per_token": 0.0,
                        "output_cost_per_token": 0.0
                    }
                ]
            }
        ),
        index={"index_directory": "pqa_index"},
        verbosity=3
    )
```

### Step 3: Update main.py

Update `api/main.py` to use the new configuration:

```python
# api/main.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from paperqa import Docs
from paperqa.settings import Settings, AgentSettings
from paperqa.agents.tools import PaperSearch, GatherEvidence, GenerateAnswer, Reset, Complete
from typing import List
import shutil
import os
from dotenv import load_dotenv
import logging

# Import the new configuration
from .config import get_settings

load_dotenv()

logging.basicConfig(level=logging.INFO)
logging.getLogger("paperqa").setLevel(logging.INFO)
logging.getLogger("litellm").setLevel(logging.DEBUG)

app = FastAPI()

# Set up CORS
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_papers"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Use the new configuration system
settings = get_settings()
docs = Docs()

# ... rest of the file remains the same
```

## Cost Comparison

| Provider | Model | Input Cost (per 1K tokens) | Output Cost (per 1K tokens) | Best For |
|----------|-------|---------------------------|----------------------------|----------|
| **Ollama** | gemma3 | $0.00 | $0.00 | Development, Privacy |
| **Azure OpenAI** | gpt-4o | $0.005 | $0.015 | Production, High Quality |
| **Azure OpenAI** | gpt-4o-mini | $0.00015 | $0.0006 | Cost-effective |
| **Google Gemini** | gemini-2.0-flash-exp | $0.00075 | $0.003 | Balanced |
| **Google Gemini** | gemini-1.5-flash | $0.000075 | $0.0003 | Very Cost-effective |
| **Amazon Bedrock** | claude-3-5-sonnet | $0.003 | $0.015 | High Quality |
| **Amazon Bedrock** | claude-3-haiku | $0.00025 | $0.00125 | Cost-effective |

## Model Capabilities Comparison

| Model | Context Window | Reasoning | Code | Multimodal | Best Use Case |
|-------|---------------|-----------|------|------------|---------------|
| **gpt-4o** | 128K | Excellent | Excellent | Yes | Complex reasoning, code generation |
| **gpt-4o-mini** | 128K | Good | Good | Yes | General purpose, cost-effective |
| **gemini-2.0-flash-exp** | 1M | Excellent | Good | Yes | Long documents, reasoning |
| **gemini-1.5-flash** | 1M | Good | Good | Yes | Cost-effective, long context |
| **claude-3-5-sonnet** | 200K | Excellent | Excellent | Yes | Complex analysis, coding |
| **claude-3-haiku** | 200K | Good | Good | Yes | Fast responses, cost-effective |
| **gemma3** | 8K | Good | Good | No | Local development, privacy |

## Deployment Considerations

### Security
- **Azure OpenAI**: Enterprise-grade security, SOC 2 compliance
- **Google Gemini**: Google Cloud security, data residency options
- **Amazon Bedrock**: AWS security, VPC support
- **Ollama**: Local deployment, no data leaves your infrastructure

### Latency
- **Ollama**: Fastest (local), depends on hardware
- **Azure OpenAI**: Very fast, global CDN
- **Google Gemini**: Fast, Google's infrastructure
- **Amazon Bedrock**: Good, AWS global infrastructure

### Reliability
- **Azure OpenAI**: 99.9% SLA, enterprise support
- **Google Gemini**: High availability, Google's infrastructure
- **Amazon Bedrock**: AWS reliability, multiple regions
- **Ollama**: Depends on local infrastructure

## Testing Your Configuration

After updating the configuration, test it with:

```bash
# Test the backend
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main topic of the McKinsey paper?", "source": "My Papers"}'

# Check which provider is being used
curl http://localhost:8000/api/papers
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify API keys are correct
   - Check environment variables are loaded
   - Ensure proper permissions for AWS profiles

2. **Rate Limiting**:
   - Implement retry logic
   - Use appropriate model tiers
   - Monitor usage quotas

3. **Cost Optimization**:
   - Use smaller models for summaries
   - Implement caching
   - Monitor token usage

### Debug Mode

Enable debug logging by setting:

```bash
export LITELLM_LOG="DEBUG"
export PAPERQA_VERBOSITY=3
```

This will show detailed information about API calls, token usage, and costs. 