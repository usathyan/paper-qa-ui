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
    print(f"🔍 DEBUG: initialize_core called with config_name: {config_name}")
    print(
        f"🔍 DEBUG: Current paper_qa_core config: {getattr(paper_qa_core, 'config_name', 'None') if paper_qa_core else 'None'}"
    )

    if paper_qa_core is None or paper_qa_core.config_name != config_name:
        print(f"🔍 DEBUG: Creating new PaperQACore with config: {config_name}")
        paper_qa_core = PaperQACore(config_name=config_name)
    else:
        print(f"🔍 DEBUG: Reusing existing PaperQACore with config: {config_name}")

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


def extract_detailed_info(
    result: dict, thinking_summary: dict, config_name: str
) -> tuple:
    """Extract detailed information from query results."""

    # Search statistics
    total_papers = result.get("agent_metadata", {}).get("session_papers_searched", 0)
    evidence_count = len(result.get("detailed_contexts", []))

    # Calculate average relevance score
    contexts = result.get("detailed_contexts", [])
    if contexts:
        avg_relevance = sum(ctx.get("score", 0) for ctx in contexts) / len(contexts)
        relevance_scores = f"{avg_relevance:.2f}/10"
    else:
        relevance_scores = "N/A"

    # Agent performance
    agent_steps = thinking_summary.get("total_steps", 0)
    tool_calls = thinking_summary.get("total_tool_calls", 0)
    processing_time = "N/A"  # Could be calculated if we track start/end times

    # Top sources
    top_sources = []
    for i, ctx in enumerate(contexts[:5], 1):
        citation = ctx.get("citation", "Unknown")
        score = ctx.get("score", 0)
        top_sources.append(f"{i}. {citation} (Score: {score:.2f})")
    top_sources_text = "\n".join(top_sources) if top_sources else "No sources found"

    # Configuration used
    config_used = f"Configuration: {config_name}\n"
    config_used += f"Evidence K: {result.get('agent_metadata', {}).get('agent_evidence_n', 'N/A')}\n"
    config_used += (
        f"Search Count: {result.get('agent_metadata', {}).get('search_count', 'N/A')}\n"
    )
    config_used += f"Max Sources: {result.get('agent_metadata', {}).get('answer_max_sources', 'N/A')}"

    return (
        str(total_papers),
        str(evidence_count),
        relevance_scores,
        str(agent_steps),
        str(tool_calls),
        processing_time,
        top_sources_text,
        config_used,
    )


async def query_papers(
    question: str,
    method: str,
    config_name: str,
    paper_directory: str,
    max_sources: int = 10,
) -> tuple[str, str, str, str, str, str, str, str, str, str, str, str]:
    """
    Query papers using the specified method.

    Returns:
        tuple: (answer, sources_info, status, total_papers, evidence_count, relevance_scores,
                agent_steps, tool_calls, processing_time, top_sources, config_used)
    """
    if not question.strip():
        return "", "", "❌ Please enter a question.", "", "", "", "", "", "", "", ""

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
                detailed_info = extract_detailed_info(
                    result, result.get("thinking_process", {}), config_name
                )
                return (
                    "**No relevant information found.**\n\nTry:\n• Rephrasing your question\n• Using 'combined' method instead of 'public'\n• Adding more specific terms",
                    sources_info,
                    status,
                    *detailed_info,
                )

            # Truncate answer if too long
            if len(answer) > 5000:
                answer = answer[:5000] + "\n\n... (truncated for display)"

            # Format answer for markdown display
            formatted_answer = answer
            if len(formatted_answer) > 10000:
                formatted_answer = (
                    formatted_answer[:10000] + "\n\n... *(truncated for display)*"
                )

            status = f"✅ Query completed successfully using {method} method"
            detailed_info = extract_detailed_info(
                result, result.get("thinking_process", {}), config_name
            )
            return formatted_answer, sources_info, status, *detailed_info
        else:
            error_msg = result.get("error", "Unknown error")
            return (
                "",
                "",
                f"❌ Query failed: {error_msg}",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            )

    except Exception as e:
        logger.error(f"Error in query_papers: {e}")
        return "", "", f"❌ Error: {str(e)}", "", "", "", "", "", "", "", ""


