"""
Utility Functions for Paper-QA
Common utilities and helper functions.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.table import Table


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, create if it doesn't."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: Any, filepath: Union[str, Path], indent: int = 2) -> None:
    """Save data to JSON file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=indent)


def load_json(filepath: Union[str, Path]) -> Any:
    """Load data from JSON file."""
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, "r") as f:
        return json.load(f)


def format_timestamp(timestamp: Optional[float] = None) -> str:
    """Format timestamp as readable string."""
    if timestamp is None:
        timestamp = time.time()

    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def create_results_table(
    results: List[Dict[str, Any]], console: Optional[Console] = None
) -> Table:
    """Create a rich table from results."""
    console = console or Console()

    table = Table(title="Paper-QA Results")
    table.add_column("Method", style="cyan")
    table.add_column("Success", style="green")
    table.add_column("Sources", style="yellow")
    table.add_column("Duration", style="blue")
    table.add_column("Answer Length", style="magenta")

    for result in results:
        method = result.get("method", "Unknown")
        success = "✓" if result.get("success", False) else "✗"
        sources = str(result.get("sources", 0))
        duration = format_duration(result.get("duration", 0))
        answer_length = str(len(result.get("answer", "")))

        table.add_row(method, success, sources, duration, answer_length)

    return table


def save_results(results: List[Dict[str, Any]], output_dir: Union[str, Path]) -> None:
    """Save results to files."""
    output_dir = ensure_directory(output_dir)
    timestamp = format_timestamp().replace(" ", "_").replace(":", "-")

    # Clean results for JSON serialization
    def clean_for_json(obj):
        """Recursively clean objects for JSON serialization."""
        if isinstance(obj, dict):
            return {k: clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_for_json(item) for item in obj]
        elif hasattr(obj, "__dict__"):
            # Convert objects to string representation
            return str(obj)
        else:
            return obj

    cleaned_results = clean_for_json(results)

    # Save summary
    summary = {
        "timestamp": timestamp,
        "total_results": len(results),
        "successful_results": sum(1 for r in results if r.get("success", False)),
        "methods": list(set(r.get("method", "Unknown") for r in results)),
        "total_sources": sum(r.get("sources", 0) for r in results),
        "total_duration": sum(r.get("duration", 0) for r in results),
    }

    save_json(summary, output_dir / f"summary_{timestamp}.json")

    # Save individual results
    for i, result in enumerate(cleaned_results):
        result_file = output_dir / f"result_{i+1}_{timestamp}.json"
        save_json(result, result_file)

    # Save combined results
    combined_file = output_dir / f"combined_results_{timestamp}.json"
    save_json(cleaned_results, combined_file)


def validate_paper_directory(paper_dir: Union[str, Path]) -> Dict[str, Any]:
    """Validate a paper directory and return statistics."""
    paper_dir = Path(paper_dir)

    if not paper_dir.exists():
        return {
            "valid": False,
            "error": "Directory does not exist",
            "papers": 0,
            "size_mb": 0,
        }

    if not paper_dir.is_dir():
        return {
            "valid": False,
            "error": "Path is not a directory",
            "papers": 0,
            "size_mb": 0,
        }

    pdf_files = list(paper_dir.rglob("*.pdf"))
    total_size = sum(f.stat().st_size for f in pdf_files)

    return {
        "valid": True,
        "papers": len(pdf_files),
        "size_mb": total_size / (1024 * 1024),
        "files": [str(f.relative_to(paper_dir)) for f in pdf_files],
    }


def check_ollama_status() -> Dict[str, Any]:
    """Check if Ollama is running and accessible."""
    import httpx

    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {
                "running": True,
                "models": [m.get("name") for m in models],
                "nomad_embed_text_available": any(
                    "nomic-embed-text" in m.get("name", "") for m in models
                ),
            }
        else:
            return {
                "running": False,
                "error": f"HTTP {response.status_code}",
                "models": [],
                "nomad_embed_text_available": False,
            }
    except Exception as e:
        return {
            "running": False,
            "error": str(e),
            "models": [],
            "nomad_embed_text_available": False,
        }


def check_openrouter_status(api_key: Optional[str] = None) -> Dict[str, Any]:
    """Check if OpenRouter.ai is accessible."""
    import httpx

    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return {"accessible": False, "error": "No API key provided", "models": []}

    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        response = httpx.get(
            "https://openrouter.ai/api/v1/models", headers=headers, timeout=10
        )

        if response.status_code == 200:
            models = response.json().get("data", [])
            gemini_available = any(
                "gemini-2.5-flash-lite" in m.get("id", "") for m in models
            )

            return {
                "accessible": True,
                "models": [m.get("id") for m in models[:10]],  # First 10 models
                "gemini_2_5_flash_lite_available": gemini_available,
            }
        else:
            return {
                "accessible": False,
                "error": f"HTTP {response.status_code}",
                "models": [],
            }
    except Exception as e:
        return {"accessible": False, "error": str(e), "models": []}


def print_system_status(console: Optional[Console] = None) -> None:
    """Print system status including Ollama and OpenRouter.ai."""
    console = console or Console()

    console.print("\n[bold blue]System Status Check[/bold blue]")

    # Check Ollama
    ollama_status = check_ollama_status()
    if ollama_status["running"]:
        console.print("✅ [green]Ollama is running[/green]")
        if ollama_status["nomad_embed_text_available"]:
            console.print("✅ [green]nomic-embed-text model is available[/green]")
        else:
            console.print("⚠️ [yellow]nomic-embed-text model not found[/yellow]")
            console.print("   Run: ollama pull nomic-embed-text")
    else:
        console.print("❌ [red]Ollama is not running[/red]")
        console.print("   Start Ollama and run: ollama pull nomic-embed-text")

    # Check OpenRouter.ai
    openrouter_status = check_openrouter_status()
    if openrouter_status["accessible"]:
        console.print("✅ [green]OpenRouter.ai is accessible[/green]")
        if openrouter_status["gemini_2_5_flash_lite_available"]:
            console.print("✅ [green]Google Gemini 2.5 Flash Lite is available[/green]")
        else:
            console.print("⚠️ [yellow]Google Gemini 2.5 Flash Lite not found[/yellow]")
    else:
        console.print("❌ [red]OpenRouter.ai is not accessible[/red]")
        console.print(f"   Error: {openrouter_status['error']}")


def create_picalm_questions() -> List[Dict[str, str]]:
    """Create sample PICALM and Alzheimer's Disease questions."""
    return [
        {
            "id": "picalm_basic",
            "question": "What is the role of PICALM in Alzheimer's disease pathogenesis?",
            "type": "basic_research",
            "description": "Basic research question about PICALM's role in Alzheimer's disease",
        },
        {
            "id": "picalm_mechanistic",
            "question": "How does PICALM interact with amyloid-beta and tau proteins in Alzheimer's disease?",
            "type": "mechanistic",
            "description": "Mechanistic question about PICALM's interactions with key proteins",
        },
        {
            "id": "picalm_therapeutic",
            "question": "What are the potential therapeutic targets related to PICALM in Alzheimer's disease treatment?",
            "type": "therapeutic",
            "description": "Therapeutic question about PICALM as a drug target",
        },
    ]


def save_questions(
    questions: List[Dict[str, str]], output_file: Union[str, Path]
) -> None:
    """Save questions to JSON file."""
    save_json(questions, output_file)


def load_questions(input_file: Union[str, Path]) -> List[Dict[str, str]]:
    """Load questions from JSON file."""
    return load_json(input_file)
