#!/usr/bin/env python3
"""
Debug script to understand UI settings initialization issues
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

def debug_settings():
    """Debug the settings initialization process."""
    try:
        from paperqa import Settings
        from paperqa.agents.tools import DEFAULT_TOOL_NAMES
        from config_manager import ConfigManager
        
        print("🔍 Debugging settings initialization...")
        
        # Test 1: Load config dictionary
        print("\n1. Loading config dictionary...")
        config_manager = ConfigManager()
        config_dict = config_manager.load_config("openrouter_ollama")
        
        print(f"✅ Config loaded: {type(config_dict)}")
        print(f"✅ Config keys: {list(config_dict.keys())}")
        
        # Check if agent key exists
        if 'agent' in config_dict:
            print(f"✅ Agent config: {config_dict['agent']}")
        else:
            print("❌ No 'agent' key in config")
        
        # Test 2: Try to create Settings object
        print("\n2. Creating Settings object...")
        try:
            settings = Settings(**config_dict)
            print(f"✅ Settings created: {type(settings)}")
            print(f"✅ Settings LLM: {settings.llm}")
            print(f"✅ Settings embedding: {settings.embedding}")
            
            # Check agent attribute
            if hasattr(settings, 'agent'):
                print(f"✅ Settings has agent: {settings.agent}")
                if hasattr(settings.agent, 'tool_names'):
                    print(f"✅ Agent tool names: {settings.agent.tool_names}")
                else:
                    print("❌ Agent has no tool_names")
            else:
                print("❌ Settings has no agent attribute")
                
        except Exception as e:
            print(f"❌ Failed to create Settings: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 3: Try to modify agent settings
        print("\n3. Testing agent settings modification...")
        try:
            if hasattr(settings, 'agent') and hasattr(settings.agent, 'tool_names'):
                if "clinical_trials_search" not in settings.agent.tool_names:
                    settings.agent.tool_names = DEFAULT_TOOL_NAMES + ["clinical_trials_search"]
                print(f"✅ Agent tool names updated: {settings.agent.tool_names}")
            else:
                from paperqa.settings import AgentSettings
                settings.agent = AgentSettings(tool_names=DEFAULT_TOOL_NAMES + ["clinical_trials_search"])
                print(f"✅ Created new agent settings: {settings.agent.tool_names}")
                
        except Exception as e:
            print(f"❌ Failed to modify agent settings: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_settings()
    sys.exit(0 if success else 1) 