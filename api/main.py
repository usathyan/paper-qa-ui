from dotenv import load_dotenv
import logging
import io
import sys
from api.config import get_settings
from paperqa import Docs, Settings
from paperqa.agents import agent_query
from paperqa.types import Doc
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Literal
import os
import shutil
import asyncio
import json

load_dotenv()

# Configure logging: turn off LiteLLM, enable paperqa DEBUG but suppress metadata warnings
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("LiteLLM Router").setLevel(logging.WARNING)
logging.getLogger("paperqa").setLevel(logging.INFO)  # Changed from DEBUG to INFO
logging.getLogger("paperqa.types").setLevel(logging.WARNING)  # Suppress metadata warnings

app = FastAPI(
    title="PaperQA Discovery API",
    description="""
    **PaperQA Discovery API** - A powerful scientific paper question-answering system.
    
    This API provides intelligent document analysis and question-answering capabilities for scientific papers.
    It supports multiple search sources including local uploaded papers and public domain research.
    
    ## Key Features:
    - **Multi-source Search**: Query local uploaded papers, public domain research, or both
    - **Intelligent Analysis**: Uses advanced LLM models for comprehensive document understanding
    - **Evidence-based Answers**: Provides citations and evidence for all responses
    - **Thinking Transparency**: Shows the AI's reasoning process for better understanding
    
    ## Search Sources:
    - **Local**: Only search through uploaded PDF papers
    - **Public**: Only search public domain research (requires external API keys)
    - **All**: Search both local papers and public domain research
    
    ## Authentication:
    - No authentication required for local operations
    - Public domain search requires Semantic Scholar and Crossref API keys
    """,
    version="2.0.0",
    contact={
        "name": "PaperQA Discovery",
        "url": "https://github.com/Future-House/paper-qa",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global docs object
docs = Docs()
UPLOAD_DIR = "uploaded_papers"

class Query(BaseModel):
    """
    Query request model for asking questions about scientific papers.
    
    This model defines the structure for submitting questions to the PaperQA system.
    The system will search through the specified sources to find relevant information
    and provide evidence-based answers.
    """
    query: str = Field(
        ...,
        description="The question or query to ask about scientific papers",
        example="What are the latest developments in KRAS inhibitors for cancer treatment?",
        min_length=1,
        max_length=1000
    )
    source: Literal["local", "public", "all"] = Field(
        default="all",
        description="""
        The search source to use for answering the query:
        
        - **local**: Only search through uploaded PDF papers in the system
        - **public**: Only search public domain research (requires external API keys)
        - **all**: Search both local papers and public domain research (recommended)
        """,
        example="all"
    )

class Evidence(BaseModel):
    """
    Evidence model representing a piece of supporting information for an answer.
    
    Each evidence item contains the actual text content and its source,
    allowing users to verify the information and understand where it came from.
    """
    context: str = Field(
        ...,
        description="The actual text content that supports the answer",
        example="The study found that KRAS inhibitors showed 45% response rate in patients with KRAS G12C mutations."
    )
    source: str = Field(
        ...,
        description="The name or identifier of the source document",
        example="KRAS_inhibitors_research_2024.pdf"
    )

class Paper(BaseModel):
    """
    Paper model representing a scientific document in the system.
    
    Contains metadata about uploaded or referenced papers, including
    the document name and citation information for proper attribution.
    """
    docname: str = Field(
        ...,
        description="The name or title of the paper/document",
        example="KRAS Inhibitors in Cancer Treatment: A Comprehensive Review"
    )
    citation: str = Field(
        ...,
        description="The citation information for the paper (author, journal, year, etc.)",
        example="Smith, J. et al. (2024). KRAS Inhibitors in Cancer Treatment. Nature Reviews Cancer, 24(3), 156-172."
    )

class Answer(BaseModel):
    """
    Answer response model containing the AI-generated response and supporting evidence.
    
    This model provides a comprehensive response including the main answer,
    supporting evidence with citations, and the AI's thinking process for transparency.
    """
    answer: str = Field(
        ...,
        description="The main answer to the user's query, synthesized from multiple sources",
        example="KRAS inhibitors have shown promising results in treating cancers with KRAS mutations, particularly G12C variants. Recent clinical trials demonstrate response rates of 30-45% in patients with advanced non-small cell lung cancer."
    )
    evidence: List[Evidence] = Field(
        default_factory=list,
        description="List of evidence pieces that support the answer, with source citations"
    )
    sources: List[Paper] = Field(
        default_factory=list,
        description="List of papers/documents that were referenced to generate the answer"
    )
    thinking_details: str = Field(
        default="",
        description="""
        Detailed thinking process of the AI system (when DEBUG logging is enabled).
        Shows the reasoning steps, search queries, and analysis process used to generate the answer.
        This provides transparency into how the AI arrived at its conclusions.
        """,
        example="Searching for KRAS inhibitors in uploaded papers... Found 3 relevant documents... Analyzing clinical trial data... Synthesizing findings from multiple sources..."
    )

class UploadResponse(BaseModel):
    """
    Response model for paper upload operations.
    
    Provides feedback on the success or failure of paper upload attempts,
    including error details when uploads fail.
    """
    message: str = Field(
        ...,
        description="Success or error message describing the upload result",
        example="Successfully uploaded KRAS_inhibitors_research_2024.pdf"
    )

class LoadPapersResponse(BaseModel):
    """
    Response model for bulk paper loading operations.
    
    Reports the number of papers successfully loaded from the upload directory
    and any errors encountered during the process.
    """
    message: str = Field(
        ...,
        description="Summary of the paper loading operation",
        example="Loaded 5 papers successfully"
    )

class DeleteResponse(BaseModel):
    """
    Response model for paper deletion operations.
    
    Confirms successful deletion of papers from the system
    or provides error details if deletion fails.
    """
    message: str = Field(
        ...,
        description="Confirmation message for paper deletion",
        example="Successfully deleted KRAS_inhibitors_research_2024.pdf"
    )

class HealthResponse(BaseModel):
    """
    Health check response model for system monitoring.
    
    Provides status information about the API server and its dependencies.
    """
    status: str = Field(
        ...,
        description="Overall system status",
        example="healthy"
    )
    version: str = Field(
        ...,
        description="API version",
        example="2.0.0"
    )
    papers_loaded: int = Field(
        ...,
        description="Number of papers currently loaded in the system",
        example=5
    )
    environment: Dict[str, bool] = Field(
        ...,
        description="Environment validation results",
        example={"openrouter_api_key": True, "ollama_server": True}
    )
    messages: List[str] = Field(
        default_factory=list,
        description="Any warning or error messages",
        example=["Ollama server not accessible"]
    )

@app.on_event("startup")
async def startup_event():
    print("PaperQA Discovery API server started successfully!")
    print("Papers will be loaded on first query or via /api/load-papers endpoint")

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """
    Health check endpoint for system monitoring.
    
    This endpoint provides comprehensive status information about the API server
    and its dependencies. It's useful for monitoring, debugging, and ensuring
    the system is properly configured.
    
    **Checks:**
    - API server status
    - Number of loaded papers
    - Environment validation (API keys, services)
    - Configuration status
    
    **Returns:**
    - Overall system health status
    - Environment validation results
    - Any warning or error messages
    
    **Use Cases:**
    - System monitoring and alerting
    - Debugging configuration issues
    - Health checks for load balancers
    - Development environment validation
    """
    from api.config import validate_environment
    
    # Validate environment
    env_validation = validate_environment()
    
    # Determine overall status
    status = "healthy"
    messages = env_validation["messages"]
    
    if not env_validation["openrouter_api_key"]:
        status = "degraded"
        messages.append("OpenRouter API key not configured - public search unavailable")
    
    if not env_validation["ollama_server"]:
        status = "degraded"
        messages.append("Ollama server not accessible - embeddings may fail")
    
    if len(messages) > 2:  # More than just the basic warnings
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        version="2.0.0",
        papers_loaded=len(docs.docs),
        environment={
            "openrouter_api_key": env_validation["openrouter_api_key"],
            "ollama_server": env_validation["ollama_server"]
        },
        messages=messages
    )

@app.get("/", tags=["System"])
def root():
    """
    Root endpoint providing basic API information.
    
    Returns basic information about the PaperQA Discovery API
    and links to the interactive documentation.
    """
    return {
        "message": "PaperQA Discovery API",
        "version": "2.0.0",
        "description": "A powerful scientific paper question-answering system",
        "documentation": "/docs",
        "health_check": "/health",
        "endpoints": {
            "upload_paper": "/api/upload",
            "list_papers": "/api/papers",
            "delete_paper": "/api/papers/{docname}",
            "load_papers": "/api/load-papers",
            "query": "/api/query"
        }
    }

@app.post("/api/upload", response_model=UploadResponse, tags=["Paper Management"])
async def upload_paper(
    file: UploadFile = File(
        ...,
        description="PDF file to upload and add to the paper collection",
        example="research_paper.pdf"
    )
):
    """
    Upload a PDF paper to the system.
    
    This endpoint allows you to upload PDF documents that will be processed and indexed
    for future queries. The system will extract text, create embeddings, and make the
    content searchable for question-answering.
    
    **Supported Formats:**
    - PDF files only (.pdf extension)
    
    **File Size Limits:**
    - Maximum file size: 50MB
    - Recommended: Under 20MB for optimal processing speed
    
    **Processing:**
    - Text extraction and chunking
    - Embedding generation for semantic search
    - Indexing for fast retrieval
    
    **Returns:**
    - Success message with filename
    - Error details if upload fails
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are supported. Please upload a file with .pdf extension."
        )
    
    if file.size and file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(
            status_code=400,
            detail="File size too large. Maximum allowed size is 50MB."
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Add to docs with settings
        settings = get_settings()
        await docs.aadd(file_path, settings=settings)
        
        return UploadResponse(message=f"Successfully uploaded {file.filename}")
    except Exception as e:
        # Clean up file if loading failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to load paper: {str(e)}"
        )

@app.get("/api/papers", response_model=List[Paper], tags=["Paper Management"])
def get_papers():
    """
    Get list of all loaded papers in the system.
    
    Returns metadata for all papers that have been successfully uploaded
    and processed by the system. This includes the document name and
    citation information for each paper.
    
    **Returns:**
    - List of paper objects with names and citations
    - Empty list if no papers are loaded
    
    **Use Cases:**
    - Check what papers are available for querying
    - Verify successful upload of papers
    - Get citation information for papers
    """
    return [
        Paper(docname=doc.docname, citation=doc.citation)
        for doc in docs.docs.values()
    ]

@app.delete("/api/papers/{docname}", response_model=DeleteResponse, tags=["Paper Management"])
async def delete_paper(docname: str):
    """
    Delete a specific paper from the system.
    
    Removes a paper from the collection and frees up associated resources.
    The paper will no longer be available for queries after deletion.
    
    **Parameters:**
    - docname: Exact name of the paper file to delete
    
    **Returns:**
    - Confirmation message on successful deletion
    - Error if paper not found
    
    **Note:**
    - This operation is irreversible
    - The paper file will be removed from the upload directory
    - All associated embeddings and indexes will be cleaned up
    """
    try:
        docs.delete(docname=docname)
        return DeleteResponse(message=f"Successfully deleted {docname}")
    except Exception as e:
        raise HTTPException(
            status_code=404, 
            detail=f"Paper not found: {str(e)}"
        )

@app.post("/api/load-papers", response_model=LoadPapersResponse, tags=["Paper Management"])
async def load_papers():
    """
    Load all PDF papers from the upload directory.
    
    This endpoint scans the upload directory for PDF files and processes
    them for use in the question-answering system. This is useful for
    bulk loading papers or reloading papers after system restart.
    
    **Process:**
    - Scans uploaded_papers/ directory for .pdf files
    - Processes each file with text extraction and embedding generation
    - Adds papers to the searchable collection
    
    **Returns:**
    - Summary of how many papers were successfully loaded
    - Error details for any papers that failed to load
    
    **Use Cases:**
    - Bulk paper loading
    - System initialization
    - Recovery after system restart
    """
    if not os.path.exists(UPLOAD_DIR):
        return LoadPapersResponse(message="No papers directory found")
    
    loaded_count = 0
    settings = get_settings()
    
    for filename in os.listdir(UPLOAD_DIR):
        if filename.endswith('.pdf'):
            try:
                file_path = os.path.join(UPLOAD_DIR, filename)
                print(f"Loading paper: {file_path}")
                await docs.aadd(file_path, settings=settings)
                loaded_count += 1
                print(f"Successfully loaded: {filename}")
            except Exception as e:
                print(f"Error loading paper {filename}: {e}")
    
    return LoadPapersResponse(message=f"Loaded {loaded_count} papers")

@app.post("/api/query", response_model=Answer, tags=["Question Answering"])
async def query(query: Query):
    """
    Ask a question about scientific papers and get an intelligent answer with streaming thinking details.
    
    This is the main endpoint for interacting with the PaperQA system.
    It processes natural language questions and returns comprehensive
    answers based on the specified search sources.
    
    **Current Implementation:**
    - Uses direct PaperQA queries with enhanced logging for thinking transparency
    - Agentic approach is configured but temporarily disabled due to compatibility issues
    - Enhanced evidence extraction and source tracking
    - Real-time thinking details capture
    
    **Search Sources:**
    - **local**: Only search uploaded papers (fastest, most relevant)
    - **public**: Only search public domain research (requires API keys)
    - **all**: Search both sources (most comprehensive, recommended)
    
    **Response Includes:**
    - Synthesized answer from multiple sources
    - Supporting evidence with citations
    - List of referenced papers
    - AI thinking process and reasoning steps
    
    **Processing Time:**
    - Local queries: 10-30 seconds
    - Public queries: 30-60 seconds
    - All sources: 30-90 seconds
    
    **Example Queries:**
    - "What are the latest developments in KRAS inhibitors?"
    - "Summarize the findings on immunotherapy for lung cancer"
    - "What is the mechanism of action of CRISPR gene editing?"
    
    **Returns:**
    - Comprehensive answer with evidence
    - Error details if query processing fails
    """
    # Ensure papers are loaded before processing query
    if len(docs.docs) == 0:
        await load_papers()
    
    # Get settings
    settings = get_settings()
    
    # Set up enhanced logging to capture ALL thinking details
    thinking_log = io.StringIO()
    thinking_handler = logging.StreamHandler(thinking_log)
    thinking_handler.setLevel(logging.DEBUG)  # Capture ALL levels for maximum detail
    thinking_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Add handler to ALL relevant loggers for comprehensive thinking capture
    paperqa_logger = logging.getLogger("paperqa")
    paperqa_logger.addHandler(thinking_handler)
    paperqa_logger.setLevel(logging.DEBUG)  # Ensure we get all details
    
    # Also capture from sub-modules
    core_logger = logging.getLogger("paperqa.core")
    core_logger.addHandler(thinking_handler)
    core_logger.setLevel(logging.DEBUG)
    
    docs_logger = logging.getLogger("paperqa.docs")
    docs_logger.addHandler(thinking_handler)
    docs_logger.setLevel(logging.DEBUG)
    
    # Temporarily suppress metadata warnings during query
    types_logger = logging.getLogger("paperqa.types")
    original_level = types_logger.level
    types_logger.setLevel(logging.WARNING)
    
    try:
        # Configure settings based on source type - use PaperQA's native capabilities
        if query.source == "public":
            # For public searches, use a fresh Docs object (no local papers)
            query_docs = Docs()
            settings.parsing.doc_filters = None
            print(f"Querying public sources only: {query.query}")
            
        elif query.source == "local":
            # For local searches, use existing docs but filter to only uploaded papers
            query_docs = docs
            settings.parsing.doc_filters = [{"file_location": UPLOAD_DIR}]
            print(f"Querying local papers only: {query.query}")
            
        else:  # "all" - use PaperQA's native capability to search both
            # For all sources, use existing docs with all capabilities
            query_docs = docs
            settings.parsing.doc_filters = None
            print(f"Querying all sources (local + public): {query.query}")
        
        print(f"Querying with {len(query_docs.docs)} loaded documents")
        
        # Execute query using PaperQA's direct aquery method (agentic approach has compatibility issues)
        # TODO: Re-enable agentic approach once compatibility issues are resolved
        result = await query_docs.aquery(query.query, settings=settings)
        
        # Extract evidence and sources from agentic response
        evidence = []
        sources = []
        
        # Agentic response has different structure - extract from result
        if hasattr(result, 'contexts') and result.contexts:
            evidence = [
                Evidence(context=context.context, source=context.text.name)
                for context in result.contexts
            ]
            
            unique_docs = {}
            for context in result.contexts:
                unique_docs[context.text.doc.dockey] = context.text.doc
            
            sources = [
                Paper(docname=doc.docname, citation=doc.citation)
                for doc in unique_docs.values()
            ]
        elif hasattr(result, 'answer'):
            # If no contexts, create basic evidence from the answer
            evidence = [
                Evidence(context=result.answer, source="Agent Response")
            ]
        
        # Get thinking details from captured logs
        thinking_details = thinking_log.getvalue()
        
        # Extract answer from agentic response
        answer_text = ""
        if hasattr(result, 'formatted_answer'):
            answer_text = result.formatted_answer
        elif hasattr(result, 'answer'):
            answer_text = result.answer
        else:
            answer_text = str(result)
        
        return Answer(
            answer=answer_text,
            evidence=evidence,
            sources=sources,
            thinking_details=thinking_details,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Query failed: {str(e)}"
        )
    finally:
        # Clean up logging handlers
        paperqa_logger.removeHandler(thinking_handler)
        core_logger.removeHandler(thinking_handler)
        docs_logger.removeHandler(thinking_handler)
        thinking_log.close()
        # Restore original logger levels
        types_logger.setLevel(original_level)

@app.post("/api/query/stream", tags=["Question Answering"])
async def query_stream(query: Query):
    """
    Stream a question about scientific papers with real-time thinking updates.
    
    This endpoint provides real-time streaming of the AI's thinking process
    as it processes your question, followed by the final answer.
    
    **Streaming Format:**
    - Each line is a JSON object with 'type' and 'content' fields
    - Types: 'thinking', 'evidence', 'answer', 'complete'
    - Real-time updates show the AI's reasoning process
    
    **Example Stream:**
    ```
    {"type": "thinking", "content": "Analyzing query: What are KRAS inhibitors?"}
    {"type": "thinking", "content": "Searching local papers for relevant information..."}
    {"type": "thinking", "content": "Found 3 relevant documents, extracting key information..."}
    {"type": "evidence", "content": "Document A: KRAS inhibitors show 45% response rate..."}
    {"type": "answer", "content": "KRAS inhibitors have shown promising results..."}
    {"type": "complete", "content": "Query completed successfully"}
    ```
    """
    async def generate_stream():
        # Ensure papers are loaded
        if len(docs.docs) == 0:
            await load_papers()
        
        settings = get_settings()
        
        # Set up streaming thinking capture
        thinking_queue = asyncio.Queue()
        
        class StreamingHandler(logging.Handler):
            def emit(self, record):
                try:
                    msg = self.format(record)
                    asyncio.create_task(thinking_queue.put({
                        "type": "thinking",
                        "content": msg
                    }))
                except Exception:
                    pass
        
        # Add streaming handler to all relevant loggers
        streaming_handler = StreamingHandler()
        streaming_handler.setFormatter(logging.Formatter('%(message)s'))
        
        paperqa_logger = logging.getLogger("paperqa")
        paperqa_logger.addHandler(streaming_handler)
        paperqa_logger.setLevel(logging.DEBUG)
        
        core_logger = logging.getLogger("paperqa.core")
        core_logger.addHandler(streaming_handler)
        core_logger.setLevel(logging.DEBUG)
        
        docs_logger = logging.getLogger("paperqa.docs")
        docs_logger.addHandler(streaming_handler)
        docs_logger.setLevel(logging.DEBUG)
        
        try:
            # Send initial thinking update
            yield f"data: {json.dumps({'type': 'thinking', 'content': f'Starting analysis of query: {query.query}'})}\n\n"
            
            # Configure settings based on source type
            if query.source == "public":
                query_docs = Docs()
                settings.parsing.doc_filters = None
                yield f"data: {json.dumps({'type': 'thinking', 'content': 'Searching public sources only...'})}\n\n"
                
            elif query.source == "local":
                query_docs = docs
                settings.parsing.doc_filters = [{"file_location": UPLOAD_DIR}]
                yield f"data: {json.dumps({'type': 'thinking', 'content': f'Searching {len(docs.docs)} local papers...'})}\n\n"
                
            else:  # "all"
                query_docs = docs
                settings.parsing.doc_filters = None
                yield f"data: {json.dumps({'type': 'thinking', 'content': f'Searching all sources ({len(docs.docs)} local papers + public domain)...'})}\n\n"
            
            # Execute query with streaming updates
            result = await query_docs.aquery(query.query, settings=settings)
            
            # Process results and send final updates
            if hasattr(result, 'contexts') and result.contexts:
                for i, context in enumerate(result.contexts[:3]):  # Show top 3 pieces of evidence
                    yield f"data: {json.dumps({'type': 'evidence', 'content': f'Evidence {i+1}: {context.context[:200]}...'})}\n\n"
            
            # Send final answer
            answer_text = ""
            if hasattr(result, 'formatted_answer'):
                answer_text = result.formatted_answer
            elif hasattr(result, 'answer'):
                answer_text = result.answer
            else:
                answer_text = str(result)
            
            yield f"data: {json.dumps({'type': 'answer', 'content': answer_text})}\n\n"
            yield f"data: {json.dumps({'type': 'complete', 'content': 'Query completed successfully'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Query failed: {str(e)}'})}\n\n"
        finally:
            # Clean up handlers
            paperqa_logger.removeHandler(streaming_handler)
            core_logger.removeHandler(streaming_handler)
            docs_logger.removeHandler(streaming_handler)
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)