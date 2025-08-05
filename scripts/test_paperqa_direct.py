#!/usr/bin/env python3
"""
Direct test of paper-qa with correct configuration
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

async def test_paperqa_direct():
    """Test paper-qa directly with correct configuration."""
    try:
        from paperqa import Docs, Settings
        
        print("Creating Settings with OpenRouter and Ollama...")
        settings = Settings(
            llm="openrouter/anthropic/claude-3.5-sonnet",
            summary_llm="openrouter/anthropic/claude-3.5-sonnet",
            embedding="ollama/nomic-embed-text",
            llm_config={
                "api_base": "https://openrouter.ai/api/v1"
            },
            embedding_config={
                "api_base": "http://localhost:11434"
            },
            temperature=0,
            verbosity=3
        )
        
        print(f"Settings created: LLM={settings.llm}, Embedding={settings.embedding}")
        
        print("Creating Docs...")
        docs = Docs()
        
        # Add a simple text file for testing
        test_file = Path("test.txt")
        test_file.write_text("This is a test document about artificial intelligence and machine learning.")
        
        print("Adding test document...")
        await docs.aadd(test_file, citation="Test Document")
        
        print("Querying...")
        result = await docs.aquery("What is this document about?", settings=settings)
        
        print(f"✅ Paper-QA test successful!")
        print(f"Answer: {result.answer}")
        
        # Clean up
        test_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Paper-QA test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_paperqa_direct())
    sys.exit(0 if success else 1) 