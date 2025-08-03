"""
Gradio UI for Paper-QA
Provides a web interface for querying papers and public sources.
Enhanced to display detailed agent thinking processes and context information.
"""

import asyncio
import logging
from typing import Optional

import gradio as gr

from config_ui import create_config_ui
from paper_qa_core import PaperQACore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global core instance
paper_qa_core: Optional[PaperQACore] = None


def initialize_core(config_name: str = "default") -> PaperQACore:
    """Initialize the Paper-QA core with the specified configuration."""
    global paper_qa_core
    if paper_qa_core is None or paper_qa_core.config_name != config_name:
        paper_qa_core = PaperQACore(config_name=config_name)
    return paper_qa_core


def format_thinking_process(thinking_data: dict) -> str:
    """Format thinking process data for display."""
    if not thinking_data:
        return "No thinking process data available."

    formatted = []

    # Agent steps
    if thinking_data.get("agent_steps"):
        formatted.append("🤖 **Agent Steps:**")
        for step in thinking_data["agent_steps"]:
            formatted.append(
                f"  {step['step']}. [{step['timestamp']}] {step['action']}"
            )
        formatted.append("")

    # Tool calls
    if thinking_data.get("tool_calls"):
        formatted.append("🔧 **Tool Calls:**")
        for tool in thinking_data["tool_calls"]:
            formatted.append(
                f"  • {tool['type']} [{tool['timestamp']}]: {tool['details']}"
            )
        formatted.append("")

    # Context details
    if thinking_data.get("context_details"):
        formatted.append("📊 **Context Updates:**")
        for detail in thinking_data["context_details"]:
            formatted.append(f"  • [{detail['timestamp']}] {detail['details']}")
        formatted.append("")

    # Summary
    total_steps = thinking_data.get("total_steps", 0)
    total_tools = thinking_data.get("total_tool_calls", 0)
    formatted.append(f"📈 **Summary:** {total_steps} steps, {total_tools} tool calls")

    return "\n".join(formatted)


def format_detailed_contexts(contexts: list) -> str:
    """Format detailed context information for display."""
    if not contexts:
        return "No context information available."

    formatted = []
    formatted.append("📚 **Detailed Context Information:**")

    for i, context in enumerate(contexts, 1):
        formatted.append(f"\n**Context {i}:**")
        formatted.append(f"  • **Citation:** {context.get('citation', 'Unknown')}")
        formatted.append(f"  • **Score:** {context.get('score', 0.0):.2f}")

        if context.get("paper_info"):
            paper = context["paper_info"]
            formatted.append(f"  • **Paper:** {paper.get('title', 'Unknown')}")
            formatted.append(f"  • **Authors:** {', '.join(paper.get('authors', []))}")
            formatted.append(f"  • **Year:** {paper.get('year', 'Unknown')}")
            if paper.get("doi"):
                formatted.append(f"  • **DOI:** {paper['doi']}")

        # Truncate text for display
        text = context.get("text", "")
        if len(text) > 300:
            text = text[:300] + "..."
        formatted.append(f"  • **Text:** {text}")

    return "\n".join(formatted)


def format_agent_metadata(metadata: dict) -> str:
    """Format agent metadata for display."""
    if not metadata:
        return "No agent metadata available."

    formatted = []
    formatted.append("⚙️ **Agent Configuration:**")

    # Basic agent info
    formatted.append(f"  • **Agent Type:** {metadata.get('agent_type', 'Unknown')}")
    formatted.append(f"  • **Search Count:** {metadata.get('search_count', 0)}")
    formatted.append(f"  • **Evidence Count:** {metadata.get('agent_evidence_n', 0)}")
    formatted.append(f"  • **Timeout:** {metadata.get('timeout', 0)}s")

    # Session info if available
    if metadata.get("session_id"):
        formatted.append(f"  • **Session ID:** {metadata['session_id']}")
        formatted.append(
            f"  • **Session Status:** {metadata.get('session_status', 'Unknown')}"
        )
        formatted.append(
            f"  • **Session Cost:** ${metadata.get('session_cost', 0.0):.4f}"
        )
        formatted.append(f"  • **Session Steps:** {metadata.get('session_steps', 0)}")
        formatted.append(
            f"  • **Tools Used:** {', '.join(metadata.get('session_tools_used', []))}"
        )
        formatted.append(
            f"  • **Papers Searched:** {metadata.get('session_papers_searched', 0)}"
        )

    return "\n".join(formatted)