def query_papers_sync(
    question: str,
    method: str,
    config_name: str,
    paper_directory: str,
    max_sources: int = 10,
) -> tuple[str, str, str, str, str, str, str, str, str, str, str, str]:
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
    .response-box {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #e9ecef;
        margin: 1rem 0;
        font-size: 16px;
        line-height: 1.6;
    }
    .response-box h1, .response-box h2, .response-box h3 {
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .response-box p {
        margin-bottom: 1rem;
    }
    .response-box ul, .response-box ol {
        margin-bottom: 1rem;
        padding-left: 2rem;
    }
    .response-box li {
        margin-bottom: 0.5rem;
    }
    .response-box strong {
        color: #2c3e50;
        font-weight: 600;
    }
    .response-box em {
        color: #6c757d;
        font-style: italic;
    }
    .info-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #007bff;
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
                                "agent_optimized",
                                "comprehensive",
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
                    - **Agent Optimized**: Enhanced agent tool calling with Claude 3.5 Sonnet
                    - **Comprehensive**: Maximum information retrieval with all features enabled
                    
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
            gr.Markdown("### 📝 Response")
            answer_output = gr.Markdown(
                label="Answer",
                value="Ask a question to get started...",
                elem_classes=["response-box"],
            )

            with gr.Row():
                sources_output = gr.Textbox(
                    label="Sources Found", interactive=False, scale=1
                )
                status_output = gr.Textbox(label="Status", interactive=False, scale=1)

        # Detailed Information Section (Collapsible)
        with gr.Accordion("🔍 Detailed Information", open=False):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📊 Search Statistics")
                    total_papers_output = gr.Textbox(
                        label="Total Papers Searched", interactive=False
                    )
                    evidence_count_output = gr.Textbox(
                        label="Evidence Pieces Retrieved", interactive=False
                    )
                    relevance_scores_output = gr.Textbox(
                        label="Average Relevance Score", interactive=False
                    )

                with gr.Column():
                    gr.Markdown("### 🤖 Agent Performance")
                    agent_steps_output = gr.Textbox(
                        label="Agent Steps", interactive=False
                    )
                    tool_calls_output = gr.Textbox(
                        label="Tool Calls Made", interactive=False
                    )
                    processing_time_output = gr.Textbox(
                        label="Processing Time", interactive=False
                    )

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 📚 Top Sources")
                    top_sources_output = gr.Textbox(
                        label="Most Relevant Sources",
                        lines=8,
                        max_lines=15,
                        interactive=False,
                    )

                with gr.Column():
                    gr.Markdown("### ⚙️ Configuration Used")
                    config_used_output = gr.Textbox(
                        label="Active Configuration",
                        lines=8,
                        max_lines=15,
                        interactive=False,
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
                total_papers_output,
                evidence_count_output,
                relevance_scores_output,
                agent_steps_output,
                tool_calls_output,
                processing_time_output,
                top_sources_output,
                config_used_output,
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
                total_papers_output,
                evidence_count_output,
                relevance_scores_output,
                agent_steps_output,
                tool_calls_output,
                processing_time_output,
                top_sources_output,
                config_used_output,
            ],
        )

    return demo


