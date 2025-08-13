"""
Simple Paper-QA Test
Tests basic Paper-QA functionality without complex configuration.
"""

import asyncio

# Add src to path
# use package imports from src


async def test_paper_qa_import() -> bool:
    """Test if we can import paper-qa."""
    print("\n" + "=" * 60)
    print("TESTING PAPER-QA IMPORT")
    print("=" * 60)

    try:
        # Try to import paper-qa
        import paperqa

        print("✅ paperqa imported successfully")

        # Check what's available
        print(
            f"Available modules: {[attr for attr in dir(paperqa) if not attr.startswith('_')]}"
        )

        return True

    except Exception as e:
        print(f"❌ paperqa import failed: {e}")
        return False


async def test_basic_paper_qa_functionality() -> bool:
    """Test basic Paper-QA functionality."""
    print("\n" + "=" * 60)
    print("TESTING BASIC PAPER-QA FUNCTIONALITY")
    print("=" * 60)

    try:
        from paperqa import Docs, Settings

        # Create a simple settings object
        settings = Settings(
            llm="openrouter/google/gemini-2.5-flash-lite",
            embedding="ollama/nomic-embed-text",
            verbosity=1,
        )

        print("✅ Settings created successfully")
        print(f"   LLM: {settings.llm}")
        print(f"   Embedding: {settings.embedding}")

        # Create a Docs object
        _ = Docs()  # Test creation without using the variable
        print("✅ Docs object created successfully")

        return True

    except Exception as e:
        print(f"❌ Basic Paper-QA functionality failed: {e}")
        return False


async def main() -> bool:
    """Run all tests."""
    print("Paper-QA Simple Import Test")
    print("=" * 60)

    tests = [
        ("Paper-QA Import", test_paper_qa_import),
        ("Basic Functionality", test_basic_paper_qa_functionality),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All Paper-QA tests passed!")
    else:
        print("⚠️ Some tests failed.")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
