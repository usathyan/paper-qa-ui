#!/usr/bin/env python3
"""
Paper-QA CLI Script
Simple command-line interface for testing Paper-QA functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import asyncio
import logging

from config_manager import setup_environment
from paper_qa_core import query_combined, query_local_papers, query_public_sources
from streaming import ConsoleStreamingCallback
from utils import create_picalm_questions, print_system_status

# Suppress all warnings and below globally
logging.basicConfig(level=logging.ERROR)
# Enable INFO for paperqa only
logging.getLogger("paperqa").setLevel(logging.INFO)


async def run_query(
    question: str, method: str, paper_dir: str = None, config: str = "default"
):
    """Run a query using the specified method."""
    print(f"\nQuerying: {question}")
    print(f"Method: {method}")
    print(f"Configuration: {config}")
    print("-" * 60)

    # Create streaming callback
    callback = ConsoleStreamingCallback()

    start_time = asyncio.get_event_loop().time()

    try:
        if method == "local":
            result = await query_local_papers(
                question,
                paper_directory=paper_dir,
                config_name=config,
                callbacks=[callback],
            )
        elif method == "public":
            result = await query_public_sources(
                question, config_name=config, callbacks=[callback]
            )
        elif method == "combined":
            result = await query_combined(
                question,
                paper_directory=paper_dir,
                config_name=config,
                callbacks=[callback],
            )
        else:
            print(f"Unknown method: {method}")
            return None

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        print("\n" + "=" * 60)
        print("QUERY RESULTS")
        print("=" * 60)
        print(f"Method: {result.get('method', 'Unknown')}")
        print(f"Success: {result.get('success', False)}")
        print(f"Sources: {result.get('sources', 0)}")
        print(f"Duration: {duration:.2f}s")
        print(f"Answer Length: {len(result.get('answer', ''))} characters")

        if result.get("error"):
            print(f"Error: {result['error']}")

        return result

    except Exception as e:
        print(f"\n❌ Query failed: {e}")
        return None


async def run_picalm_demo():
    """Run PICALM demo with all three questions."""
    print("\n" + "=" * 60)
    print("PICALM AND ALZHEIMER'S DISEASE DEMO")
    print("=" * 60)

    questions = create_picalm_questions()
    results = []

    for question_data in questions:
        question_id = question_data["id"]
        question = question_data["question"]

        print(f"\nQuestion {question_id}: {question}")

        # Test all three methods
        config_map = {
            "local": "local_only",
            "public": "public_only",
            "combined": "combined",
        }
        for method in ["local", "public", "combined"]:
            config = config_map[method]
            result = await run_query(question, method, config=config)
            if result:
                result["question_id"] = question_id
                result["question"] = question
                results.append(result)

        print("\n" + "-" * 60)

    # Save results
    if results:
        from utils import save_results

        save_results(results, "results/picalm_demo")
        print(f"\n✅ Saved {len(results)} results to results/picalm_demo/")


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Paper-QA CLI")
    parser.add_argument("--question", "-q", help="Question to ask")
    parser.add_argument(
        "--method",
        "-m",
        choices=["local", "public", "combined"],
        default="combined",
        help="Query method",
    )
    parser.add_argument("--paper-dir", "-p", help="Paper directory for local queries")
    parser.add_argument(
        "--config", "-c", default="default", help="Configuration to use"
    )
    parser.add_argument("--demo", action="store_true", help="Run PICALM demo")
    parser.add_argument("--status", action="store_true", help="Check system status")
    parser.add_argument("--setup", action="store_true", help="Setup environment")

    args = parser.parse_args()

    try:
        # Setup environment
        if args.setup:
            print("Setting up environment...")
            setup_environment()
            print("✅ Environment setup complete")
            return

        # Check status
        if args.status:
            print_system_status()
            return

        # Run demo
        if args.demo:
            await run_picalm_demo()
            return

        # Run single query
        if args.question:
            await run_query(args.question, args.method, args.paper_dir, args.config)
        else:
            print(
                "Please provide a question with --question or run --demo for PICALM demo"
            )
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
