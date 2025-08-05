#!/usr/bin/env python3
"""
Paper-QA Gradio UI with optimized local Ollama support.
Based on insights from GitHub discussions and testing.
"""

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import List, Tuple

import gradio as gr
from paperqa import Settings, Docs
from paperqa.agents.tools import DEFAULT_TOOL_NAMES

from config_manager import ConfigManager

# Configure logging with INFO level for cleaner output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set paper-qa to INFO level and turn off LiteLLM debug
logging.getLogger("paperqa").setLevel(logging.INFO)
logging.getLogger("litellm").setLevel(logging.WARNING)  # Turn off LiteLLM debug
logging.getLogger("httpx").setLevel(logging.WARNING)  # Reduce HTTP noise

# Global state
app_state = {
    "uploaded_docs": [],
    "settings": None,
    "docs": None,
    "status_tracker": None,
    "processing_status": ""
}


class StatusTracker:
    """Simple status tracker for paper-qa operations."""
    
    def __init__(self):
        self.status_updates = []
        self.current_step = 0
    
    def add_status(self, status: str):
        """Add a status update."""
        self.status_updates.append(f"{time.strftime('%H:%M:%S')} - {status}")
        logger.info(f"Status: {status}")
    
    def get_status_html(self) -> str:
        """Get formatted HTML of all status updates."""
        if not self.status_updates:
            return "<div style='text-align: center; color: #666;'>Ready to process questions</div>"
        
        html_parts = ["<div style='max-height: 200px; overflow-y: auto; background: #f8f9fa; padding: 10px; border-radius: 5px;'>"]
        html_parts.append("<strong>Processing Status:</strong><br>")
        for i, status in enumerate(self.status_updates[-10:], 1):  # Show last 10 updates
            html_parts.append(f"{i}. {status}<br>")
        html_parts.append("</div>")
        return "".join(html_parts)
    
    def clear(self):
        """Clear all status updates."""
        self.status_updates = []
        self.current_step = 0


def initialize_settings(config_name: str = "optimized_ollama") -> Settings:
    """Initialize paper-qa settings with the specified configuration."""
    try:
        config_manager = ConfigManager()
        config_dict = config_manager.load_config(config_name)
        settings = Settings(**config_dict)
        
        # Ensure clinical_trials_search is available if using agent
        if hasattr(settings, 'agent') and hasattr(settings.agent, 'tool_names'):
            if "clinical_trials_search" not in settings.agent.tool_names:
                settings.agent.tool_names = DEFAULT_TOOL_NAMES + ["clinical_trials_search"]
        else:
            from paperqa.settings import AgentSettings
            settings.agent = AgentSettings(tool_names=DEFAULT_TOOL_NAMES + ["clinical_trials_search"])
        
        status_tracker = StatusTracker()
        app_state["settings"] = settings
        app_state["status_tracker"] = status_tracker
        logger.info(f"Initialized Settings with config: {config_name}")
        return settings
    except Exception as e:
        logger.error(f"Failed to initialize Settings: {e}")
        raise


async def process_uploaded_files_async(files: List[str]) -> Tuple[str, str]:
    """Process uploaded files by copying them to papers directory and adding to paper-qa index."""
    if not files:
        return "", "No files uploaded."
    
    # Ensure papers directory exists
    papers_dir = Path("./papers")
    papers_dir.mkdir(exist_ok=True)
    
    processed_files = []
    failed_files = []
    
    try:
        # Initialize paper-qa Docs object for indexing
        if not app_state["settings"]:
            app_state["settings"] = initialize_settings()
        
        settings = app_state["settings"]
        docs = Docs()  # Create Docs without parameters
        
        for file_obj in files:
            # Handle Gradio file object - extract the actual file path
            if hasattr(file_obj, 'name'):
                # Newer Gradio versions return file objects with .name attribute
                source_path = Path(file_obj.name)
            else:
                # Fallback for string paths
                source_path = Path(file_obj)
            
            dest_path = papers_dir / source_path.name
            
            try:
                # Check if file is already in the target location
                if source_path.resolve() == dest_path.resolve():
                    # File is already in the target location, skip copying
                    logger.info(f"File {source_path.name} is already in papers directory, skipping copy")
                else:
                    # Copy file to papers directory
                    import shutil
                    if hasattr(file_obj, 'name'):
                        # For file objects, use the object directly
                        shutil.copy2(file_obj.name, dest_path)
                    else:
                        # For string paths, use the path
                        shutil.copy2(source_path, dest_path)
                
                # Add to paper-qa index with settings
                logger.info(f"Adding {source_path.name} to paper-qa index...")
                await docs.aadd(dest_path, settings=settings)
                
                # Update app state
                doc_info = {
                    "filename": source_path.name,
                    "size": dest_path.stat().st_size if dest_path.exists() else 0,
                    "status": "Indexed",
                    "path": str(dest_path)
                }
                app_state["uploaded_docs"].append(doc_info)
                processed_files.append(source_path.name)
                
                logger.info(f"Successfully processed and indexed: {source_path.name}")
                
            except Exception as e:
                logger.error(f"Failed to process {source_path.name}: {e}")
                failed_files.append(f"{source_path.name}: {str(e)}")
        
        # Store the Docs object for later use
        app_state["docs"] = docs
        
        # Prepare status message
        status_msg = f"✅ Successfully processed {len(processed_files)} files"
        if failed_files:
            status_msg += f"\n❌ Failed to process {len(failed_files)} files: {', '.join(failed_files)}"
        
        # Update status tracker
        if "status_tracker" in app_state:
            app_state["status_tracker"].add_status(f"📚 Indexed {len(processed_files)} documents")
        
        return f"Processed: {', '.join(processed_files)}", status_msg
        
    except Exception as e:
        error_msg = f"❌ Processing failed: {str(e)}"
        logger.error(f"Exception in process_uploaded_files: {e}", exc_info=True)
        return "", error_msg


