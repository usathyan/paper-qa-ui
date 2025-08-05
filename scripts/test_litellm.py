#!/usr/bin/env python3
"""
Test script for LiteLLM with OpenRouter and Ollama
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

async def test_litellm_openrouter():
    """Test LiteLLM with OpenRouter."""
    try:
        from litellm import completion
        
        print("Testing OpenRouter with LiteLLM...")
        
        response = completion(
            model="openrouter/anthropic/claude-3.5-sonnet",
            messages=[{"role": "user", "content": "Hello, how are you?"}],
            api_base="https://openrouter.ai/api/v1"
        )
        
        print(f"✅ OpenRouter test successful!")
        print(f"Response: {response.choices[0].message.content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter test failed: {e}")
        return False

async def test_litellm_ollama():
    """Test LiteLLM with Ollama."""
    try:
        from litellm import completion
        
        print("Testing Ollama with LiteLLM...")
        
        response = completion(
            model="ollama/llama3.2",
            messages=[{"role": "user", "content": "Hello, how are you?"}],
            api_base="http://localhost:11434"
        )
        
        print(f"✅ Ollama test successful!")
        print(f"Response: {response.choices[0].message.content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("LiteLLM Test Suite")
    print("=" * 60)
    
    # Check environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return False
    
    print(f"✅ OPENROUTER_API_KEY is set (length: {len(api_key)})")
    
    tests = [
        ("OpenRouter", test_litellm_openrouter),
        ("Ollama", test_litellm_ollama),
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
        print("🎉 All LiteLLM tests passed!")
    else:
        print("⚠️ Some tests failed.")
    
    return passed == total

if __name__ == "__main__":
    import os
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 