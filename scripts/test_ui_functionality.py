#!/usr/bin/env python3
"""
Test script to verify UI functionality.
"""

import requests
import time
import sys
from pathlib import Path

def test_ui_accessibility():
    """Test if the UI is accessible and responding."""
    print("🧪 Testing UI accessibility...")
    
    try:
        # Test if server is responding
        response = requests.get("http://localhost:7860", timeout=10)
        if response.status_code == 200:
            print("✅ UI is accessible and responding")
            print(f"📄 Response size: {len(response.text)} characters")
            return True
        else:
            print(f"❌ UI returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to UI server")
        print("💡 Make sure the server is running with: make ui")
        return False
    except Exception as e:
        print(f"❌ Error testing UI: {e}")
        return False

def test_ui_health():
    """Test UI health endpoint if available."""
    print("\n🧪 Testing UI health...")
    
    try:
        # Try to access the health endpoint
        response = requests.get("http://localhost:7860/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint responding")
        else:
            print(f"⚠️ Health endpoint returned: {response.status_code}")
    except:
        print("⚠️ Health endpoint not available (this is normal)")

def main():
    """Main test function."""
    print("🚀 Paper-QA UI Functionality Test")
    print("=" * 40)
    
    # Test basic accessibility
    if not test_ui_accessibility():
        print("\n❌ UI is not accessible. Please check:")
        print("   1. Is the server running? (make ui)")
        print("   2. Is port 7860 available? (make kill-server)")
        print("   3. Are there any error messages?")
        return False
    
    # Test health
    test_ui_health()
    
    print("\n🎉 UI is working correctly!")
    print("🌐 Access the UI at: http://localhost:7860")
    print("📱 You can now:")
    print("   - Upload PDF documents")
    print("   - Ask questions about the documents")
    print("   - View answers with evidence sources")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 