def process_uploaded_files(files: List[str]) -> Tuple[str, str]:
    """Synchronous wrapper for process_uploaded_files_async."""
    return asyncio.run(process_uploaded_files_async(files))


async def process_question_async(question: str, config_name: str = "optimized_ollama") -> Tuple[str, str, str, str]:
    """Process a question using paper-qa with the specified configuration."""
    if not question.strip():
        return "", "", "", "Please enter a question."
    
    if not app_state["uploaded_docs"]:
        return "", "", "", "Please upload documents before asking questions."
    
    start_time = time.time()
    
    try:
        # Initialize settings if needed
        if not app_state["settings"] or config_name != "optimized_ollama":
            app_state["settings"] = initialize_settings(config_name)
        
        if "status_tracker" in app_state:
            app_state["status_tracker"].clear()
            app_state["status_tracker"].add_status("🔍 Initializing and searching documents...")
        
        app_state["processing_status"] = "🔍 Initializing and searching documents..."
        logger.info(f"Processing question: {question}")
        logger.info(f"Using config: {config_name}")
        logger.info(f"Number of uploaded docs: {len(app_state['uploaded_docs'])}")
        
        if "status_tracker" in app_state:
            app_state["status_tracker"].add_status("🤖 Initializing...")
            app_state["status_tracker"].add_status("🔍 Searching documents...")
        
        app_state["processing_status"] = "🔍 Searching documents..."
        
        # Use the stored Docs object for querying
        if "docs" not in app_state or not app_state["docs"]:
            return "", "", "", "No documents have been indexed. Please upload and process documents first."
        
        # Query using the Docs object with settings
        answer_response = await app_state["docs"].aquery(question, settings=app_state["settings"])
        
        processing_time = time.time() - start_time
        logger.info(f"Docs query completed in {processing_time:.2f} seconds")
        
        answer = answer_response.answer
        contexts = answer_response.contexts if hasattr(answer_response, 'contexts') else []
        
        if answer and "insufficient information" not in answer.lower():
            if "status_tracker" in app_state:
                app_state["status_tracker"].add_status("✅ Answer generated successfully!")
            app_state["processing_status"] = "✅ Answer generated successfully!"
        else:
            if "status_tracker" in app_state:
                app_state["status_tracker"].add_status("⚠️ Limited information found - try a more general question")
            app_state["processing_status"] = "⚠️ Limited information found - try a more general question"
        
        answer_html = format_answer_html(answer, contexts)
        sources_html = format_sources_html(contexts)
        metadata_html = format_metadata_html({
            "processing_time": processing_time,
            "documents_searched": len(app_state["uploaded_docs"]),
            "evidence_sources": len(contexts),
            "confidence": 0.85 if contexts else 0.3
        })
        
        return answer_html, sources_html, metadata_html, ""
        
    except Exception as e:
        app_state["processing_status"] = "❌ Error occurred during processing"
        error_msg = f"❌ Processing failed: {str(e)}"
        logger.error(f"Exception in process_question: {e}", exc_info=True)
        return "", "", "", error_msg


def process_question(question: str, config_name: str = "optimized_ollama") -> Tuple[str, str, str, str, str, str]:
    """Synchronous wrapper for process_question_async."""
    answer_html, sources_html, metadata_html, error_msg = asyncio.run(process_question_async(question, config_name))
    
    # Get status updates
    progress_html = ""
    status_html = ""
    if "status_tracker" in app_state:
        status_html = app_state["status_tracker"].get_status_html()
    
    return answer_html, sources_html, metadata_html, error_msg, progress_html, status_html


def format_answer_html(answer: str, contexts: List) -> str:
    """Format the answer as HTML."""
    if not answer:
        return "<div style='color: #666; text-align: center;'>No answer generated.</div>"
    
    # Simple formatting - you can enhance this
    formatted_answer = answer.replace('\n', '<br>')
    return f"<div style='background: #f8f9fa; padding: 15px; border-radius: 5px;'>{formatted_answer}</div>"


