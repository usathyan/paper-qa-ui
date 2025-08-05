#!/usr/bin/env python3
"""
Test script to verify UI query functionality
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

async def test_ui_query():
    """Test the UI query functionality."""
    try:
        from paperqa2_ui import initialize_settings, process_question_async, app_state
        
        print("🧪 Testing UI query functionality...")
        
        # Test 1: Initialize settings
        print("\n1. Initializing settings...")
        settings = initialize_settings("openrouter_ollama")
        print(f"✅ Settings initialized: {settings.llm}")
        
        # Test 2: Check if papers exist and simulate upload
        print("\n2. Checking papers directory and simulating upload...")
        papers_dir = Path("./papers")
        if papers_dir.exists():
            pdf_files = list(papers_dir.glob("*.pdf"))
            print(f"✅ Found {len(pdf_files)} PDF files")
            
            # Simulate document upload by adding to app_state
            app_state["uploaded_docs"] = []
            for pdf in pdf_files:
                doc_info = {
                    "filename": pdf.name,
                    "size": pdf.stat().st_size,
                    "status": "Processed",
                    "path": str(pdf)
                }
                app_state["uploaded_docs"].append(doc_info)
                print(f"   - Added {pdf.name} to uploaded docs")
        else:
            print("❌ No papers directory found")
            return False
        
        # Test 3: Test a simple query
        print("\n3. Testing query...")
        try:
            answer_html, sources_html, metadata_html, error = await process_question_async(
                "What is this paper about?",
                "openrouter_ollama"
            )
            
            if error:
                print(f"❌ Query failed: {error}")
                return False
            
            print(f"✅ Query completed successfully!")
            print(f"✅ Answer length: {len(answer_html)} characters")
            print(f"✅ Sources length: {len(sources_html)} characters")
            print(f"✅ Metadata length: {len(metadata_html)} characters")
            
            # Show a preview of the answer
            if answer_html:
                preview = answer_html[:200].replace('<', '&lt;').replace('>', '&gt;')
                print(f"✅ Answer preview: {preview}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Query failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing UI query functionality...")
    
    success = asyncio.run(test_ui_query())
    
    if success:
        print("\n✅ UI query test passed!")
        print("🎉 The UI is working correctly with the new agent_query approach.")
    else:
        print("\n❌ UI query test failed.")
        print("💡 Check the error messages above for details.")
    
    sys.exit(0 if success else 1) 