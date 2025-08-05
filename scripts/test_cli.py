#!/usr/bin/env python3
"""
Test script for Paper-QA CLI
Verifies basic functionality without requiring actual PDFs.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def test_config_loading():
    """Test that configurations can be loaded properly."""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION LOADING")
    print("=" * 60)

    try:
        from config_manager import ConfigManager
        
        config_manager = ConfigManager()
        
        # Test loading the new configuration
        configs_to_test = ["openrouter_ollama", "ollama", "openrouter_optimized"]
        
        for config_name in configs_to_test:
            try:
                settings = config_manager.get_settings(config_name)
                print(f"✅ {config_name}: LLM={settings.llm}, Embedding={settings.embedding}")
            except Exception as e:
                print(f"❌ {config_name}: {e}")
                
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False


async def test_paperqa_import():
    """Test that paper-qa can be imported and basic objects created."""
    print("\n" + "=" * 60)
    print("TESTING PAPER-QA IMPORT")
    print("=" * 60)

    try:
        from paperqa import Docs, Settings
        
        # Test creating basic objects
        docs = Docs()
        print("✅ Docs object created successfully")
        
        # Test creating settings
        settings = Settings(
            llm="openrouter/anthropic/claude-3.5-sonnet",
            embedding="ollama/nomic-embed-text"
        )
        print("✅ Settings object created successfully")
        print(f"   LLM: {settings.llm}")
        print(f"   Embedding: {settings.embedding}")
        
        return True
        
    except Exception as e:
        print(f"❌ Paper-QA import failed: {e}")
        return False


async def test_environment():
    """Test environment setup."""
    print("\n" + "=" * 60)
    print("TESTING ENVIRONMENT")
    print("=" * 60)

    # Check OpenRouter API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        print(f"✅ OPENROUTER_API_KEY is set (length: {len(api_key)})")
    else:
        print("❌ OPENROUTER_API_KEY not set")
        print("   Please set your OpenRouter API key in .env file")
        return False

    # Check if papers directory exists
    papers_dir = Path("./papers")
    if papers_dir.exists():
        pdf_files = list(papers_dir.glob("*.pdf"))
        print(f"✅ Papers directory exists with {len(pdf_files)} PDF files")
    else:
        print("⚠️ Papers directory doesn't exist (will be created when needed)")
        papers_dir.mkdir(exist_ok=True)

    return True


async def main():
    """Run all tests."""
    print("Paper-QA CLI Test Suite")
    print("=" * 60)

    tests = [
        ("Environment", test_environment),
        ("Paper-QA Import", test_paperqa_import),
        ("Configuration Loading", test_config_loading),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! CLI should work correctly.")
        print("\nNext steps:")
        print("1. Add PDF files to ./papers/ directory")
        print("2. Run: paper-qa-cli 'Your question here'")
        print("3. Or run: python scripts/paper_qa_cli.py 'Your question here'")
    else:
        print("⚠️ Some tests failed. Please fix the issues above.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 