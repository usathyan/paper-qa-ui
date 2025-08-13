"""
Test configuration loading
"""

import asyncio

# Add src to path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config_manager import ConfigManager


async def test_config_loading() -> bool:
    """Test configuration loading."""
    print("Testing configuration loading...")

    try:
        config_manager = ConfigManager()

        # List available configs
        configs = config_manager.list_configs()
        print(f"Available configs: {configs}")

        # Try to load each config
        for config_name in configs:
            try:
                config = config_manager.load_config(config_name)
                print(f"✅ Loaded config: {config_name}")
                print(f"   LLM: {config.get('llm')}")
                print(f"   Embedding: {config.get('embedding')}")
            except Exception as e:
                print(f"❌ Failed to load config {config_name}: {e}")

        return True

    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


async def main() -> None:
    """Run the test."""
    await test_config_loading()


if __name__ == "__main__":
    asyncio.run(main())
