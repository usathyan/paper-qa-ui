#!/usr/bin/env python3
"""
Test script to verify Docs.query() works correctly for evidence retrieval.
This addresses the GitHub issue #868 where agent_query() doesn't find evidence from index.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from paperqa import Settings, Docs
from config_manager import ConfigManager


async def test_docs_query():
    """Test Docs.query() approach for evidence retrieval."""
    print("🧪 Testing Docs.query() approach...")
    
    # Load configuration
    config_manager = ConfigManager()
    config_dict = config_manager.load_config("openrouter_ollama")
    settings = Settings(**config_dict)
    
    print(f"✅ Loaded settings with LLM: {settings.llm}")
    print(f"✅ Embedding: {settings.embedding}")
    
    # Create Docs object - use the correct approach
    docs = Docs(
        llm=settings.llm,
        llm_config=settings.llm_config,
        embedding=settings.embedding,
        embedding_config=settings.embedding_config,
        temperature=settings.temperature,
        answer=settings.answer,
        parsing=settings.parsing,
        prompts=settings.prompts
    )
    
    # Check if we have any papers
    papers_dir = Path("./papers")
    if not papers_dir.exists():
        print("❌ No papers directory found. Please add some PDF files to ./papers/")
        return
    
    pdf_files = list(papers_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in ./papers/. Please add some documents first.")
        return
    
    print(f"📚 Found {len(pdf_files)} PDF files")
    
    # Add documents to Docs
    for pdf_file in pdf_files:
        print(f"📄 Adding {pdf_file.name}...")
        await docs.aadd(pdf_file)
    
    # Test query
    test_question = "What is this paper about?"
    print(f"\n❓ Testing question: {test_question}")
    
    try:
        response = await docs.aquery(test_question)
        
        print(f"\n✅ Query successful!")
        print(f"📝 Answer: {response.answer[:200]}...")
        print(f"📚 Contexts found: {len(response.contexts) if hasattr(response, 'contexts') else 0}")
        
        if hasattr(response, 'contexts') and response.contexts:
            print("🔍 Evidence sources:")
            for i, context in enumerate(response.contexts[:3], 1):
                source_name = getattr(context.text, 'name', f'Source {i}') if hasattr(context, 'text') else f'Source {i}'
                print(f"   {i}. {source_name}")
        else:
            print("⚠️ No contexts found - this might indicate the evidence retrieval issue")
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_docs_query()) 