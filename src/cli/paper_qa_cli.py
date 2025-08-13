#!/usr/bin/env python3
"""
Paper-QA CLI Script
Simple command-line interface for testing Paper-QA functionality.
"""

import sys

# running as a module; no manual sys.path modification needed

import argparse
import asyncio
import logging
import json
import os

from dotenv import load_dotenv

load_dotenv()

# Suppress all warnings and below globally
logging.basicConfig(level=logging.ERROR)
# Enable INFO for paperqa only
logging.getLogger("paperqa").setLevel(logging.INFO)


async def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Paper-QA CLI - Query scientific papers with natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query local PDFs
  paper-qa-cli "What is the main finding?" --method local --paper-dir ./papers
  
  # Use different configuration
  paper-qa-cli "Explain the methodology" --config ollama
  
  # Save results to file
  paper-qa-cli "What are the conclusions?" --output results.json
        """,
    )

    parser.add_argument("question", help="Question to ask about papers")

    parser.add_argument(
        "--method",
        "-m",
        choices=["local", "public", "combined"],
        default="local",
        help="Query method (default: local)",
    )

    parser.add_argument(
        "--paper-dir",
        "-p",
        default="./papers",
        help="Paper directory for local queries (default: ./papers)",
    )

    parser.add_argument(
        "--config",
        "-c",
        default="openrouter_ollama",
        help="Configuration to use (default: openrouter_ollama)",
    )

    parser.add_argument("--output", "-o", help="Output file for results (optional)")

    args = parser.parse_args()

    # Check environment
    if (
        not os.getenv("OPENROUTER_API_KEY")
        or os.getenv("OPENROUTER_API_KEY") == "your_openrouter_api_key_here"
    ):
        print("❌ Error: OPENROUTER_API_KEY not properly set in environment")
        print("Please set your OpenRouter API key:")
        print("1. Copy env.template to .env")
        print("2. Edit .env and set OPENROUTER_API_KEY=your_actual_key")
        print("3. Get your key from: https://openrouter.ai/keys")
        return 1

    # Check if paper directory exists for local method
    if args.method == "local" and not os.path.exists(args.paper_dir):
        print(f"❌ Error: Paper directory not found: {args.paper_dir}")
        print(
            "Please create the directory and add PDF files, or specify a different directory with --paper-dir"
        )
        return 1

    try:
        # Fallback: use PaperQACore if available, otherwise skip
        try:
            from ..paperqa2_core import PaperQACore  # type: ignore
        except Exception:
            from ..paper_qa_core import PaperQACore  # type: ignore

        print(f"\nQuerying: {args.question}")
        print(f"Method: {args.method}")
        print(f"Configuration: {args.config}")
        print("-" * 60)

        core = PaperQACore(args.config)

        if args.method == "local":
            result = await core.query_local_papers(args.question, args.paper_dir)
        elif args.method == "public":
            result = await core.query_public_sources(args.question)
        elif args.method == "combined":
            result = await core.query_combined(args.question, args.paper_dir)
        else:
            print(f"❌ Error: Unknown method {args.method}")
            return 1

        # Display results
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
            return 1

        print(f"\n🎯 **Answer:**\n{result.get('answer', 'No answer generated')}")

        if result.get("agent_metadata"):
            metadata = result["agent_metadata"]
            print("\n📊 **Search Statistics**")
            print(f"Total Papers Searched: {metadata.get('papers_searched', 0)}")
            print(f"Evidence Pieces Retrieved: {metadata.get('evidence_count', 0)}")
            print(
                f"Average Relevance Score: {metadata.get('avg_relevance_score', 'N/A')}"
            )

            print("\n🤖 **Agent Performance**")
            print(f"Agent Steps: {metadata.get('agent_steps', 0)}")
            print(f"Tool Calls Made: {metadata.get('tool_calls', 0)}")
            print(f"Processing Time: {metadata.get('processing_time', 'N/A')}")

        # Save to file if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n💾 Results saved to {args.output}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
