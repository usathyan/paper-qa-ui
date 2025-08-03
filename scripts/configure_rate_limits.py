#!/usr/bin/env python3
"""
Configure Rate Limiting for PaperQA
Adds environment variables to .env file to improve API reliability
"""

import sys
from pathlib import Path


def configure_rate_limits():
    """Configure rate limiting environment variables"""

    env_file = Path(".env")

    if not env_file.exists():
        print("❌ .env file not found")
        return False

    # Read current .env content
    with open(env_file, "r") as f:
        current_content = f.read()

    # Rate limiting configuration to add
    rate_limit_config = """

# Rate Limiting Configuration for PaperQA APIs
# These settings help prevent rate limit errors and improve API reliability

# Semantic Scholar API (most commonly rate-limited)
SEMANTIC_SCHOLAR_API_REQUEST_TIMEOUT=30.0
SEMANTIC_SCHOLAR_API_KEY=""

# Crossref API
CROSSREF_API_REQUEST_TIMEOUT=30.0
CROSSREF_MAILTO="user@example.com"

# OpenAlex API
OPENALEX_API_REQUEST_TIMEOUT=30.0
OPENALEX_MAILTO="user@example.com"

# Unpaywall API
UNPAYWALL_TIMEOUT=30.0
UNPAYWALL_EMAIL="user@example.com"

# General API settings
PQA_VERBOSITY=3
"""

    # Check if rate limiting config already exists
    if "SEMANTIC_SCHOLAR_API_REQUEST_TIMEOUT" in current_content:
        print("✅ Rate limiting configuration already exists in .env")
        return True

    # Add rate limiting configuration
    new_content = current_content + rate_limit_config

    # Backup current .env
    backup_file = Path(".env.backup")
    if not backup_file.exists():
        with open(backup_file, "w") as f:
            f.write(current_content)
        print("📋 Created .env.backup")

    # Write updated .env
    with open(env_file, "w") as f:
        f.write(new_content)

    print("✅ Added rate limiting configuration to .env")
    print("📝 Please update the email addresses in .env with your actual email")

    return True


def optimize_configurations():
    """Optimize PaperQA configuration files for better rate limit handling"""

    configs = {
        "configs/public_only.json": {
            "agent": {
                "concurrency": 2,  # Reduced from 5
                "search_count": 15,  # Reduced from 50
                "timeout": 600.0,  # Increased from 500.0
            },
            "answer": {"max_concurrent_requests": 2},  # Reduced from 4
        },
        "configs/default.json": {
            "agent": {
                "concurrency": 3,  # Reduced from 5
                "search_count": 20,  # Reduced from 25
                "timeout": 600.0,  # Increased from 600.0 (already good)
            },
            "answer": {"max_concurrent_requests": 3},  # Reduced from 4
        },
    }

    import json

    for config_file, optimizations in configs.items():
        config_path = Path(config_file)

        if not config_path.exists():
            print(f"⚠️ {config_file} not found, skipping")
            continue

        # Read current config
        with open(config_path, "r") as f:
            config = json.load(f)

        # Apply optimizations
        for section, settings in optimizations.items():
            if section not in config:
                config[section] = {}

            for key, value in settings.items():
                if section == "agent" and key == "index":
                    if "index" not in config["agent"]:
                        config["agent"]["index"] = {}
                    config["agent"]["index"].update(value)
                else:
                    config[section][key] = value

        # Write updated config
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        print(f"✅ Optimized {config_file} for rate limit handling")


def main():
    """Main function"""

    print("🔧 Configuring Rate Limiting for PaperQA")
    print("=" * 50)

    # Configure environment variables
    if configure_rate_limits():
        print("\n📋 Rate limiting environment variables added")
    else:
        print("\n❌ Failed to configure environment variables")
        return False

    # Optimize configurations
    print("\n⚙️ Optimizing configuration files...")
    optimize_configurations()

    print("\n✅ Rate limiting configuration complete!")
    print("\n📝 Next steps:")
    print("1. Edit .env file and update email addresses")
    print("2. Restart your terminal to load new environment variables")
    print(
        "3. Test with: python3 scripts/paper_qa_cli.py --question 'test' --method public"
    )

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
