"""
Paper-QA Core Functions
Provides three main query functions: local papers, public sources, and combined.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from typing import Any, Callable, Dict, List, Optional, Union

from paperqa import Docs
from paperqa.agents import agent_query
from tenacity import retry, stop_after_attempt, wait_exponential

# Suppress all warnings and below globally
logging.basicConfig(level=logging.ERROR)
# Enable DEBUG for paperqa only
logging.getLogger("paperqa").setLevel(logging.DEBUG)


class PaperQACore:
    """Core Paper-QA functionality with streaming and error handling."""

    def __init__(self, config_name: str = "default"):
        """Initialize Paper-QA core with configuration."""
        self.config_name = config_name

        # Use config manager to load settings
        from config_manager import ConfigManager

        config_manager = ConfigManager()
        self.settings = config_manager.get_settings(config_name)

        self.docs: Optional[Docs] = None

    async def initialize_docs(
        self, paper_directory: Optional[Union[str, Path]] = None
    ) -> None:
        """Initialize Docs object with local papers."""
        if paper_directory:
            self.settings.agent.index.paper_directory = paper_directory

        self.docs = Docs()

        # Add papers from directory if it exists
        paper_dir = Path(self.settings.agent.index.paper_directory)
        if paper_dir.exists() and paper_dir.is_dir():
            for pdf_file in paper_dir.rglob("*.pdf"):
                print(f"Adding paper: {pdf_file.name}")
                await self.docs.aadd(pdf_file, settings=self.settings)

        print(f"Loaded {len(self.docs.docs)} papers")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def query_local_papers(
        self,
        question: str,
        paper_directory: Optional[Union[str, Path]] = None,
        callbacks: Optional[List[Callable[[str], None]]] = None,
    ) -> Dict[str, Any]:
        """
        Query local papers only.

        Args:
            question: The question to ask
            paper_directory: Directory containing papers
            callbacks: List of callback functions for streaming

        Returns:
            Dictionary containing answer and metadata
        """
        if not self.docs:
            await self.initialize_docs(paper_directory)

        print(f"Querying local papers: {question}")

        try:
            result = await self.docs.aquery(
                question, settings=self.settings, callbacks=callbacks
            )

            return {
                "answer": result.answer,
                "contexts": result.contexts,
                "sources": len(result.contexts) if result.contexts else 0,
                "method": "local_papers",
                "success": True,
            }

        except Exception as e:
            print(f"Error querying local papers: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "contexts": [],
                "sources": 0,
                "method": "local_papers",
                "success": False,
                "error": str(e),
            }

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def query_public_sources(
        self, question: str, callbacks: Optional[List[Callable[[str], None]]] = None
    ) -> Dict[str, Any]:
        """
        Query public sources using agent system.

        Args:
            question: The question to ask
            callbacks: List of callback functions for streaming

        Returns:
            Dictionary containing answer and metadata
        """
        print(f"Querying public sources: {question}")

        try:
            result = await agent_query(question, self.settings)

            return {
                "answer": result.session.answer,
                "contexts": result.session.contexts,
                "sources": (
                    len(result.session.contexts) if result.session.contexts else 0
                ),
                "method": "public_sources",
                "success": True,
            }

        except Exception as e:
            print(f"Error querying public sources: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "contexts": [],
                "sources": 0,
                "method": "public_sources",
                "success": False,
                "error": str(e),
            }

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def query_combined(
        self,
        question: str,
        paper_directory: Optional[Union[str, Path]] = None,
        callbacks: Optional[List[Callable[[str], None]]] = None,
    ) -> Dict[str, Any]:
        """
        Query both local papers and public sources.

        Args:
            question: The question to ask
            paper_directory: Directory containing papers
            callbacks: List of callback functions for streaming

        Returns:
            Dictionary containing answer and metadata
        """
        print(f"Querying combined sources: {question}")

        # First try local papers
        local_result = await self.query_local_papers(
            question, paper_directory, callbacks
        )

        # Then try public sources
        public_result = await self.query_public_sources(question, callbacks)

        # Combine results
        combined_answer = f"Local Papers Answer:\n{local_result['answer']}\n\n"
        combined_answer += f"Public Sources Answer:\n{public_result['answer']}"

        combined_contexts = []
        if local_result.get("contexts"):
            combined_contexts.extend(local_result["contexts"])
        if public_result.get("contexts"):
            combined_contexts.extend(public_result["contexts"])

        return {
            "answer": combined_answer,
            "contexts": combined_contexts,
            "sources": len(combined_contexts),
            "method": "combined",
            "success": local_result["success"] or public_result["success"],
            "local_result": local_result,
            "public_result": public_result,
        }


# Convenience functions
async def query_local_papers(
    question: str,
    paper_directory: Optional[Union[str, Path]] = None,
    config_name: str = "local_only",
    callbacks: Optional[List[Callable[[str], None]]] = None,
) -> Dict[str, Any]:
    """Query local papers only."""
    core = PaperQACore(config_name)
    return await core.query_local_papers(question, paper_directory, callbacks)


async def query_public_sources(
    question: str,
    config_name: str = "public_only",
    callbacks: Optional[List[Callable[[str], None]]] = None,
) -> Dict[str, Any]:
    """Query public sources only."""
    core = PaperQACore(config_name)
    return await core.query_public_sources(question, callbacks)


async def query_combined(
    question: str,
    paper_directory: Optional[Union[str, Path]] = None,
    config_name: str = "combined",
    callbacks: Optional[List[Callable[[str], None]]] = None,
) -> Dict[str, Any]:
    """Query both local papers and public sources."""
    core = PaperQACore(config_name)
    return await core.query_combined(question, paper_directory, callbacks)
