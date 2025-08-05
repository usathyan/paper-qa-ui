#!/usr/bin/env python3
"""
Simple test script for paper-qa with Ollama
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

async def test_simple():
    """Test simple paper-qa functionality with Ollama."""
    try:
        from paperqa import Docs, Settings
        
        print("Creating Settings...")
        settings = Settings(
            llm="ollama/llama3.2:latest",
            embedding="ollama/nomic-embed-text:latest",
            llm_config={
                "api_base": "http://localhost:11434",
                "api_type": "ollama"
            },
            embedding_config={
                "api_base": "http://localhost:11434",
                "dimensions": 768
            }
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
        
        print(f"Answer: {result.answer}")
        
        # Clean up
        test_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple())
    sys.exit(0 if success else 1) 