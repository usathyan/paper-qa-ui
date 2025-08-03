#!/usr/bin/env python3
"""
Simple runner for Semantic Scholar API test
"""

import sys
import os

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_semantic_search import test_picalm_alzheimers_search, test_specific_paper_search

if __name__ == "__main__":
    print("🧪 Running Semantic Scholar API Test")
    print("=" * 50)
    
    try:
        # Run the basic test
        test_picalm_alzheimers_search()
        
        # Run the specific test
        test_specific_paper_search()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc() 