def format_sources_html(contexts: List) -> str:
    """Format the sources as HTML."""
    if not contexts:
        return "<div style='color: #666; text-align: center;'>No sources found.</div>"
    
    html_parts = ["<div style='max-height: 300px; overflow-y: auto;'>"]
    html_parts.append("<h4>Evidence Sources:</h4>")
    
    for i, context in enumerate(contexts, 1):
        try:
            # Extract source information
            source_name = getattr(context.text, 'name', f'Source {i}') if hasattr(context, 'text') else f'Source {i}'
            content = context.text[:200] + "..." if len(str(context.text)) > 200 else str(context.text)
            
            html_parts.append(f"<div style='margin-bottom: 10px; padding: 10px; background: #fff; border-left: 3px solid #007bff;'>")
            html_parts.append(f"<strong>{source_name}</strong><br>")
            html_parts.append(f"<small>{content}</small>")
            html_parts.append("</div>")
        except Exception as e:
            logger.warning(f"Error formatting context {i}: {e}")
            html_parts.append(f"<div>Source {i}: [Error formatting source]</div>")
    
    html_parts.append("</div>")
    return "".join(html_parts)


def format_metadata_html(metadata: dict) -> str:
    """Format metadata as HTML."""
    html_parts = ["<div style='background: #e9ecef; padding: 10px; border-radius: 5px; font-size: 0.9em;'>"]
    html_parts.append("<h5>Processing Information:</h5>")
    html_parts.append(f"<strong>Processing Time:</strong> {metadata.get('processing_time', 0):.2f} seconds<br>")
    html_parts.append(f"<strong>Documents Searched:</strong> {metadata.get('documents_searched', 0)}<br>")
    html_parts.append(f"<strong>Evidence Sources:</strong> {metadata.get('evidence_sources', 0)}<br>")
    html_parts.append(f"<strong>Confidence:</strong> {metadata.get('confidence', 0):.1%}")
    html_parts.append("</div>")
    return "".join(html_parts)


def clear_all():
    """Clear all uploaded documents and reset state."""
    app_state["uploaded_docs"] = []
    app_state["docs"] = None
    if "status_tracker" in app_state:
        app_state["status_tracker"].clear()
    return "", "", "", "", "", ""


# Initialize default settings
try:
    initialize_settings("optimized_ollama")
    logger.info("✅ Initialized with optimized Ollama configuration")
except Exception as e:
    logger.error(f"❌ Failed to initialize settings: {e}")

# Create Gradio interface
with gr.Blocks(title="Paper-QA UI", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📚 Paper-QA UI")
    gr.Markdown("Upload PDF documents and ask questions using local Ollama models.")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📁 Document Upload")
            file_upload = gr.File(
                file_count="multiple",
                file_types=[".pdf"],
                label="Upload PDF Documents"
            )
            upload_button = gr.Button("📤 Process Documents", variant="primary")
            upload_status = gr.Textbox(label="Upload Status", interactive=False)
            
            gr.Markdown("### ⚙️ Configuration")
            config_dropdown = gr.Dropdown(
                choices=["optimized_ollama", "openrouter_ollama", "ollama", "clinical_trials"],
                value="optimized_ollama",
                label="Select Configuration",
                info="Choose your preferred model configuration"
            )
            
            gr.Markdown("### 🧹 Actions")
            clear_button = gr.Button("🗑️ Clear All", variant="secondary")
        
        with gr.Column(scale=2):
            gr.Markdown("### ❓ Ask Questions")
            question_input = gr.Textbox(
                label="Enter your question",
                placeholder="What is this paper about?",
                lines=3
            )
            
            with gr.Row():
                ask_button = gr.Button("🤖 Ask Question", variant="primary", size="lg")
            
            # Status display
            status_display = gr.HTML(label="Processing Status")
            
            gr.Markdown("### 📝 Answer")
            answer_display = gr.HTML(label="Answer")
            
            gr.Markdown("### 📚 Sources")
            sources_display = gr.HTML(label="Evidence Sources")
            
            gr.Markdown("### 📊 Metadata")
            metadata_display = gr.HTML(label="Processing Information")
            
            error_display = gr.Textbox(label="Errors", interactive=False, visible=False)
    
    # Event handlers
    upload_button.click(
        fn=process_uploaded_files,
        inputs=[file_upload],
        outputs=[upload_status, error_display]
    )
    
    ask_button.click(
        fn=process_question,
        inputs=[question_input, config_dropdown],
        outputs=[answer_display, sources_display, metadata_display, error_display, status_display, status_display]
    )
    
    question_input.submit(
        fn=process_question,
        inputs=[question_input, config_dropdown],
        outputs=[answer_display, sources_display, metadata_display, error_display, status_display, status_display]
    )
    
    clear_button.click(
        fn=clear_all,
        outputs=[answer_display, sources_display, metadata_display, error_display, status_display, status_display]
    )

if __name__ == "__main__":
    import os
    # Suppress Gradio version warning
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
    
    try:
        demo.launch(
            server_name="0.0.0.0", 
            server_port=7860, 
            share=False,
            show_error=True,
            quiet=False
        )
    except OSError as e:
        if "address already in use" in str(e):
            print(f"❌ Port 7860 is already in use. Try: make kill-server")
        else:
            raise
