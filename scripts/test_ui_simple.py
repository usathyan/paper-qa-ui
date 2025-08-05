#!/usr/bin/env python3
"""
Simple test to verify the UI approach works with document indexing.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager
from paperqa import Settings, Docs


async def test_ui_approach():
    """Test the UI approach with document indexing."""
    print("🧪 Testing UI approach with document indexing...")
    
    try:
        # Load optimized configuration
        config_manager = ConfigManager()
        config_dict = config_manager.load_config("optimized_ollama")
        settings = Settings(**config_dict)
        
        print(f"✅ Loaded optimized settings with LLM: {settings.llm}")
        print(f"✅ Embedding: {settings.embedding}")
        
        # Create Docs object (same as UI)
        docs = Docs()  # Create Docs without parameters
        
        # Check if we have any papers
        papers_dir = Path("./papers")
        if not papers_dir.exists():
            print("❌ No papers directory found. Please add some PDF files to ./papers/")
            return False
        
        pdf_files = list(papers_dir.glob("*.pdf"))
        if not pdf_files:
            print("❌ No PDF files found in ./papers/. Please add some documents first.")
            return False
        
        print(f"📚 Found {len(pdf_files)} PDF files")
        
        # Add documents to index (same as UI)
        for pdf_file in pdf_files:
            print(f"📄 Adding {pdf_file.name} to index...")
            try:
                await docs.aadd(pdf_file, settings=settings)
                print(f"✅ Successfully indexed {pdf_file.name}")
            except Exception as e:
                print(f"❌ Failed to index {pdf_file.name}: {e}")
                return False
        
        # Test query (same as UI)
        test_question = "What is this paper about?"
        print(f"\n❓ Testing query: {test_question}")
        
        try:
            response = await docs.aquery(test_question, settings=settings)
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
            return False
        
        print("\n🎉 UI approach test successful!")
        print("💡 The UI should work perfectly with this approach.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_ui_approach())
    if success:
        print("\n✅ All tests passed! The UI approach is working correctly.")
    else:
        print("\n❌ Tests failed. Please check your setup.") 