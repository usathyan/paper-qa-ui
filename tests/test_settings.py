"""
Test paper-qa Settings
"""

import asyncio

# Add src to path
# use package imports from src

from paperqa import Settings


async def test_settings():
    """Test Settings creation."""
    print("Testing paper-qa Settings...")

    try:
        # Try creating settings directly
        settings = Settings(
            llm="openrouter/google/gemini-2.5-flash-lite",
            embedding="ollama/nomic-embed-text",
            verbosity=1,
        )
        print("✅ Created Settings directly")
        print(f"   LLM: {settings.llm}")
        print(f"   Embedding: {settings.embedding}")

        # Try from_name with different approaches
        try:
            Settings.from_name("default")
            print("✅ Created Settings.from_name('default')")
        except Exception as e:
            print(f"❌ Settings.from_name('default') failed: {e}")

        try:
            Settings.from_name("configs/default.json")
            print("✅ Created Settings.from_name('configs/default')")
        except Exception as e:
            print(f"❌ Settings.from_name('configs/default') failed: {e}")

        try:
            Settings.from_name("configs/default.json")
            print("✅ Created Settings.from_name('configs/default.json')")
        except Exception as e:
            print(f"❌ Settings.from_name('configs/default.json') failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False


async def main():
    """Run the test."""
    await test_settings()


if __name__ == "__main__":
    asyncio.run(main())
