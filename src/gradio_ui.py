"""
Gradio UI for Paper-QA
Provides a web interface for querying papers and public sources.
"""

import asyncio
import logging
import queue
import time
from typing import Optional

import gradio as gr

from paper_qa_core import PaperQACore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global core instance
paper_qa_core: Optional[PaperQACore] = None

# Status update queue
status_queue = queue.Queue()


def initialize_core(config_name: str = "default") -> PaperQACore:
    """Initialize the Paper-QA core with the specified configuration."""
    global paper_qa_core
    if paper_qa_core is None or paper_qa_core.config_name != config_name:
        paper_qa_core = PaperQACore(config_name=config_name)
    return paper_qa_core


async def query_papers(
    question: str,
    method: str,
    config_name: str,
    paper_directory: str,
    max_sources: int = 10,
) -> tuple[str, str, str, str]:
    """
    Query papers using the specified method.

    Returns:
        tuple: (answer, sources_info, status)
    """
    if not question.strip():
        return "", "", "❌ Please enter a question.", "Ready to query..."

    try:
        # Add initial status update
        add_status_update(f"🔍 Starting {method} query...")

        # Initialize core
        add_status_update("⚙️ Initializing Paper-QA core...")
        core = initialize_core(config_name)

        # Set up callbacks for streaming
        answer_parts = []

        def stream_callback(text: str):
            answer_parts.append(text)

        callbacks = [stream_callback] if method in ["local", "combined"] else None

        # Execute query based on method
        if method == "local":
            add_status_update("📚 Loading local papers...")
            result = await core.query_local_papers(
                question,
                paper_directory=paper_directory if paper_directory else None,
                callbacks=callbacks,
            )
        elif method == "public":
            add_status_update(
                "🌐 Searching public sources (Semantic Scholar, Crossref, etc.)..."
            )
            add_status_update("🔍 Querying Semantic Scholar database...")
            add_status_update("📄 Searching for relevant papers...")
            result = await core.query_public_sources(question)
        elif method == "combined":
            add_status_update("🔄 Searching both local and public sources...")
            result = await core.query_combined(
                question,
                paper_directory=paper_directory if paper_directory else None,
                callbacks=callbacks,
            )
        elif method == "semantic_scholar":
            add_status_update("🔍 Direct Semantic Scholar API search...")
            result = await core.query_semantic_scholar_api(question)
        else:
            return "", "", f"❌ Unknown method: {method}"

        # Process results
        add_status_update("📝 Processing results and generating answer...")
        add_status_update("🤖 Generating AI response...")
        if result["success"]:
            answer = result["answer"]
            sources_count = result["sources"]
            sources_info = f"📚 Found {sources_count} sources"

            # Check if answer is meaningful
            if answer.strip() == "I cannot answer." or answer.strip() == "":
                status = "⚠️ Query completed but no relevant information found. Try rephrasing your question or using a different method."
                add_status_update("⚠️ No relevant information found")
                return (
                    "No relevant information found. Try:\n• Rephrasing your question\n• Using 'combined' method instead of 'public'\n• Adding more specific terms",
                    sources_info,
                    status,
                    get_status_updates(),
                )

                # Truncate answer if too long
            if len(answer) > 5000:
                answer = answer[:5000] + "\n\n... (truncated for display)"

            add_status_update(f"✅ Success! Found {sources_count} sources")
            add_status_update(f"📄 Generated {len(answer)} character answer")
            add_status_update("🎉 Query completed successfully!")
            status = f"✅ Query completed successfully using {method} method"
            return answer, sources_info, status, get_status_updates()
        else:
            error_msg = result.get("error", "Unknown error")
            add_status_update(f"❌ Query failed: {error_msg}")
            if "rate limit" in error_msg.lower():
                add_status_update(
                    "💡 Tip: Consider getting a Semantic Scholar API key for higher rate limits"
                )
            return "", "", f"❌ Query failed: {error_msg}", get_status_updates()

    except Exception as e:
        logger.error(f"Error in query_papers: {e}")
        add_status_update(f"❌ Error: {str(e)}")
        return "", "", f"❌ Error: {str(e)}", get_status_updates()


def query_papers_sync(
    question: str,
    method: str,
    config_name: str,
    paper_directory: str,
    max_sources: int = 10,
) -> tuple[str, str, str, str]:
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
        return "", "", f"❌ Error: {str(e)}"


def get_status_updates() -> str:
    """
    Get current status updates for display in the UI.
    """
    try:
        # Get all available status updates
        updates = []
        while not status_queue.empty():
            try:
                update = status_queue.get_nowait()
                updates.append(update)
            except queue.Empty:
                break

        if updates:
            # Show last 8 updates for better visibility
            recent_updates = updates[-8:] if len(updates) > 8 else updates
            return "\n".join(recent_updates)
        else:
            return "Ready to query...\n\n💡 Tip: Enter a question and click 'Ask Question' to start"
    except Exception as e:
        return f"Status error: {str(e)}"


def add_status_update(message: str):
    """
    Add a status update to the queue.
    """
    try:
        timestamp = time.strftime("%H:%M:%S")
        # Add emoji and better formatting
        formatted_message = f"[{timestamp}] {message}"
        status_queue.put(formatted_message)

        # Also log to console for debugging
        print(f"📊 Status: {formatted_message}")
    except Exception as e:
        logger.error(f"Error adding status update: {e}")


def create_ui():
    """Create the Gradio interface."""

    # Custom CSS for better styling
    css = """
    .gradio-container {
        max-width: 1200px !important;
        margin: auto !important;
    }
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .status-box {
        background-color: #f0f0f0;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    """

    with gr.Blocks(css=css, title="Paper-QA Web Interface") as demo:
        # Header
        gr.HTML(
            """
        <div class="main-header">
            <h1>📚 Paper-QA Web Interface</h1>
            <p>Ask questions about your research papers and get AI-powered answers with citations</p>
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
                # Status and info
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
                    """
                    )

        # Output section
        with gr.Group():
            gr.Markdown("### 📝 Answer")
            answer_output = gr.Textbox(
                label="Answer", lines=10, max_lines=20, interactive=False
            )

            with gr.Row():
                sources_output = gr.Textbox(label="Sources", interactive=False)

                status_output = gr.Textbox(label="Status", interactive=False)

            # Real-time status updates
            with gr.Group():
                gr.Markdown("### 🔄 Real-time Status")
                with gr.Row():
                    status_updates_output = gr.Textbox(
                        label="Query Progress",
                        lines=5,
                        max_lines=10,
                        interactive=False,
                        value="Ready to query...\n\n💡 Tip: Enter a question and click 'Ask Question' to start",
                    )
                    refresh_status_btn = gr.Button("🔄 Refresh Status", size="sm")

        # Footer
        gr.HTML(
            """
        <div style="text-align: center; margin-top: 2rem; color: #666;">
            <p>Powered by Paper-QA with OpenRouter.ai and Ollama</p>
            <p>Built with Gradio</p>
        </div>
        """
        )

        # Event handlers
        query_btn.click(
            fn=query_papers,
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
                status_updates_output,
            ],
        )

        # Enter key support
        question_input.submit(
            fn=query_papers,
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
                status_updates_output,
            ],
        )

        # Manual refresh button for status updates
        def update_status():
            return get_status_updates()

        refresh_status_btn.click(
            fn=update_status,
            inputs=[],
            outputs=status_updates_output,
        )

    return demo


def main():
    """Main function to launch the Gradio interface."""
    print("🚀 Starting Paper-QA Gradio Interface...")

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
