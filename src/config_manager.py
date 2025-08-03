"""
Configuration Management for Paper-QA
Handles loading, validation, and management of configuration files.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

from paperqa import Settings


class ConfigManager:
    """Manages Paper-QA configuration files and settings."""

    def __init__(self, config_dir: str = "configs"):
        """Initialize configuration manager."""
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        config_file = self.config_dir / f"{config_name}.json"

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_file, "r") as f:
            config = json.load(f)

        return config

    def save_config(self, config_name: str, config: Dict[str, Any]) -> None:
        """Save configuration to JSON file."""
        config_file = self.config_dir / f"{config_name}.json"

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

    def get_settings(self, config_name: str) -> Settings:
        """Get Paper-QA Settings object from configuration."""
        config = self.load_config(config_name)

        # Create Settings object with full configuration
        # Pass all configuration parameters to Settings constructor
        return Settings(**config)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure."""
        required_keys = ["llm", "summary_llm", "embedding"]

        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing required configuration key: {key}")

        return True

    def merge_configs(self, base_config: str, override_config: str) -> Dict[str, Any]:
        """Merge two configurations, with override taking precedence."""
        base = self.load_config(base_config)
        override = self.load_config(override_config)

        def deep_merge(d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
            """Recursively merge two dictionaries."""
            result = d1.copy()

            for key, value in d2.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value

            return result

        return deep_merge(base, override)

    def create_custom_config(
        self, config_name: str, llm: str, embedding: str, **kwargs
    ) -> None:
        """Create a custom configuration with specified parameters."""
        config = {
            "llm": llm,
            "summary_llm": llm,
            "embedding": embedding,
            "temperature": 0.0,
            "verbosity": 2,
            **kwargs,
        }

        self.validate_config(config)
        self.save_config(config_name, config)

    def list_configs(self) -> list[str]:
        """List all available configuration files."""
        configs = []
        for config_file in self.config_dir.glob("*.json"):
            configs.append(config_file.stem)
        return sorted(configs)

    def get_config_info(self, config_name: str) -> Dict[str, Any]:
        """Get information about a configuration."""
        config = self.load_config(config_name)

        return {
            "name": config_name,
            "llm": config.get("llm"),
            "embedding": config.get("embedding"),
            "temperature": config.get("temperature", 0.0),
            "verbosity": config.get("verbosity", 0),
            "has_agent_config": "agent" in config,
            "has_answer_config": "answer" in config,
            "has_parsing_config": "parsing" in config,
        }


def load_env_variables() -> None:
    """Load environment variables from .env file."""
    from dotenv import load_dotenv

    # Try to load from .env file
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
    else:
        print("No .env file found. Using system environment variables.")


def validate_environment() -> Dict[str, bool]:
    """Validate that required environment variables are set."""
    required_vars = {
        "OPENROUTER_API_KEY": "OpenRouter.ai API key for Google Gemini 2.5 Flash Lite"
    }

    optional_vars = {
        "PQA_HOME": "Paper-QA home directory",
        "PAPER_DIRECTORY": "Paper directory",
        "INDEX_DIRECTORY": "Index directory",
        "SEMANTIC_SCHOLAR_API_REQUEST_TIMEOUT": "Semantic Scholar timeout",
        "CROSSREF_API_REQUEST_TIMEOUT": "Crossref timeout",
        "OPENALEX_API_REQUEST_TIMEOUT": "OpenAlex timeout",
        "UNPAYWALL_TIMEOUT": "Unpaywall timeout",
    }

    validation = {}

    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        validation[var] = value is not None
        if not validation[var]:
            print(
                f"WARNING: Required environment variable {var} ({description}) is not set"
            )

    # Check optional variables
    for var, description in optional_vars.items():
        value = os.getenv(var)
        validation[var] = value is not None
        if validation[var]:
            print(f"INFO: Optional environment variable {var} ({description}) is set")

    return validation


def setup_environment() -> None:
    """Setup environment for Paper-QA."""
    load_env_variables()
    validation = validate_environment()

    if not validation.get("OPENROUTER_API_KEY"):
        print("\nERROR: OPENROUTER_API_KEY is required!")
        print("Please set your OpenRouter.ai API key:")
        print("1. Get your API key from https://openrouter.ai/")
        print("2. Create a .env file with: OPENROUTER_API_KEY=your_key_here")
        print("3. Or set it as an environment variable")
        raise ValueError("OPENROUTER_API_KEY not set")

    print("\nEnvironment setup complete!")
    print("Paper-QA is ready to use with OpenRouter.ai and Ollama.")
