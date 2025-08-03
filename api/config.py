import os
from paperqa import Settings
from paperqa.settings import AgentSettings
from dotenv import load_dotenv
# from api.retry_utils import retry_on_rate_limit, retry_on_api_error

load_dotenv()

def get_openrouter_settings():
    """
    Get OpenRouter.ai settings for cloud LLM functionality with proper LiteLLM configuration.
    
    This configuration addresses the LiteLLM streaming and caching issues mentioned in:
    https://github.com/Future-House/paper-qa/issues/904
    
    Key fixes:
    - Proper model naming with provider prefix
    - Correct LiteLLM parameter structure
    - Disabled streaming to avoid compatibility issues
    - Proper caching configuration
    """
    
    # OpenRouter configuration - using Ollama for embeddings only
    settings = Settings(
        llm="openrouter/z-ai/glm-4.5-air:free",
        summary_llm="openrouter/z-ai/glm-4.5-air:free", 
        embedding="ollama/nomic-embed-text:latest",  # Use Ollama for embeddings
        verbosity=3,  # Maximum verbosity - all LLM/Embeddings calls and detailed logging
        prompts={'use_json': False},  # Disable JSON output to avoid parsing errors
        # Alternative model option (commented out):
        # llm="openrouter/google/gemma-3n-e2b-it:free",
        # summary_llm="openrouter/google/gemma-3n-e2b-it:free",
        llm_config={
            "model_list": [
                {
                    "model_name": "openrouter/z-ai/glm-4.5-air:free",
                    "litellm_params": {
                        "model": "openrouter/z-ai/glm-4.5-air:free",
                        "api_key": os.getenv("OPENROUTER_API_KEY"),
                        "api_base": "https://openrouter.ai/api/v1",
                        # LiteLLM configuration fixes based on GitHub issue #904
                        "stream": False,  # Disable streaming to avoid compatibility issues
                        "timeout": 600,   # 10 minute timeout
                        "max_retries": 3, # Retry failed requests
                        # Caching configuration (disabled for now due to compatibility issues)
                        # "cache": None,  # Disable caching to avoid bool error
                    },
                    "cost": 0.0,  # Free tier
                    "input_cost_per_token": 0.0,
                    "output_cost_per_token": 0.0
                }
            ]
        },
        summary_llm_config={
            "model_list": [
                {
                    "model_name": "openrouter/z-ai/glm-4.5-air:free",
                    "litellm_params": {
                        "model": "openrouter/z-ai/glm-4.5-air:free",
                        "api_key": os.getenv("OPENROUTER_API_KEY"),
                        "api_base": "https://openrouter.ai/api/v1",
                        "stream": False,
                        "timeout": 600,
                        "max_retries": 3,
                    }
                }
            ]
        },
        agent=AgentSettings(
            agent_type="ToolSelector",
            should_pre_search=True,
            search_count=5,
            tool_names=[
                "PaperSearch",
                "GatherEvidence", 
                "GenerateAnswer"
            ],
            agent_llm="openrouter/z-ai/glm-4.5-air:free",
            agent_llm_config={
                "model_list": [
                    {
                        "model_name": "openrouter/z-ai/glm-4.5-air:free",
                        "litellm_params": {
                            "model": "openrouter/z-ai/glm-4.5-air:free",
                            "api_key": os.getenv("OPENROUTER_API_KEY"),
                            "api_base": "https://openrouter.ai/api/v1",
                            "stream": False,
                            "timeout": 600,
                            "max_retries": 3,
                        }
                    }
                ]
            }
        )
    )
    
    return settings

