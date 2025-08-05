#!/usr/bin/env python3
"""
Test script to verify file upload functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from paperqa2_ui import process_uploaded_files_async


async def test_file_upload():
    """Test the file upload functionality."""
    print("🧪 Testing file upload functionality...")
    
    # Check if we have any PDF files to test with
    papers_dir = Path("./papers")
    if not papers_dir.exists():
        print("❌ No papers directory found. Please add some PDF files to ./papers/")
        return False
    
    pdf_files = list(papers_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ No PDF files found in ./papers/. Please add some documents first.")
        return False
    
    print(f"📚 Found {len(pdf_files)} PDF files for testing")
    
    # Test with the first PDF file
    test_file = str(pdf_files[0])
    print(f"📄 Testing with: {Path(test_file).name}")
    
    try:
        # Test the upload function
        result = await process_uploaded_files_async([test_file])
        
        print(f"✅ Upload test completed!")
        print(f"📝 Result: {result[0]}")
        print(f"📝 Status: {result[1]}")
        
        if "Successfully processed" in result[1]:
            print("🎉 File upload functionality is working correctly!")
            return True
        else:
            print("❌ File upload failed")
            return False
            
    except Exception as e:
        print(f"❌ File upload test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_file_upload())
    if success:
        print("\n✅ File upload functionality is working!")
    else:
        print("\n❌ File upload functionality has issues.")
        sys.exit(1) 