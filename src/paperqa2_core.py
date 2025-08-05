"""
PaperQA2 Core Functions
Simplified implementation focused on the specifications: upload PDFs, ask questions, get cited answers.
"""

import asyncio
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from paperqa import Docs, Settings
except ImportError as e:
    logging.error(f"Error importing paperqa: {e}")
    logging.error("Please ensure paper-qa is installed: uv pip install paper-qa")
    raise

from config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Enable debug logging for paper-qa
logging.getLogger("paperqa").setLevel(logging.DEBUG)


class PaperQA2Core:
    """
    Core class for PaperQA2 functionality according to specifications.
    Focuses on: document upload, processing, question answering with citations.
    """
    
    def __init__(self, config_name: str = "default"):
        """Initialize PaperQA2 core with specified configuration."""
        self.config_name = config_name
        self.config_manager = ConfigManager()
        self.settings = self._load_settings(config_name)
        self.docs = None
        self.session_id = f"session_{int(time.time())}"
        self.documents = []
        
        # Create session directories
        self.paper_dir = Path("./papers") / self.session_id
        self.index_dir = Path("./indexes") / self.session_id
        
        self.paper_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized PaperQA2 core with config: {config_name}")
    
    def _load_settings(self, config_name: str) -> Settings:
        """Load PaperQA settings from configuration."""
        try:
            # Get the Settings object directly from config manager
            settings = self.config_manager.get_settings(config_name)
            return settings
            
        except Exception as e:
            logger.error(f"Failed to load settings for {config_name}: {e}")
            # Return default settings
            return Settings()
    
    async def add_document(self, file_path: str) -> Dict[str, Any]:
        """
        Add a document to the PaperQA index.
        
        Args:
            file_path: Path to the PDF document
            
        Returns:
            Dict with processing results
        """
        try:
            # Validate file
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found: {file_path}"}
            
            if not (file_path.lower().endswith('.pdf') or file_path.lower().endswith('.txt')):
                return {"success": False, "error": "Only PDF and TXT files are supported"}
            
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:  # 100MB limit from specs
                return {"success": False, "error": "File too large (max 100MB)"}
            
            # Initialize Docs if not already done
            if self.docs is None:
                self.docs = Docs()
            
            # Handle the file path (Gradio uploads to temp directory)
            original_path = Path(file_path)
            filename = original_path.name
            
            # For permanent storage, copy to our session directory to avoid temp file cleanup
            session_file_path = self.paper_dir / filename
            
            try:
                # Ensure session directory exists
                self.paper_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy file to session directory for permanent storage
                import shutil
                shutil.copy2(file_path, session_file_path)
                logger.info(f"Copied {filename} to {session_file_path}")
                
                # Verify the copied file exists and is readable
                if not session_file_path.exists():
                    return {"success": False, "error": f"Failed to copy file to {session_file_path}"}
                
                # Add document to PaperQA using the permanent path
                await self.docs.aadd(str(session_file_path), settings=self.settings)
                
                logger.info(f"Successfully processed and stored: {filename}")
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                # Provide more specific error messages
                if "Failed to open file" in str(e):
                    return {"success": False, "error": f"Could not read PDF file: {filename}. File may be corrupted or password-protected."}
                else:
                    return {"success": False, "error": f"Failed to process document: {str(e)}"}
            
            # Store document info
            doc_info = {
                "filename": filename,
                "size": file_size,
                "path": str(session_file_path),
                "status": "processed"
            }
            self.documents.append(doc_info)
            
            logger.info(f"Successfully added document: {filename}")
            return {"success": True, "document": doc_info}
        
        except Exception as e:
            logger.error(f"Failed to add document {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=20))
    async def ask_question(self, question: str) -> Dict[str, Any]:
        """
        Ask a question about the uploaded documents.
        
        Args:
            question: The user's question
            
        Returns:
            Dict with answer, citations, and metadata
        """
        try:
            if not self.docs:
                return {
                    "success": False, 
                    "error": "No documents uploaded. Please upload documents first."
                }
            
            if not question.strip():
                return {"success": False, "error": "Please provide a question."}
            
            if len(question) > 500:
                return {"success": False, "error": "Question too long (max 500 characters)."}
            
            # Track processing time
            start_time = time.time()
            
            # Use PaperQA to answer the question
            result = await self.docs.aquery(question, settings=self.settings)
            
            processing_time = time.time() - start_time
            
            # Extract answer and format response
            if hasattr(result, 'answer'):
                answer = result.answer
            else:
                answer = str(result)
            
            # Extract citations and evidence
            citations = []
            evidence_sources = []
            
            if hasattr(result, 'context') and result.context:
                for i, context in enumerate(result.context):
                    # Extract citation info
                    if hasattr(context, 'text') and hasattr(context, 'name'):
                        citations.append({
                            "text": context.name,
                            "page": getattr(context, 'page', 'Unknown'),
                            "doc": getattr(context, 'doc', 'Unknown')
                        })
                        
                        evidence_sources.append({
                            "text": context.text[:300],  # Limit text length
                            "score": getattr(context, 'score', 0.0),
                            "doc": getattr(context, 'doc', 'Unknown'),
                            "page": getattr(context, 'page', 'Unknown')
                        })
            
            # Check if answer is meaningful
            if not answer or answer.strip().lower() in ["i don't know", "i cannot answer", ""]:
                return {
                    "success": True,
                    "answer": "I cannot answer this question based on the provided documents.",
                    "citations": [],
                    "evidence_sources": [],
                    "metadata": {
                        "processing_time": processing_time,
                        "documents_searched": len(self.documents),
                        "evidence_sources": 0,
                        "confidence": 0.0
                    }
                }
            
            return {
                "success": True,
                "answer": answer,
                "citations": citations,
                "evidence_sources": evidence_sources,
                "metadata": {
                    "processing_time": processing_time,
                    "documents_searched": len(self.documents),
                    "evidence_sources": len(evidence_sources),
                    "confidence": 0.85  # Would be calculated from actual scores
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to process question '{question}': {e}")
            error_msg = str(e)
            
            # Handle specific error types with user-friendly messages
            if "TCPTransport closed" in error_msg or "handler is closed" in error_msg:
                error_msg = "Connection error occurred. This is usually temporary - please try again."
            elif "rate limit" in error_msg.lower() or "429" in error_msg:
                error_msg = "Rate limit exceeded. Please wait a moment and try again."
            elif "timeout" in error_msg.lower():
                error_msg = "Request timed out. Please try again with a shorter question."
            
            return {"success": False, "error": error_msg}
    
    def get_documents(self) -> List[Dict[str, Any]]:
        """Get list of uploaded documents."""
        return self.documents.copy()
    
    def clear_documents(self) -> None:
        """Clear all uploaded documents."""
        self.documents.clear()
        self.docs = None
        logger.info("Cleared all documents")
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session."""
        return {
            "session_id": self.session_id,
            "config_name": self.config_name,
            "documents_count": len(self.documents),
            "paper_directory": str(self.paper_dir),
            "index_directory": str(self.index_dir)
        }
    
    def add_document_sync(self, file_path: str) -> Dict[str, Any]:
        """Synchronous wrapper for add_document."""
        try:
            import asyncio
            import threading
            import concurrent.futures
            
            def run_in_thread():
                # Create a new event loop in this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(self.add_document(file_path))
                    # Wait for any pending tasks to complete
                    pending = asyncio.all_tasks(loop)
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    return result
                finally:
                    # Ensure all tasks are properly cleaned up
                    try:
                        # Cancel any remaining tasks
                        remaining_tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
                        if remaining_tasks:
                            for task in remaining_tasks:
                                task.cancel()
                            loop.run_until_complete(asyncio.gather(*remaining_tasks, return_exceptions=True))
                        
                        # Cleanup generators and executor
                        loop.run_until_complete(loop.shutdown_asyncgens())
                        loop.run_until_complete(loop.shutdown_default_executor())
                    except Exception as e:
                        # Don't propagate cleanup errors
                        pass
                    finally:
                        # Close the loop
                        if not loop.is_closed():
                            loop.close()
            
            # Run in a separate thread to avoid event loop conflicts
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=300)
                
        except Exception as e:
            logger.error(f"Error in add_document_sync: {e}")
            return {"success": False, "error": str(e)}
    
    def ask_question_sync(self, question: str) -> Dict[str, Any]:
        """Synchronous wrapper for ask_question using the proven ThreadPoolExecutor approach."""
        try:
            import asyncio
            import concurrent.futures
            
            def run_async_query():
                """Run the async query in a clean event loop."""
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Run the query - let LiteLLM manage its own HTTP clients
                    result = loop.run_until_complete(self.ask_question(question))
                    return result
                finally:
                    # Clean up the loop
                    try:
                        # Wait for any remaining tasks
                        pending = asyncio.all_tasks(loop)
                        if pending:
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        
                        # Shutdown generators and executor
                        loop.run_until_complete(loop.shutdown_asyncgens())
                        loop.run_until_complete(loop.shutdown_default_executor())
                    except Exception:
                        pass  # Ignore cleanup errors
                    finally:
                        if not loop.is_closed():
                            loop.close()
            
            # Check if there's already an event loop running
            try:
                asyncio.get_running_loop()
                # If we're in an event loop, use ThreadPoolExecutor
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async_query)
                    return future.result(timeout=600)  # 10 minute timeout
            except RuntimeError:
                # No event loop running, we can run directly
                return run_async_query()
                
        except concurrent.futures.TimeoutError:
            return {"success": False, "error": "Question processing timed out after 10 minutes"}
        except Exception as e:
            logger.error(f"Error in ask_question_sync: {e}")
            return {"success": False, "error": str(e)}


# Backward compatibility - maintain old interface for existing code
class PaperQACore(PaperQA2Core):
    """Backward compatibility wrapper for existing code."""
    
    async def query_local_papers(self, question: str, paper_directory: Optional[str] = None) -> Dict[str, Any]:
        """Query local papers - legacy interface."""
        return await self.ask_question(question)
    
    async def query_public_sources(self, question: str) -> Dict[str, Any]:
        """Query public sources - not implemented in new focused design."""
        return {
            "success": False,
            "error": "Public sources not available. Please upload PDF documents."
        }
    
    async def query_combined(self, question: str, paper_directory: Optional[str] = None) -> Dict[str, Any]:
        """Query combined sources - legacy interface."""
        return await self.ask_question(question)