async def query_papers(
    question: str,
    method: str,
    config_name: str,
    paper_directory: str,
    max_sources: int = 10,
) -> tuple[str, str, str, str, str, str]:
    """
    Query papers using the specified method.

    Returns:
        tuple: (answer, sources_info, status, thinking_process, detailed_contexts, agent_metadata)
    """
    if not question.strip():
        return "", "", "❌ Please enter a question.", "Ready to query...", "", ""

    try:
        # Initialize core
        core = initialize_core(config_name)

        # Execute query based on method
        if method == "local":
            result = await core.query_local_papers(
                question,
                paper_directory=paper_directory if paper_directory else None,
            )
        elif method == "public":
            result = await core.query_public_sources(question)
        elif method == "combined":
            result = await core.query_combined(
                question,
                paper_directory=paper_directory if paper_directory else None,
            )
        elif method == "semantic_scholar":
            result = await core.query_semantic_scholar_api(question)
        else:
            return "", "", f"❌ Unknown method: {method}", "", "", ""

        # Process results
        if result["success"]:
            answer = result["answer"]
            sources_count = result["sources"]
            sources_info = f"📚 Found {sources_count} sources"

            # Check if answer is meaningful
            if answer.strip() == "I cannot answer." or answer.strip() == "":
                status = "⚠️ Query completed but no relevant information found. Try rephrasing your question or using a different method."
                return (
                    "No relevant information found. Try:\n• Rephrasing your question\n• Using 'combined' method instead of 'public'\n• Adding more specific terms",
                    sources_info,
                    status,
                    "No thinking process data available.",
                    "No context information available.",
                    "No agent metadata available.",
                )

            # Truncate answer if too long
            if len(answer) > 5000:
                answer = answer[:5000] + "\n\n... (truncated for display)"

            # Format detailed information
            thinking_process = format_thinking_process(
                result.get("thinking_process", {})
            )
            detailed_contexts = format_detailed_contexts(
                result.get("detailed_contexts", [])
            )
            agent_metadata = format_agent_metadata(result.get("agent_metadata", {}))

            status = f"✅ Query completed successfully using {method} method"
            return (
                answer,
                sources_info,
                status,
                thinking_process,
                detailed_contexts,
                agent_metadata,
            )
        else:
            error_msg = result.get("error", "Unknown error")
            return "", "", f"❌ Query failed: {error_msg}", "", "", ""

    except Exception as e:
        logger.error(f"Error in query_papers: {e}")
        return "", "", f"❌ Error: {str(e)}", "", "", ""


def query_papers_sync(
    question: str,
    method: str,
    config_name: str,
    paper_directory: str,
    max_sources: int = 10,
) -> tuple[str, str, str, str, str, str]:
    """
    Synchronous wrapper for query_papers to work with Gradio.
    """
    try:
        # Check if there's already an event loop running
        try:
            asyncio.get_running_loop()
            # If we're in an event loop, we need to create a new task
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    query_papers(
                        question, method, config_name, paper_directory, max_sources
                    ),
                )
                return future.result()
        except RuntimeError:
            # No event loop running, we can use asyncio.run
            return asyncio.run(
                query_papers(
                    question, method, config_name, paper_directory, max_sources
                )
            )
    except Exception as e:
        logger.error(f"Error in query_papers_sync: {e}")
        return "", "", f"❌ Error: {str(e)}", "", "", ""


