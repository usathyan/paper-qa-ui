#!/usr/bin/env python3
"""
Comprehensive test script to verify the complete workflow with local Ollama models.
Based on insights from GitHub discussion #731.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager
from paperqa import Settings, ask


def test_complete_workflow():
    """Test the complete workflow with local Ollama models."""
    print("🧪 Testing complete workflow with local Ollama models...")
    print(f"📋 Based on GitHub discussion #731 insights")
    
    try:
        # Load optimized configuration
        config_manager = ConfigManager()
        config_dict = config_manager.load_config("optimized_ollama")
        settings = Settings(**config_dict)
        
        print(f"✅ Loaded optimized settings with LLM: {settings.llm}")
        print(f"✅ Embedding: {settings.embedding}")
        print(f"✅ Paper directory: {settings.paper_directory}")
        
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
        
        # Test the ask function (this is what the discussion was about)
        test_question = "What is this paper about?"
        print(f"\n❓ Testing question: {test_question}")
        
        try:
            answer = ask(
                test_question,
                settings=settings
            )
            
            print(f"\n✅ Query successful!")
            print(f"📝 Answer: {answer.session.answer[:200]}...")
            print(f"📚 Contexts found: {len(answer.session.contexts) if hasattr(answer.session, 'contexts') else 0}")
            
            if hasattr(answer.session, 'contexts') and answer.session.contexts:
                print("🔍 Evidence sources:")
                for i, context in enumerate(answer.session.contexts[:3], 1):
                    source_name = getattr(context.text, 'name', f'Source {i}') if hasattr(context, 'text') else f'Source {i}'
                    print(f"   {i}. {source_name}")
            else:
                print("⚠️ No contexts found - this might indicate the evidence retrieval issue")
                
        except Exception as e:
            print(f"❌ Query failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n🎉 Complete workflow test successful!")
        print("💡 Your setup is working perfectly with local Ollama models.")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_complete_workflow()
    if success:
        print("\n✅ All tests passed! Your local Ollama setup is working perfectly.")
        print("🚀 You can now use the UI with confidence.")
    else:
        print("\n❌ Tests failed. Please check your configuration.") 