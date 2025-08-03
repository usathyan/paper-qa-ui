#!/usr/bin/env python3
"""
Paper-QA Setup Script
Helps users set up the Paper-QA project with all necessary components.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11+ is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(
        f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible"
    )
    return True


def check_uv_installed():
    """Check if uv is installed."""
    if shutil.which("uv") is None:
        print("❌ uv is not installed")
        print(
            "Please install uv: https://docs.astral.sh/uv/getting-started/installation/"
        )
        return False
    print("✅ uv is installed")
    return True


def check_ollama_installed():
    """Check if Ollama is installed."""
    if shutil.which("ollama") is None:
        print("❌ Ollama is not installed")
        print("Please install Ollama: https://ollama.ai/download")
        return False
    print("✅ Ollama is installed")
    return True


def check_ollama_running():
    """Check if Ollama is running."""
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print("✅ Ollama is running")
            return True
        else:
            print("❌ Ollama is not running")
            print("Please start Ollama: ollama serve")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Ollama is not running")
        print("Please start Ollama: ollama serve")
        return False


def setup_virtual_environment():
    """Set up virtual environment."""
    if Path(".venv").exists():
        print("✅ Virtual environment already exists")
        return True

    return run_command("uv venv --python 3.11", "Creating virtual environment")


def install_dependencies():
    """Install project dependencies."""
    return run_command("uv pip install -e .", "Installing dependencies")


def install_ollama_models():
    """Install required Ollama models."""
    return run_command(
        "ollama pull nomic-embed-text", "Installing nomic-embed-text model"
    )


def create_directories():
    """Create necessary directories."""
    directories = ["papers", "papers/picalm_alzheimer", "results", "indexes", "data"]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

    return True


def setup_environment_file():
    """Set up environment file."""
    env_template = Path("env.template")
    env_file = Path(".env")

    if env_file.exists():
        print("✅ .env file already exists")
        return True

    if env_template.exists():
        shutil.copy(env_template, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file and add your OpenRouter.ai API key")
        return True
    else:
        print("❌ env.template not found")
        return False


def check_openrouter_key():
    """Check if OpenRouter.ai API key is set."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key and api_key != "your_openrouter_api_key_here":
        print("✅ OpenRouter.ai API key is configured")
        return True
    else:
        print("⚠️  OpenRouter.ai API key not configured")
        print("Please set OPENROUTER_API_KEY in your .env file")
        return False


def run_basic_tests():
    """Run basic tests to verify setup."""
    print("🔄 Running basic tests...")
    try:
        result = subprocess.run(
            [sys.executable, "tests/test_basic_setup.py"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print("✅ Basic tests passed")
            return True
        else:
            print("❌ Basic tests failed")
            print("Test output:")
            print(result.stdout)
            print("Test errors:")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("🎉 SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Add your OpenRouter.ai API key to .env file")
    print("2. Add PDF papers to papers/ directory")
    print("3. Test the system:")
    print("   python scripts/paper_qa_cli.py --status")
    print("   python scripts/paper_qa_cli.py --demo")
    print("\nFor more information, see README.md")


def main():
    """Main setup function."""
    print("Paper-QA Setup Script")
    print("=" * 60)

    # Check prerequisites
    checks = [
        ("Python Version", check_python_version),
        ("UV Package Manager", check_uv_installed),
        ("Ollama Installation", check_ollama_installed),
        ("Ollama Running", check_ollama_running),
    ]

    for check_name, check_func in checks:
        if not check_func():
            print(f"\n❌ Setup failed: {check_name} check failed")
            return False

    # Setup steps
    setup_steps = [
        ("Virtual Environment", setup_virtual_environment),
        ("Dependencies", install_dependencies),
        ("Ollama Models", install_ollama_models),
        ("Directories", create_directories),
        ("Environment File", setup_environment_file),
    ]

    for step_name, step_func in setup_steps:
        if not step_func():
            print(f"\n❌ Setup failed: {step_name} step failed")
            return False

    # Final checks
    final_checks = [
        ("OpenRouter.ai API Key", check_openrouter_key),
        ("Basic Tests", run_basic_tests),
    ]

    for check_name, check_func in final_checks:
        check_func()  # Don't fail setup for these checks

    print_next_steps()
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
