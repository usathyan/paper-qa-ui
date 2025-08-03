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
import json
import logging

from paper_qa_core import query_combined, query_local_papers, query_public_sources
from streaming import ConsoleStreamingCallback
from utils import create_picalm_questions

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
        elif method == "semantic_scholar":
            # Use the core directly for semantic scholar API
            from src.paper_qa_core import PaperQACore

            core = PaperQACore(config)
            result = await core.query_semantic_scholar_api(question)
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
    parser = argparse.ArgumentParser(description="Paper-QA CLI with enhanced features")
    parser.add_argument(
        "question",
        help="Question to ask about papers",
    )
    parser.add_argument(
        "--method",
        "-m",
        choices=[
            "local",
            "public",
            "combined",
            "semantic_scholar",
            "clinical_trials",
            "clinical_trials_only",
        ],
        default="public",
        help="Query method (default: public for best results)",
    )
    parser.add_argument("--paper-dir", "-p", help="Paper directory for local queries")
    parser.add_argument(
        "--config",
        "-c",
        default="default",
        help="Configuration to use (default: default)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for results (optional)",
    )

    args = parser.parse_args()

    from src.paper_qa_core import PaperQACore

    core = PaperQACore(args.config)

    if args.method == "local":
        if not args.paper_dir:
            print("❌ Error: --paper-dir is required for local queries")
            return
        result = await core.query_local_papers(args.question, args.paper_dir)
    elif args.method == "public":
        result = await core.query_public_sources(args.question)
    elif args.method == "combined":
        result = await core.query_combined(args.question, args.paper_dir)
    elif args.method == "semantic_scholar":
        result = await core.query_semantic_scholar_api(args.question)
    elif args.method == "clinical_trials":
        result = await core.query_clinical_trials(args.question)
    elif args.method == "clinical_trials_only":
        result = await core.query_clinical_trials_only(args.question)
    else:
        print(f"❌ Error: Unknown method {args.method}")
        return

    # Display results
    if result.get("error"):
        print(f"❌ Error: {result['error']}")
        return

    print(f"\n🎯 **Answer:**\n{result.get('answer', 'No answer generated')}")

    if result.get("agent_metadata"):
        metadata = result["agent_metadata"]
        print("\n📊 **Search Statistics**")
        print(f"Total Papers Searched: {metadata.get('papers_searched', 0)}")
        print(f"Evidence Pieces Retrieved: {metadata.get('evidence_count', 0)}")
        print(f"Average Relevance Score: {metadata.get('avg_relevance_score', 'N/A')}")

        print("\n🤖 **Agent Performance**")
        print(f"Agent Steps: {metadata.get('agent_steps', 0)}")
        print(f"Tool Calls Made: {metadata.get('tool_calls', 0)}")
        print(f"Processing Time: {metadata.get('processing_time', 'N/A')}")

    # Save to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n💾 Results saved to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
