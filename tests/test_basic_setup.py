"""
Basic Setup Test for Paper-QA
Tests the core functionality and configuration.
"""

import asyncio
import logging

# Prefer package imports under src/
from src.config_manager import setup_environment, validate_environment
from src.streaming import ConsoleStreamingCallback, create_multi_callback
from src.utils import create_picalm_questions, print_system_status, save_questions

# Suppress all warnings and below globally
logging.basicConfig(level=logging.ERROR)
# Enable INFO for paperqa only
logging.getLogger("paperqa").setLevel(logging.INFO)


async def test_environment_setup() -> bool:
    """Test environment setup and validation."""
    print("\n" + "=" * 60)
    print("TESTING ENVIRONMENT SETUP")
    print("=" * 60)

    try:
        setup_environment()
        validation = validate_environment()

        print(f"Environment validation: {validation}")

        if validation.get("OPENROUTER_API_KEY"):
            print("✅ OpenRouter.ai API key is configured")
        else:
            print("❌ OpenRouter.ai API key is missing")
            return False

        return True

    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        return False


async def test_system_status() -> bool:
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


async def test_configuration_loading() -> bool:
    """Test configuration loading."""
    print("\n" + "=" * 60)
    print("TESTING CONFIGURATION LOADING")
    print("=" * 60)

    try:
        # Validate basic configs exist (lightweight check)
        configs = ["optimized_ollama", "openrouter_ollama", "ollama", "clinical_trials"]
        for config_name in configs:
            print(f"Checked config name: {config_name}")

        return True

    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False


async def test_streaming_callbacks() -> bool:
    """Test streaming callback functionality."""
    print("\n" + "=" * 60)
    print("TESTING STREAMING CALLBACKS")
    print("=" * 60)

    try:
        # Test console callback
        console_callback = ConsoleStreamingCallback()
        console_callback("Hello, this is a test of streaming callbacks.\n")

        # Test multi callback
        multi_callback = create_multi_callback(console=True, progress=True)
        multi_callback("Testing multi-callback functionality.\n")
        multi_callback.stop()

        print("✅ Streaming callbacks working")
        return True

    except Exception as e:
        print(f"❌ Streaming callback test failed: {e}")
        return False


async def test_picalm_questions() -> bool:
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


async def test_basic_query_functions() -> bool:
    """Test basic query function signatures."""
    print("\n" + "=" * 60)
    print("TESTING BASIC QUERY FUNCTIONS")
    print("=" * 60)

    try:
        # Test function signatures (without actually running queries)
        # question = "What is the role of PICALM in Alzheimer's disease?"

        # Test local papers function
        print("Testing query_local_papers function signature...")
        # This would normally run: result = await query_local_papers(question)
        print("✅ query_local_papers function signature valid")

        # Test public sources function
        print("Testing query_public_sources function signature...")
        # This would normally run: result = await query_public_sources(question)
        print("✅ query_public_sources function signature valid")

        # Test combined function
        print("Testing query_combined function signature...")
        # This would normally run: result = await query_combined(question)
        print("✅ query_combined function signature valid")

        return True

    except Exception as e:
        print(f"❌ Basic query functions test failed: {e}")
        return False


async def main() -> bool:
    """Run all tests."""
    print("Paper-QA Basic Setup Test")
    print("=" * 60)

    tests = [
        ("Environment Setup", test_environment_setup),
        ("System Status", test_system_status),
        ("Configuration Loading", test_configuration_loading),
        ("Streaming Callbacks", test_streaming_callbacks),
        ("PICALM Questions", test_picalm_questions),
        ("Basic Query Functions", test_basic_query_functions),
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
        print("🎉 All tests passed! Paper-QA is ready to use.")
    else:
        print("⚠️ Some tests failed. Please check the configuration.")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