def create_query_ui() -> gr.Blocks:
    """Create the main query interface."""

    # Custom CSS for better styling
    css = """
    .gradio-container {
        max-width: 1400px !important;
        margin: auto !important;
    }
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #007bff;
    }
    .thinking-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #ffc107;
    }
    .context-box {
        background-color: #d1ecf1;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #17a2b8;
    }
    .metadata-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #28a745;
    }
    """

    with gr.Blocks(css=css, title="Paper-QA Enhanced Web Interface") as demo:
        # Header
        gr.HTML(
            """
        <div class="main-header">
            <h1>📚 Paper-QA Enhanced Web Interface</h1>
            <p>Ask questions about your research papers and get AI-powered answers with detailed agent thinking processes</p>
        </div>
        """
        )

        with gr.Row():
            with gr.Column(scale=2):
                # Input section
                with gr.Group():
                    gr.Markdown("### 🔍 Ask Your Question")
                    question_input = gr.Textbox(
                        label="Question",
                        placeholder="e.g., What are the main findings of this research?",
                        lines=3,
                        max_lines=5,
                    )

                with gr.Row():
                    with gr.Column():
                        method_dropdown = gr.Dropdown(
                            choices=["local", "public", "combined", "semantic_scholar"],
                            value="public",
                            label="Search Method",
                            info="public: Semantic Scholar & Crossref | local: Your PDFs | combined: Both | semantic_scholar: Direct API search",
                        )

                    with gr.Column():
                        config_dropdown = gr.Dropdown(
                            choices=[
                                "default",
                                "local_only",
                                "public_only",
                                "combined",
                            ],
                            value="default",
                            label="Configuration",
                            info="Different settings for different use cases",
                        )

                with gr.Row():
                    with gr.Column():
                        paper_dir_input = gr.Textbox(
                            label="Papers Directory (optional)",
                            placeholder="./papers",
                            info="Path to your PDF papers directory",
                        )

                    with gr.Column():
                        max_sources_input = gr.Number(
                            label="Max Sources",
                            value=10,
                            minimum=1,
                            maximum=50,
                            info="Maximum number of sources to include",
                        )

                query_btn = gr.Button("🔍 Ask Question", variant="primary", size="lg")

            with gr.Column(scale=1):
                # Information section
                with gr.Group():
                    gr.Markdown("### ℹ️ Information")
                    gr.Markdown(
                        """
                    **Query Methods:**
                    - **Local**: Search only your uploaded PDF papers
                    - **Public**: Search online sources (Semantic Scholar, Crossref, etc.)
                    - **Combined**: Search both local and public sources
                    
                    **Configurations:**
                    - **Default**: Balanced settings for general use
                    - **Local Only**: Optimized for local papers
                    - **Public Only**: Optimized for online sources
                    - **Combined**: Optimized for mixed sources
                    
                    **💡 Tips for Better Results:**
                    - Be specific in your questions
                    - Use scientific terminology
                    - Try different query methods if one doesn't work
                    - For broad topics, use "combined" method
                    
                    **🔍 Enhanced Features:**
                    - View agent thinking processes
                    - See detailed context information
                    - Monitor tool calls and steps
                    - Track agent metadata
                    """
                    )

        # Output section
        with gr.Group():
            gr.Markdown("### 📝 Answer")
            answer_output = gr.Textbox(
                label="Answer", lines=8, max_lines=15, interactive=False
            )

            with gr.Row():
                sources_output = gr.Textbox(label="Sources", interactive=False)
                status_output = gr.Textbox(label="Status", interactive=False)

        # Enhanced information sections
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🤖 Agent Thinking Process")
                thinking_output = gr.Textbox(
                    label="Agent Steps & Tool Calls",
                    lines=12,
                    max_lines=20,
                    interactive=False,
                    value="Ready to display agent thinking process...",
                )

            with gr.Column():
                gr.Markdown("### 📚 Detailed Contexts")
                contexts_output = gr.Textbox(
                    label="Context Information",
                    lines=12,
                    max_lines=20,
                    interactive=False,
                    value="Ready to display detailed context information...",
                )

        with gr.Row():
            gr.Markdown("### ⚙️ Agent Metadata")
            metadata_output = gr.Textbox(
                label="Agent Configuration & Session Info",
                lines=8,
                max_lines=15,
                interactive=False,
                value="Ready to display agent metadata...",
            )

        # Event handlers
        query_btn.click(
            fn=query_papers_sync,
            inputs=[
                question_input,
                method_dropdown,
                config_dropdown,
                paper_dir_input,
                max_sources_input,
            ],
            outputs=[
                answer_output,
                sources_output,
                status_output,
                thinking_output,
                contexts_output,
                metadata_output,
            ],
        )

        # Enter key support
        question_input.submit(
            fn=query_papers_sync,
            inputs=[
                question_input,
                method_dropdown,
                config_dropdown,
                paper_dir_input,
                max_sources_input,
            ],
            outputs=[
                answer_output,
                sources_output,
                status_output,
                thinking_output,
                contexts_output,
                metadata_output,
            ],
        )

    return demo


def create_ui():
    """Create the complete Gradio interface with tabs."""

    with gr.Blocks(title="Paper-QA Enhanced Web Interface") as demo:
        # Create tabs
        with gr.Tabs():
            # Query tab
            with gr.TabItem("🔍 Query Papers", id=0):
                create_query_ui()

            # Configuration tab
            with gr.TabItem("⚙️ Configure", id=1):
                create_config_ui()

        # Footer
        gr.HTML(
            """
        <div style="text-align: center; margin-top: 2rem; color: #666;">
            <p>Powered by Paper-QA with OpenRouter.ai and Ollama</p>
            <p>Enhanced with detailed agent thinking processes and configuration management</p>
        </div>
        """
        )

    return demo


def main():
    """Main function to launch the Gradio interface."""
    print("🚀 Starting Paper-QA Enhanced Gradio Interface...")

    # Create and launch the interface
    demo = create_ui()

    # Launch with appropriate settings
    demo.launch(
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860,  # Default Gradio port
        share=False,  # Don't create public link by default
        show_error=True,  # Show detailed errors
        quiet=False,  # Show startup messages
    )


if __name__ == "__main__":
    main()
