"""
Simple Test for Paper-QA
Basic functionality test without complex dependencies.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import create_picalm_questions, print_system_status, save_questions


async def test_picalm_questions():
    """Test PICALM questions creation."""
    print("\n" + "=" * 60)
    print("TESTING PICALM QUESTIONS")
    print("=" * 60)

    try:
        questions = create_picalm_questions()

        print(f"Created {len(questions)} PICALM questions:")
        for q in questions:
            print(f"  - {q['id']}: {q['question']}")

        # Save questions to file
        save_questions(questions, "tests/picalm_questions.json")
        print("✅ Questions saved to tests/picalm_questions.json")

        return True

    except Exception as e:
        print(f"❌ PICALM questions test failed: {e}")
        return False


async def test_system_status():
    """Test system status checks."""
    print("\n" + "=" * 60)
    print("TESTING SYSTEM STATUS")
    print("=" * 60)

    try:
        print_system_status()
        return True

    except Exception as e:
        print(f"❌ System status check failed: {e}")
        return False


async def test_basic_imports():
    """Test basic imports."""
    print("\n" + "=" * 60)
    print("TESTING BASIC IMPORTS")
    print("=" * 60)

    try:
        # Test basic imports
        from streaming import ConsoleStreamingCallback

        print("✅ ConsoleStreamingCallback imported successfully")

        print("✅ Utility functions imported successfully")

        # Test streaming callback
        callback = ConsoleStreamingCallback()
        callback("Test message")
        print("✅ Streaming callback working")

        return True

    except Exception as e:
        print(f"❌ Basic imports test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("Paper-QA Simple Test")
    print("=" * 60)

    tests = [
        ("Basic Imports", test_basic_imports),
        ("PICALM Questions", test_picalm_questions),
        ("System Status", test_system_status),
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
        print("🎉 All basic tests passed!")
    else:
        print("⚠️ Some tests failed.")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
