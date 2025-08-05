#!/usr/bin/env python3
"""
Test script to verify the optimized configuration loads correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager
from paperqa import Settings


def test_optimized_config():
    """Test that the optimized configuration loads correctly."""
    print("🧪 Testing optimized configuration for UI...")
    try:
        config_manager = ConfigManager()
        config_dict = config_manager.load_config("optimized_ollama")
        settings = Settings(**config_dict)
        
        print(f"✅ Loaded optimized settings with LLM: {settings.llm}")
        print(f"✅ Embedding: {settings.embedding}")
        print(f"✅ Evidence K: {settings.answer.evidence_k}")
        print(f"✅ Answer Max Sources: {settings.answer.answer_max_sources}")
        print(f"✅ Max Concurrent Requests: {settings.answer.max_concurrent_requests}")
        print(f"✅ Use JSON: {settings.prompts.use_json}")
        
        print(f"✅ LLM Config API Base: {settings.llm_config.get('api_base', 'Not found')}")
        print(f"✅ Embedding Config API Base: {settings.embedding_config.get('api_base', 'Not found')}")
        
        print("\n🎉 Optimized configuration is ready for use!")
        print("💡 You can now select 'optimized_ollama' in the UI configuration dropdown.")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_optimized_config()
    if success:
        print("\n✅ All tests passed! The optimized configuration is ready.")
    else:
        print("\n❌ Tests failed. Please check the configuration.") 