def get_openrouter_gemma_settings():
    """
    Get OpenRouter.ai settings with Google Gemma model with proper LiteLLM configuration.
    
    This configuration addresses the LiteLLM streaming and caching issues mentioned in:
    https://github.com/Future-House/paper-qa/issues/904
    """
    
    # OpenRouter configuration with Google Gemma - using Ollama for embeddings only
    settings = Settings(
        llm="openrouter/google/gemma-3n-e2b-it:free",
        summary_llm="openrouter/google/gemma-3n-e2b-it:free", 
        embedding="ollama/nomic-embed-text:latest",  # Use Ollama for embeddings
        verbosity=3,  # Maximum verbosity - all LLM/Embeddings calls and detailed logging
        prompts={'use_json': False},  # Disable JSON output to avoid parsing errors
        llm_config={
            "model_list": [
                {
                    "model_name": "openrouter/google/gemma-3n-e2b-it:free",
                    "litellm_params": {
                        "model": "openrouter/google/gemma-3n-e2b-it:free",
                        "api_key": os.getenv("OPENROUTER_API_KEY"),
                        "api_base": "https://openrouter.ai/api/v1",
                        # LiteLLM configuration fixes
                        "stream": False,  # Disable streaming to avoid compatibility issues
                        "timeout": 600,   # 10 minute timeout
                        "max_retries": 3, # Retry failed requests
                    },
                    "cost": 0.0,  # Free tier
                    "input_cost_per_token": 0.0,
                    "output_cost_per_token": 0.0
                }
            ]
        },
        summary_llm_config={
            "model_list": [
                {
                    "model_name": "openrouter/google/gemma-3n-e2b-it:free",
                    "litellm_params": {
                        "model": "openrouter/google/gemma-3n-e2b-it:free",
                        "api_key": os.getenv("OPENROUTER_API_KEY"),
                        "api_base": "https://openrouter.ai/api/v1",
                        "stream": False,
                        "timeout": 600,
                        "max_retries": 3,
                    }
                }
            ]
        },
        agent=AgentSettings(
            agent_type="ToolSelector",
            should_pre_search=True,
            search_count=5,
            tool_names=[
                "PaperSearch",
                "GatherEvidence", 
                "GenerateAnswer"
            ],
            agent_llm="openrouter/google/gemma-3n-e2b-it:free",
            agent_llm_config={
                "model_list": [
                    {
                        "model_name": "openrouter/google/gemma-3n-e2b-it:free",
                        "litellm_params": {
                            "model": "openrouter/google/gemma-3n-e2b-it:free",
                            "api_key": os.getenv("OPENROUTER_API_KEY"),
                            "api_base": "https://openrouter.ai/api/v1",
                            "stream": False,
                            "timeout": 600,
                            "max_retries": 3,
                        }
                    }
                ]
            }
        )
    )
    
    return settings

def get_ollama_settings():
    """
    Get Ollama settings for local LLM functionality with proper LiteLLM configuration.
    
    This configuration addresses the LiteLLM streaming and caching issues mentioned in:
    https://github.com/Future-House/paper-qa/issues/904
    """
    
    settings = Settings(
        llm="ollama/gemma3:latest",
        summary_llm="ollama/gemma3:latest",
        embedding="ollama/nomic-embed-text:latest",
        verbosity=3,  # Maximum verbosity - all LLM/Embeddings calls and detailed logging
        prompts={'use_json': False},  # Disable JSON output to avoid parsing errors
        llm_config={
            "model_list": [
                {
                    "model_name": "ollama/gemma3:latest",
                    "litellm_params": {
                        "model": "ollama/gemma3:latest",
                        "api_base": "http://localhost:11434",
                        "api_type": "ollama",
                        # LiteLLM configuration fixes for Ollama
                        "stream": False,  # Disable streaming to avoid compatibility issues
                        "timeout": 600,   # 10 minute timeout
                        "max_retries": 3, # Retry failed requests
                        # Ollama-specific parameters
                        "temperature": 0.7,
                        "max_tokens": 4096,
                    }
                }
            ]
        },
        summary_llm_config={
            "model_list": [
                {
                    "model_name": "ollama/gemma3:latest",
                    "litellm_params": {
                        "model": "ollama/gemma3:latest",
                        "api_base": "http://localhost:11434",
                        "api_type": "ollama",
                        "stream": False,
                        "timeout": 600,
                        "max_retries": 3,
                        "temperature": 0.7,
                        "max_tokens": 4096,
                    }
                }
            ]
        },
        agent=AgentSettings(
            agent_type="ToolSelector",
            should_pre_search=False,  # Disable search for local only
            tool_names=[
                "GatherEvidence",
                "GenerateAnswer"
            ],
            agent_llm="ollama/gemma3:latest",
            agent_llm_config={
                "model_list": [
                    {
                        "model_name": "ollama/gemma3:latest",
                        "litellm_params": {
                            "model": "ollama/gemma3:latest",
                            "api_base": "http://localhost:11434",
                            "api_type": "ollama",
                            "stream": False,
                            "timeout": 600,
                            "max_retries": 3,
                            "temperature": 0.7,
                            "max_tokens": 4096,
                        }
                    }
                ]
            }
        )
    )
    
    return settings

def get_settings(use_gemma=False, use_ollama=False):
    """
    Get settings based on configuration preference.
    
    Args:
        use_gemma (bool): Use OpenRouter with Google Gemma model
        use_ollama (bool): Use Ollama for both LLM and embeddings (default to avoid rate limits)
    
    Returns:
        Settings: Configured PaperQA settings
    """
    if use_ollama:
        return get_ollama_settings()
    elif use_gemma:
        return get_openrouter_gemma_settings()
    else:
        # Default to Ollama to avoid OpenRouter rate limiting
        return get_ollama_settings()

def validate_environment():
    """
    Validate that required environment variables and services are available.
    
    Returns:
        dict: Validation results with status and messages
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
    
    # Check if Ollama server is running (basic check)
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