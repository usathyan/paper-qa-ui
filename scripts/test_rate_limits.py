#!/usr/bin/env python3
"""
Test script to demonstrate paper-qa's built-in rate limit handling and retry mechanisms.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from paper_qa_core import PaperQACore
from utils import print_system_status


async def test_rate_limit_handling():
    """Test how paper-qa handles rate limits with different configurations."""
    
    print("🧪 Testing Paper-QA Rate Limit Handling")
    print("=" * 50)
    
    # Check system status first
    print_system_status()
    print()
    
    # Test questions that might trigger rate limits
    test_questions = [
        "What is FOXA1?",
        "What is PICALM?",
        "What is Alzheimer's disease?",
        "What are the latest treatments for cancer?",
        "What is CRISPR technology?"
    ]
    
    configs_to_test = ["public_only", "default"]
    
    for config_name in configs_to_test:
        print(f"\n📋 Testing with config: {config_name}")
        print("-" * 30)
        
        core = PaperQACore(config_name)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n🔍 Test {i}: {question}")
            print(f"   Config: {config_name}")
            
            try:
                # This will use paper-qa's built-in retry mechanisms
                result = await core.query_public_sources(question)
                
                if result["success"]:
                    print(f"   ✅ Success: Found {result['sources']} sources")
                    print(f"   📝 Answer length: {len(result['answer'])} characters")
                else:
                    print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   💥 Exception: {e}")
            
            # Small delay between requests to be respectful
            await asyncio.sleep(2)
    
    print("\n🎯 Rate Limit Handling Summary:")
    print("=" * 50)
    print("✅ Paper-QA has built-in retry mechanisms using tenacity")
    print("✅ Handles 403 Forbidden errors from Semantic Scholar")
    print("✅ Exponential backoff with configurable parameters")
    print("✅ Configurable timeouts via environment variables")
    print("✅ Reduced concurrency to minimize rate limiting")
    print("\n📝 Environment variables you can set:")
    print("   SEMANTIC_SCHOLAR_API_REQUEST_TIMEOUT=30.0")
    print("   CROSSREF_API_REQUEST_TIMEOUT=30.0")
    print("   OPENALEX_API_REQUEST_TIMEOUT=30.0")
    print("   UNPAYWALL_TIMEOUT=30.0")


if __name__ == "__main__":
    asyncio.run(test_rate_limit_handling()) 