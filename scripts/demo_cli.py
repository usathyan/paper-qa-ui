#!/usr/bin/env python3
"""
Demo script showing how the Paper-QA CLI works
This script demonstrates the CLI functionality without requiring actual API calls.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

async def demo_cli_functionality():
    """Demonstrate CLI functionality."""
    print("Paper-QA CLI Demo")
    print("=" * 60)
    
    # Check environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key and api_key != "your_openrouter_api_key_here":
        print(f"✅ OPENROUTER_API_KEY is configured (length: {len(api_key)})")
        api_configured = True
    else:
        print("⚠️ OPENROUTER_API_KEY not properly configured")
        print("   Please set your actual OpenRouter API key in .env file")
        api_configured = False
    
    # Check papers directory
    papers_dir = Path("./papers")
    if papers_dir.exists():
        pdf_files = list(papers_dir.glob("*.pdf"))
        print(f"✅ Papers directory exists with {len(pdf_files)} PDF files")
        if pdf_files:
            print("   Available papers:")
            for pdf in pdf_files:
                print(f"   - {pdf.name}")
    else:
        print("⚠️ Papers directory doesn't exist")
        papers_dir.mkdir(exist_ok=True)
        print("   Created papers directory")
    
    # Check Ollama
    try:
        import subprocess
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is running")
            if "nomic-embed-text" in result.stdout:
                print("✅ nomic-embed-text model is available")
            else:
                print("⚠️ nomic-embed-text model not found")
        else:
            print("❌ Ollama is not running")
    except FileNotFoundError:
        print("❌ Ollama not found")
    
    print("\n" + "=" * 60)
    print("CLI USAGE EXAMPLES")
    print("=" * 60)
    
    print("1. Basic query:")
    print("   paper-qa-cli 'What is this paper about?' --paper-dir ./papers")
    
    print("\n2. Query with specific configuration:")
    print("   paper-qa-cli 'What are the main findings?' --config ollama")
    
    print("\n3. Save results to file:")
    print("   paper-qa-cli 'What is the methodology?' --output results.json")
    
    print("\n4. Use different paper directory:")
    print("   paper-qa-cli 'What is this about?' --paper-dir /path/to/papers")
    
    print("\n" + "=" * 60)
    print("CONFIGURATION OPTIONS")
    print("=" * 60)
    
    configs = [
        ("openrouter_ollama", "OpenRouter LLM + Ollama embeddings (recommended)"),
        ("ollama", "Local-only processing with Ollama"),
        ("openrouter_optimized", "Optimized OpenRouter settings")
    ]
    
    for config_name, description in configs:
        config_file = Path(f"configs/{config_name}.json")
        if config_file.exists():
            print(f"✅ {config_name}: {description}")
        else:
            print(f"❌ {config_name}: Configuration file missing")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    
    if api_configured:
        print("✅ API key is configured - CLI should work!")
        print("   Try: paper-qa-cli 'What is this paper about?' --paper-dir ./papers")
    else:
        print("1. Configure your OpenRouter API key:")
        print("   - Get your key from: https://openrouter.ai/keys")
        print("   - Edit .env file and set OPENROUTER_API_KEY=your_actual_key")
        
    print("\n2. Add PDF files to ./papers/ directory")
    print("\n3. Run the CLI:")
    print("   make cli-example")
    print("   or")
    print("   paper-qa-cli 'Your question here'")
    
    print("\n4. For testing:")
    print("   make test-cli")

if __name__ == "__main__":
    import os
    asyncio.run(demo_cli_functionality()) 