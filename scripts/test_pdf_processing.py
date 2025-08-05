#!/usr/bin/env python3
"""
Test PDF processing and basic paper-qa functionality
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

async def test_pdf_processing():
    """Test basic PDF processing."""
    try:
        from paperqa import Docs, Settings
        
        print("Testing PDF processing...")
        
        # Create basic settings
        settings = Settings(
            llm="openrouter/google/gemini-2.5-flash-lite",
            embedding="ollama/nomic-embed-text",
            embedding_config={
                "api_base": "http://localhost:11434"
            }
        )
        
        print(f"Settings created: LLM={settings.llm}, Embedding={settings.embedding}")
        
        # Create Docs object
        docs = Docs()
        
        # Check if PDF exists
        pdf_file = Path("./papers/2507.21046v3.pdf")
        if not pdf_file.exists():
            print(f"❌ PDF file not found: {pdf_file}")
            return False
            
        print(f"✅ PDF file found: {pdf_file}")
        print(f"   Size: {pdf_file.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Try to add the PDF
        print("Adding PDF to Docs...")
        await docs.aadd(pdf_file, citation="Test Paper")
        
        print("✅ PDF added successfully!")
        
        # Check if docs has any content
        print(f"Number of documents: {len(docs.docs) if hasattr(docs, 'docs') else 'Unknown'}")
        
        # Try a simple query
        print("Testing simple query...")
        result = await docs.aquery("What is the title of this paper?", settings=settings)
        
        print(f"✅ Query completed!")
        print(f"Answer: {result.answer}")
        
        if result.sources:
            print(f"Sources: {len(result.sources)}")
            for i, source in enumerate(result.sources, 1):
                print(f"  {i}. {source.citation}")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_pdf_processing())
    sys.exit(0 if success else 1) 