def create_ui():
    """Create the Gradio UI with enhanced features."""
    
    with gr.Blocks(
        title="Paper-QA Enhanced Interface",
        css="""
        .response-box {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
        }
        .status-box {
            background-color: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 6px;
            padding: 12px;
            margin: 8px 0;
        }
        """
    ) as demo:
        gr.Markdown("# 📚 Paper-QA Enhanced Interface")
        gr.Markdown("Query scientific papers and clinical trials with advanced AI capabilities")
        
        with gr.Tabs():
            # Query Papers Tab
            with gr.Tab("🔍 Query Papers"):
                with gr.Row():
                    with gr.Column(scale=2):
                        question_input = gr.Textbox(
                            label="Question",
                            placeholder="Enter your research question here...",
                            lines=3
                        )
                        
                        with gr.Row():
                            method_dropdown = gr.Dropdown(
                                choices=[
                                    "public", 
                                    "local", 
                                    "combined", 
                                    "semantic_scholar",
                                    "clinical_trials",
                                    "clinical_trials_only"
                                ],
                                value="public",
                                label="Search Method",
                                info="Choose how to search for information"
                            )
                            
                            config_dropdown = gr.Dropdown(
                                choices=[
                                    "default", 
                                    "agent_optimized", 
                                    "comprehensive",
                                    "clinical_trials",
                                    "clinical_trials_only"
                                ],
                                value="default",
                                label="Configuration",
                                info="Choose the AI configuration"
                            )
                        
                        paper_dir_input = gr.Textbox(
                            label="Paper Directory (for local/combined)",
                            placeholder="./papers",
                            visible=False
                        )
                        
                        with gr.Row():
                            query_btn = gr.Button("🔍 Query Papers", variant="primary")
                            clear_btn = gr.Button("🗑️ Clear", variant="secondary")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 📋 Quick Examples")
                        example_questions = [
                            "What are the latest treatments for Alzheimer's disease?",
                            "How does PICALM affect amyloid beta clearance?",
                            "What clinical trials exist for ulcerative colitis?",
                            "What are the genetic risk factors for Parkinson's disease?"
                        ]
                        
                        for i, example in enumerate(example_questions):
                            gr.Button(
                                example,
                                size="sm",
                                variant="outline"
                            ).click(
                                fn=lambda q=example: q,
                                outputs=question_input
                            )
                
                with gr.Row():
                    with gr.Column(scale=2):
                        answer_output = gr.Markdown(
                            label="Answer",
                            elem_classes=["response-box"]
                        )
                        
                        sources_output = gr.Markdown(
                            label="Sources",
                            elem_classes=["response-box"]
                        )
                    
                    with gr.Column(scale=1):
                        status_output = gr.Markdown(
                            label="Status",
                            elem_classes=["status-box"]
                        )
                        
                        refresh_status_btn = gr.Button("🔄 Refresh Status", size="sm")
                
                # Event handlers
                def on_method_change(method):
                    return gr.update(visible=method in ["local", "combined"])
                
                method_dropdown.change(
                    fn=on_method_change,
                    inputs=[method_dropdown],
                    outputs=[paper_dir_input]
                )
                
                def query_papers(question, method, config, paper_dir):
                    if not question.strip():
                        return "Please enter a question.", "", "No question provided."
                    
                    try:
                        # Import here to avoid circular imports
                        from src.paper_qa_core import PaperQACore
                        
                        async def run_query():
                            core = PaperQACore(config)
                            
                            if method == "local":
                                if not paper_dir:
                                    return "❌ Error: Paper directory required for local queries", "", "Error: Missing paper directory"
                                result = await core.query_local_papers(question, paper_dir)
                            elif method == "public":
                                result = await core.query_public_sources(question)
                            elif method == "combined":
                                result = await core.query_combined(question, paper_dir)
                            elif method == "semantic_scholar":
                                result = await core.query_semantic_scholar_api(question)
                            elif method == "clinical_trials":
                                result = await core.query_clinical_trials(question)
                            elif method == "clinical_trials_only":
                                result = await core.query_clinical_trials_only(question)
                            else:
                                return f"❌ Error: Unknown method {method}", "", f"Error: Invalid method {method}"
                            
                            if result.get("error"):
                                return f"❌ Error: {result['error']}", "", f"Error: {result['error']}"
                            
                            # Format sources
                            sources_info = ""
                            if result.get("agent_metadata"):
                                metadata = result["agent_metadata"]
                                sources_info = f"""
### 📊 Search Results
- **Papers Searched:** {metadata.get('papers_searched', 0)}
- **Evidence Retrieved:** {metadata.get('evidence_count', 0)}
- **Agent Steps:** {metadata.get('agent_steps', 0)}
- **Tool Calls:** {metadata.get('tool_calls', 0)}
- **Method Used:** {result.get('method', 'Unknown')}
                                """
                            
                            status = f"✅ Query completed using {method} method with {config} configuration"
                            
                            return result.get('answer', 'No answer generated'), sources_info, status
                        
                        return asyncio.run(run_query())
                        
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        return error_msg, "", f"Error: {str(e)}"
                
                query_btn.click(
                    fn=query_papers,
                    inputs=[question_input, method_dropdown, config_dropdown, paper_dir_input],
                    outputs=[answer_output, sources_output, status_output]
                )
                
                clear_btn.click(
                    fn=lambda: ("", "", ""),
                    outputs=[answer_output, sources_output, status_output]
                )
                
                # Example button handlers
                for i, example in enumerate(example_questions):
                    gr.Button(
                        example,
                        size="sm",
                        variant="outline"
                    ).click(
                        fn=lambda q=example: (q, "public", "default", ""),
                        outputs=[question_input, method_dropdown, config_dropdown, paper_dir_input]
                    )
            
            # Configure Tab
            with gr.Tab("⚙️ Configure"):
                from src.config_ui import create_config_ui
                config_ui = create_config_ui()
        
        # Footer
        gr.Markdown("---")
        gr.Markdown("""
        ### 🆕 New Features
        - **Clinical Trials Search**: Query clinicaltrials.gov for medical research
        - **Multiple Search Methods**: Public papers, local files, combined, and clinical trials
        - **Advanced Configuration**: Customize AI behavior and search parameters
        - **Real-time Status**: Monitor agent progress and tool usage
        
        ### 📚 Documentation
        - [User Manual](docs/user_manual.md) - Complete usage guide
        - [Developer Guide](DEVELOPER.md) - Technical details
        - [Architecture](Architecture.md) - System design
        """)
    
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
