"""
Configuration UI Management
Handles loading, saving, and managing all configurable variables through the UI.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import gradio as gr


class ConfigUIManager:
    """Manages configuration through the UI."""

    def __init__(self, configs_dir: str = "configs"):
        self.configs_dir = Path(configs_dir)
        self.config_files = {
            "default": "default.json",
            "local_only": "local_only.json",
            "public_only": "public_only.json",
            "combined": "combined.json",
            "openrouter": "openrouter.json",
            "agent_optimized": "agent_optimized.json",
            "comprehensive": "comprehensive.json",
        }

    def get_available_configs(self) -> List[str]:
        """Get list of available configuration files."""
        return list(self.config_files.keys())

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load a configuration file."""
        if config_name not in self.config_files:
            raise ValueError(f"Unknown config: {config_name}")

        config_path = self.configs_dir / self.config_files[config_name]
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            return json.load(f)

    def save_config(self, config_name: str, config_data: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        if config_name not in self.config_files:
            raise ValueError(f"Unknown config: {config_name}")

        config_path = self.configs_dir / self.config_files[config_name]

        # Create backup
        if config_path.exists():
            backup_path = config_path.with_suffix(".json.backup")
            with open(config_path, "r") as f:
                backup_data = f.read()
            with open(backup_path, "w") as f:
                f.write(backup_data)

        # Save new config
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)

        return True

    def get_config_schema(self) -> Dict[str, Any]:
        """Get the complete configuration schema with all available options."""
        return {
            "llm": {
                "type": "text",
                "label": "LLM Model",
                "description": "The LLM model to use for answering questions",
                "default": "openrouter/google/gemini-2.5-flash-lite",
                "options": [
                    "openrouter/google/gemini-2.5-flash-lite",
                    "openrouter/anthropic/claude-3.5-sonnet",
                    "openrouter/meta-llama/llama-3.1-8b-instruct",
                    "ollama/llama3.2",
                ],
            },
            "summary_llm": {
                "type": "text",
                "label": "Summary LLM Model",
                "description": "The LLM model to use for summarization",
                "default": "openrouter/google/gemini-2.5-flash-lite",
                "options": [
                    "openrouter/google/gemini-2.5-flash-lite",
                    "openrouter/anthropic/claude-3.5-sonnet",
                    "openrouter/meta-llama/llama-3.1-8b-instruct",
                    "ollama/llama3.2",
                ],
            },
            "embedding": {
                "type": "text",
                "label": "Embedding Model",
                "description": "The embedding model to use for vector search",
                "default": "ollama/nomic-embed-text",
                "options": [
                    "ollama/nomic-embed-text",
                    "openai/text-embedding-ada-002",
                    "sentence-transformers/all-MiniLM-L6-v2",
                ],
            },
            "temperature": {
                "type": "number",
                "label": "Temperature",
                "description": "Controls randomness in LLM responses (0.0 = deterministic, 1.0 = very random)",
                "default": 0.0,
                "minimum": 0.0,
                "maximum": 2.0,
                "step": 0.1,
            },
            "verbosity": {
                "type": "number",
                "label": "Verbosity Level",
                "description": "Logging verbosity level (0 = silent, 3 = very verbose)",
                "default": 3,
                "minimum": 0,
                "maximum": 5,
                "step": 1,
            },
            "agent": {
                "agent_llm": {
                    "type": "text",
                    "label": "Agent LLM Model",
                    "description": "The LLM model for the agent",
                    "default": "openrouter/google/gemini-2.5-flash-lite",
                },
                "agent_type": {
                    "type": "dropdown",
                    "label": "Agent Type",
                    "description": "Type of agent to use",
                    "default": "ToolSelector",
                    "choices": ["ToolSelector", "Task"],
                },
                "search_count": {
                    "type": "number",
                    "label": "Search Count",
                    "description": "Number of papers to search for",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                    "step": 1,
                },
                "timeout": {
                    "type": "number",
                    "label": "Timeout (seconds)",
                    "description": "Agent execution timeout",
                    "default": 600.0,
                    "minimum": 30.0,
                    "maximum": 3600.0,
                    "step": 30.0,
                },
                "should_pre_search": {
                    "type": "checkbox",
                    "label": "Pre-search",
                    "description": "Run search tool before invoking agent",
                    "default": True,
                },
                "wipe_context_on_answer_failure": {
                    "type": "checkbox",
                    "label": "Wipe Context on Failure",
                    "description": "Clear context when answer generation fails",
                    "default": True,
                },
                "agent_evidence_n": {
                    "type": "number",
                    "label": "Agent Evidence Count",
                    "description": "Number of evidence pieces for agent",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 50,
                    "step": 1,
                },
                "return_paper_metadata": {
                    "type": "checkbox",
                    "label": "Return Paper Metadata",
                    "description": "Include paper metadata in results",
                    "default": True,
                },
                "index": {
                    "paper_directory": {
                        "type": "text",
                        "label": "Paper Directory",
                        "description": "Directory containing papers to index",
                        "default": "./papers",
                    },
                    "index_directory": {
                        "type": "text",
                        "label": "Index Directory",
                        "description": "Directory to store indexes",
                        "default": "./indexes",
                    },
                    "recurse_subdirectories": {
                        "type": "checkbox",
                        "label": "Recurse Subdirectories",
                        "description": "Search subdirectories for papers",
                        "default": True,
                    },
                    "concurrency": {
                        "type": "number",
                        "label": "Concurrency",
                        "description": "Number of concurrent filesystem reads",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10,
                        "step": 1,
                    },
                    "sync_with_paper_directory": {
                        "type": "checkbox",
                        "label": "Sync with Paper Directory",
                        "description": "Keep index synchronized with paper directory",
                        "default": False,
                    },
                },
            },
            "answer": {
                "evidence_k": {
                    "type": "number",
                    "label": "Evidence K",
                    "description": "Number of evidence pieces to retrieve",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                    "step": 1,
                },
                "evidence_detailed_citations": {
                    "type": "checkbox",
                    "label": "Detailed Citations",
                    "description": "Include detailed citation information",
                    "default": True,
                },
                "evidence_retrieval": {
                    "type": "checkbox",
                    "label": "Evidence Retrieval",
                    "description": "Enable evidence retrieval",
                    "default": True,
                },
                "evidence_relevance_score_cutoff": {
                    "type": "number",
                    "label": "Relevance Score Cutoff",
                    "description": "Minimum relevance score for evidence",
                    "default": 1,
                    "minimum": 0,
                    "maximum": 10,
                    "step": 0.1,
                },
                "evidence_summary_length": {
                    "type": "text",
                    "label": "Evidence Summary Length",
                    "description": "Length of evidence summaries",
                    "default": "about 150 words",
                },
                "evidence_skip_summary": {
                    "type": "checkbox",
                    "label": "Skip Evidence Summary",
                    "description": "Skip generating evidence summaries",
                    "default": False,
                },
                "answer_max_sources": {
                    "type": "number",
                    "label": "Max Sources",
                    "description": "Maximum number of sources in answer",
                    "default": 15,
                    "minimum": 1,
                    "maximum": 50,
                    "step": 1,
                },
                "max_answer_attempts": {
                    "type": "number",
                    "label": "Max Answer Attempts",
                    "description": "Maximum attempts to generate answer",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10,
                    "step": 1,
                },
                "answer_length": {
                    "type": "text",
                    "label": "Answer Length",
                    "description": "Target length for answers",
                    "default": "about 500 words",
                },
                "max_concurrent_requests": {
                    "type": "number",
                    "label": "Max Concurrent Requests",
                    "description": "Maximum concurrent API requests",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 10,
                    "step": 1,
                },
                "answer_filter_extra_background": {
                    "type": "checkbox",
                    "label": "Filter Extra Background",
                    "description": "Filter out extra background information",
                    "default": False,
                },
                "get_evidence_if_no_contexts": {
                    "type": "checkbox",
                    "label": "Get Evidence if No Contexts",
                    "description": "Retrieve evidence even if no contexts found",
                    "default": True,
                },
                "group_contexts_by_question": {
                    "type": "checkbox",
                    "label": "Group Contexts by Question",
                    "description": "Group contexts by their associated question",
                    "default": False,
                },
            },
            "parsing": {
                "chunk_size": {
                    "type": "number",
                    "label": "Chunk Size",
                    "description": "Size of text chunks for processing",
                    "default": 5000,
                    "minimum": 1000,
                    "maximum": 10000,
                    "step": 500,
                },
                "page_size_limit": {
                    "type": "number",
                    "label": "Page Size Limit",
                    "description": "Maximum page size for processing",
                    "default": 1280000,
                    "minimum": 100000,
                    "maximum": 5000000,
                    "step": 100000,
                },
                "pdfs_use_block_parsing": {
                    "type": "checkbox",
                    "label": "PDF Block Parsing",
                    "description": "Use block parsing for PDFs",
                    "default": False,
                },
                "use_doc_details": {
                    "type": "checkbox",
                    "label": "Use Document Details",
                    "description": "Include document details in processing",
                    "default": True,
                },
                "overlap": {
                    "type": "number",
                    "label": "Overlap",
                    "description": "Overlap between text chunks",
                    "default": 250,
                    "minimum": 0,
                    "maximum": 1000,
                    "step": 50,
                },
                "disable_doc_valid_check": {
                    "type": "checkbox",
                    "label": "Disable Document Validation",
                    "description": "Skip document validation checks",
                    "default": False,
                },
                "defer_embedding": {
                    "type": "checkbox",
                    "label": "Defer Embedding",
                    "description": "Defer embedding generation",
                    "default": False,
                },
                "chunking_algorithm": {
                    "type": "dropdown",
                    "label": "Chunking Algorithm",
                    "description": "Algorithm for text chunking",
                    "default": "simple_overlap",
                    "choices": ["simple_overlap", "recursive_character", "markdown"],
                },
            },
            "prompts": {
                "use_json": {
                    "type": "checkbox",
                    "label": "Use JSON",
                    "description": "Use JSON format for prompts",
                    "default": True,
                },
                "summary": {
                    "type": "textarea",
                    "label": "Summary Prompt",
                    "description": "Prompt template for summarization",
                    "default": "Summarize the following text in a concise way that is helpful for answering the user's question. Do not include information that is not relevant to the question. Do not include information that is not in the text.\n\nText: {text}\n\nSummary:",
                    "lines": 4,
                },
                "qa": {
                    "type": "textarea",
                    "label": "QA Prompt",
                    "description": "Prompt template for question answering",
                    "default": "Answer the question '{question}'\nUse the context below if helpful. You can cite the context using the key like (pqac-abcd1234). If there is insufficient context, say so.\n\nContext: {context}",
                    "lines": 4,
                },
                "select": {
                    "type": "textarea",
                    "label": "Select Prompt",
                    "description": "Prompt template for paper selection",
                    "default": "Select the most relevant papers for answering the question: {question}\n\nPapers: {papers}\n\nSelected papers:",
                    "lines": 4,
                },
                "system": {
                    "type": "textarea",
                    "label": "System Prompt",
                    "description": "System prompt for the LLM",
                    "default": "You are a helpful AI assistant that answers questions based on scientific papers. Always cite your sources using the provided citation keys.",
                    "lines": 3,
                },
            },
        }


def create_config_ui() -> gr.Blocks:
    """Create the configuration UI tab."""

    config_manager = ConfigUIManager()
    schema = config_manager.get_config_schema()

    def load_config_to_ui(config_name: str) -> tuple:
        """Load configuration and return all UI component values."""
        try:
            config = config_manager.load_config(config_name)
            return _config_to_ui_values(config, schema)
        except Exception as e:
            return tuple(
                [f"Error loading config: {str(e)}"] * 50
            )  # Return error for all fields

    def save_config_from_ui(config_name: str, *values) -> str:
        """Save configuration from UI component values."""
        try:
            config = _ui_values_to_config(values, schema)
            config_manager.save_config(config_name, config)
            return f"✅ Configuration '{config_name}' saved successfully! Please restart the server for changes to take effect."
        except Exception as e:
            return f"❌ Error saving config: {str(e)}"

    def _config_to_ui_values(config: Dict[str, Any], schema: Dict[str, Any]) -> tuple:
        """Convert config dict to UI component values."""
        values = []

        # Top-level settings
        values.extend(
            [
                config.get("llm", ""),
                config.get("summary_llm", ""),
                config.get("embedding", ""),
                config.get("temperature", 0.0),
                config.get("verbosity", 3),
            ]
        )

        # Agent settings
        agent = config.get("agent", {})
        values.extend(
            [
                agent.get("agent_llm", ""),
                agent.get("agent_type", "ToolSelector"),
                agent.get("search_count", 20),
                agent.get("timeout", 600.0),
                agent.get("should_pre_search", True),
                agent.get("wipe_context_on_answer_failure", True),
                agent.get("agent_evidence_n", 5),
                agent.get("return_paper_metadata", True),
            ]
        )

        # Agent index settings
        index = agent.get("index", {})
        values.extend(
            [
                index.get("paper_directory", "./papers"),
                index.get("index_directory", "./indexes"),
                index.get("recurse_subdirectories", True),
                index.get("concurrency", 3),
                index.get("sync_with_paper_directory", False),
            ]
        )

        # Answer settings
        answer = config.get("answer", {})
        values.extend(
            [
                answer.get("evidence_k", 20),
                answer.get("evidence_detailed_citations", True),
                answer.get("evidence_retrieval", True),
                answer.get("evidence_relevance_score_cutoff", 1),
                answer.get("evidence_summary_length", "about 150 words"),
                answer.get("evidence_skip_summary", False),
                answer.get("answer_max_sources", 15),
                answer.get("max_answer_attempts", 3),
                answer.get("answer_length", "about 500 words"),
                answer.get("max_concurrent_requests", 3),
                answer.get("answer_filter_extra_background", False),
                answer.get("get_evidence_if_no_contexts", True),
                answer.get("group_contexts_by_question", False),
            ]
        )

        # Parsing settings
        parsing = config.get("parsing", {})
        values.extend(
            [
                parsing.get("chunk_size", 5000),
                parsing.get("page_size_limit", 1280000),
                parsing.get("pdfs_use_block_parsing", False),
                parsing.get("use_doc_details", True),
                parsing.get("overlap", 250),
                parsing.get("disable_doc_valid_check", False),
                parsing.get("defer_embedding", False),
                parsing.get("chunking_algorithm", "simple_overlap"),
            ]
        )

        # Prompt settings
        prompts = config.get("prompts", {})
        values.extend(
            [
                prompts.get("use_json", True),
                prompts.get("summary", ""),
                prompts.get("qa", ""),
                prompts.get("select", ""),
                prompts.get("system", ""),
            ]
        )

        return tuple(values)

    def _ui_values_to_config(values: tuple, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert UI component values to config dict."""
        config = {}
        value_index = 0

        # Top-level settings
        config["llm"] = values[value_index]
        value_index += 1
        config["summary_llm"] = values[value_index]
        value_index += 1
        config["embedding"] = values[value_index]
        value_index += 1
        config["temperature"] = values[value_index]
        value_index += 1
        config["verbosity"] = values[value_index]
        value_index += 1

        # Agent settings
        config["agent"] = {
            "agent_llm": values[value_index],
            "agent_type": values[value_index + 1],
            "search_count": values[value_index + 2],
            "timeout": values[value_index + 3],
            "should_pre_search": values[value_index + 4],
            "wipe_context_on_answer_failure": values[value_index + 5],
            "agent_evidence_n": values[value_index + 6],
            "return_paper_metadata": values[value_index + 7],
            "index": {
                "paper_directory": values[value_index + 8],
                "index_directory": values[value_index + 9],
                "recurse_subdirectories": values[value_index + 10],
                "concurrency": values[value_index + 11],
                "sync_with_paper_directory": values[value_index + 12],
            },
        }
        value_index += 13

        # Answer settings
        config["answer"] = {
            "evidence_k": values[value_index],
            "evidence_detailed_citations": values[value_index + 1],
            "evidence_retrieval": values[value_index + 2],
            "evidence_relevance_score_cutoff": values[value_index + 3],
            "evidence_summary_length": values[value_index + 4],
            "evidence_skip_summary": values[value_index + 5],
            "answer_max_sources": values[value_index + 6],
            "max_answer_attempts": values[value_index + 7],
            "answer_length": values[value_index + 8],
            "max_concurrent_requests": values[value_index + 9],
            "answer_filter_extra_background": values[value_index + 10],
            "get_evidence_if_no_contexts": values[value_index + 11],
            "group_contexts_by_question": values[value_index + 12],
        }
        value_index += 13

        # Parsing settings
        config["parsing"] = {
            "chunk_size": values[value_index],
            "page_size_limit": values[value_index + 1],
            "pdfs_use_block_parsing": values[value_index + 2],
            "use_doc_details": values[value_index + 3],
            "overlap": values[value_index + 4],
            "disable_doc_valid_check": values[value_index + 5],
            "defer_embedding": values[value_index + 6],
            "chunking_algorithm": values[value_index + 7],
        }
        value_index += 8

        # Prompt settings
        config["prompts"] = {
            "use_json": values[value_index],
            "summary": values[value_index + 1],
            "qa": values[value_index + 2],
            "select": values[value_index + 3],
            "system": values[value_index + 4],
        }
        value_index += 5

        return config

    # Create UI components
    with gr.Blocks(title="Paper-QA Configuration") as config_ui:
        gr.HTML(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1>⚙️ Paper-QA Configuration</h1>
                <p>Configure all settings for Paper-QA. Changes require server restart to take effect.</p>
            </div>
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                config_dropdown = gr.Dropdown(
                    choices=config_manager.get_available_configs(),
                    value="default",
                    label="Configuration File",
                    info="Select which configuration file to edit",
                )

                load_btn = gr.Button("📂 Load Configuration", variant="secondary")
                save_btn = gr.Button("💾 Save Configuration", variant="primary")

                status_output = gr.Textbox(
                    label="Status",
                    interactive=False,
                    value="Select a configuration file and click 'Load Configuration' to begin editing.",
                )

            with gr.Column(scale=3):
                # Top-level settings
                with gr.Group():
                    gr.Markdown("### 🔧 General Settings")

                    with gr.Row():
                        llm_input = gr.Textbox(
                            label="LLM Model",
                            value="openrouter/google/gemini-2.5-flash-lite",
                            info="The LLM model to use for answering questions",
                        )
                        summary_llm_input = gr.Textbox(
                            label="Summary LLM Model",
                            value="openrouter/google/gemini-2.5-flash-lite",
                            info="The LLM model to use for summarization",
                        )

                    with gr.Row():
                        embedding_input = gr.Textbox(
                            label="Embedding Model",
                            value="ollama/nomic-embed-text",
                            info="The embedding model to use for vector search",
                        )
                        temperature_input = gr.Slider(
                            label="Temperature",
                            value=0.0,
                            minimum=0.0,
                            maximum=2.0,
                            step=0.1,
                            info="Controls randomness in LLM responses",
                        )

                    verbosity_input = gr.Slider(
                        label="Verbosity Level",
                        value=3,
                        minimum=0,
                        maximum=5,
                        step=1,
                        info="Logging verbosity level",
                    )

                # Agent settings
                with gr.Group():
                    gr.Markdown("### 🤖 Agent Settings")

                    with gr.Row():
                        agent_llm_input = gr.Textbox(
                            label="Agent LLM Model",
                            value="openrouter/google/gemini-2.5-flash-lite",
                            info="The LLM model for the agent",
                        )
                        agent_type_input = gr.Dropdown(
                            choices=["ToolSelector", "Task"],
                            value="ToolSelector",
                            label="Agent Type",
                            info="Type of agent to use",
                        )

                    with gr.Row():
                        search_count_input = gr.Number(
                            label="Search Count",
                            value=20,
                            minimum=1,
                            maximum=100,
                            step=1,
                            info="Number of papers to search for",
                        )
                        timeout_input = gr.Number(
                            label="Timeout (seconds)",
                            value=600.0,
                            minimum=30.0,
                            maximum=3600.0,
                            step=30.0,
                            info="Agent execution timeout",
                        )

                    with gr.Row():
                        should_pre_search_input = gr.Checkbox(
                            label="Pre-search",
                            value=True,
                            info="Run search tool before invoking agent",
                        )
                        wipe_context_input = gr.Checkbox(
                            label="Wipe Context on Failure",
                            value=True,
                            info="Clear context when answer generation fails",
                        )

                    with gr.Row():
                        agent_evidence_n_input = gr.Number(
                            label="Agent Evidence Count",
                            value=5,
                            minimum=1,
                            maximum=50,
                            step=1,
                            info="Number of evidence pieces for agent",
                        )
                        return_metadata_input = gr.Checkbox(
                            label="Return Paper Metadata",
                            value=True,
                            info="Include paper metadata in results",
                        )

                # Index settings
                with gr.Group():
                    gr.Markdown("### 📁 Index Settings")

                    with gr.Row():
                        paper_dir_input = gr.Textbox(
                            label="Paper Directory",
                            value="./papers",
                            info="Directory containing papers to index",
                        )
                        index_dir_input = gr.Textbox(
                            label="Index Directory",
                            value="./indexes",
                            info="Directory to store indexes",
                        )

                    with gr.Row():
                        recurse_input = gr.Checkbox(
                            label="Recurse Subdirectories",
                            value=True,
                            info="Search subdirectories for papers",
                        )
                        sync_input = gr.Checkbox(
                            label="Sync with Paper Directory",
                            value=False,
                            info="Keep index synchronized with paper directory",
                        )

                    concurrency_input = gr.Number(
                        label="Concurrency",
                        value=3,
                        minimum=1,
                        maximum=10,
                        step=1,
                        info="Number of concurrent filesystem reads",
                    )

                # Answer settings
                with gr.Group():
                    gr.Markdown("### 📝 Answer Settings")

                    with gr.Row():
                        evidence_k_input = gr.Number(
                            label="Evidence K",
                            value=20,
                            minimum=1,
                            maximum=100,
                            step=1,
                            info="Number of evidence pieces to retrieve",
                        )
                        evidence_cutoff_input = gr.Number(
                            label="Relevance Score Cutoff",
                            value=1,
                            minimum=0,
                            maximum=10,
                            step=0.1,
                            info="Minimum relevance score for evidence",
                        )

                    with gr.Row():
                        evidence_citations_input = gr.Checkbox(
                            label="Detailed Citations",
                            value=True,
                            info="Include detailed citation information",
                        )
                        evidence_retrieval_input = gr.Checkbox(
                            label="Evidence Retrieval",
                            value=True,
                            info="Enable evidence retrieval",
                        )

                    evidence_summary_length_input = gr.Textbox(
                        label="Evidence Summary Length",
                        value="about 150 words",
                        info="Length of evidence summaries",
                    )

                    evidence_skip_summary_input = gr.Checkbox(
                        label="Skip Evidence Summary",
                        value=False,
                        info="Skip generating evidence summaries",
                    )

                    with gr.Row():
                        max_sources_input = gr.Number(
                            label="Max Sources",
                            value=15,
                            minimum=1,
                            maximum=50,
                            step=1,
                            info="Maximum number of sources in answer",
                        )
                        max_attempts_input = gr.Number(
                            label="Max Answer Attempts",
                            value=3,
                            minimum=1,
                            maximum=10,
                            step=1,
                            info="Maximum attempts to generate answer",
                        )

                    answer_length_input = gr.Textbox(
                        label="Answer Length",
                        value="about 500 words",
                        info="Target length for answers",
                    )

                    max_concurrent_input = gr.Number(
                        label="Max Concurrent Requests",
                        value=3,
                        minimum=1,
                        maximum=10,
                        step=1,
                        info="Maximum concurrent API requests",
                    )

                    with gr.Row():
                        filter_background_input = gr.Checkbox(
                            label="Filter Extra Background",
                            value=False,
                            info="Filter out extra background information",
                        )
                        get_evidence_input = gr.Checkbox(
                            label="Get Evidence if No Contexts",
                            value=True,
                            info="Retrieve evidence even if no contexts found",
                        )

                    group_contexts_input = gr.Checkbox(
                        label="Group Contexts by Question",
                        value=False,
                        info="Group contexts by their associated question",
                    )

                # Parsing settings
                with gr.Group():
                    gr.Markdown("### 📄 Parsing Settings")

                    with gr.Row():
                        chunk_size_input = gr.Number(
                            label="Chunk Size",
                            value=5000,
                            minimum=1000,
                            maximum=10000,
                            step=500,
                            info="Size of text chunks for processing",
                        )
                        page_limit_input = gr.Number(
                            label="Page Size Limit",
                            value=1280000,
                            minimum=100000,
                            maximum=5000000,
                            step=100000,
                            info="Maximum page size for processing",
                        )

                    with gr.Row():
                        block_parsing_input = gr.Checkbox(
                            label="PDF Block Parsing",
                            value=False,
                            info="Use block parsing for PDFs",
                        )
                        doc_details_input = gr.Checkbox(
                            label="Use Document Details",
                            value=True,
                            info="Include document details in processing",
                        )

                    overlap_input = gr.Number(
                        label="Overlap",
                        value=250,
                        minimum=0,
                        maximum=1000,
                        step=50,
                        info="Overlap between text chunks",
                    )

                    with gr.Row():
                        disable_valid_input = gr.Checkbox(
                            label="Disable Document Validation",
                            value=False,
                            info="Skip document validation checks",
                        )
                        defer_embedding_input = gr.Checkbox(
                            label="Defer Embedding",
                            value=False,
                            info="Defer embedding generation",
                        )

                    chunking_algorithm_input = gr.Dropdown(
                        choices=["simple_overlap", "recursive_character", "markdown"],
                        value="simple_overlap",
                        label="Chunking Algorithm",
                        info="Algorithm for text chunking",
                    )

                # Prompt settings
                with gr.Group():
                    gr.Markdown("### 💬 Prompt Settings")

                    use_json_input = gr.Checkbox(
                        label="Use JSON", value=True, info="Use JSON format for prompts"
                    )

                    summary_prompt_input = gr.Textbox(
                        label="Summary Prompt",
                        value="Summarize the following text in a concise way that is helpful for answering the user's question. Do not include information that is not relevant to the question. Do not include information that is not in the text.\n\nText: {text}\n\nSummary:",
                        lines=4,
                        info="Prompt template for summarization",
                    )

                    qa_prompt_input = gr.Textbox(
                        label="QA Prompt",
                        value="Answer the question '{question}'\nUse the context below if helpful. You can cite the context using the key like (pqac-abcd1234). If there is insufficient context, say so.\n\nContext: {context}",
                        lines=4,
                        info="Prompt template for question answering",
                    )

                    select_prompt_input = gr.Textbox(
                        label="Select Prompt",
                        value="Select the most relevant papers for answering the question: {question}\n\nPapers: {papers}\n\nSelected papers:",
                        lines=4,
                        info="Prompt template for paper selection",
                    )

                    system_prompt_input = gr.Textbox(
                        label="System Prompt",
                        value="You are a helpful AI assistant that answers questions based on scientific papers. Always cite your sources using the provided citation keys.",
                        lines=3,
                        info="System prompt for the LLM",
                    )

        # Event handlers
        load_btn.click(
            fn=load_config_to_ui,
            inputs=[config_dropdown],
            outputs=[
                llm_input,
                summary_llm_input,
                embedding_input,
                temperature_input,
                verbosity_input,
                agent_llm_input,
                agent_type_input,
                search_count_input,
                timeout_input,
                should_pre_search_input,
                wipe_context_input,
                agent_evidence_n_input,
                return_metadata_input,
                paper_dir_input,
                index_dir_input,
                recurse_input,
                concurrency_input,
                sync_input,
                evidence_k_input,
                evidence_citations_input,
                evidence_retrieval_input,
                evidence_cutoff_input,
                evidence_summary_length_input,
                evidence_skip_summary_input,
                max_sources_input,
                max_attempts_input,
                answer_length_input,
                max_concurrent_input,
                filter_background_input,
                get_evidence_input,
                group_contexts_input,
                chunk_size_input,
                page_limit_input,
                block_parsing_input,
                doc_details_input,
                overlap_input,
                disable_valid_input,
                defer_embedding_input,
                chunking_algorithm_input,
                use_json_input,
                summary_prompt_input,
                qa_prompt_input,
                select_prompt_input,
                system_prompt_input,
            ],
        )

        save_btn.click(
            fn=save_config_from_ui,
            inputs=[
                config_dropdown,
                llm_input,
                summary_llm_input,
                embedding_input,
                temperature_input,
                verbosity_input,
                agent_llm_input,
                agent_type_input,
                search_count_input,
                timeout_input,
                should_pre_search_input,
                wipe_context_input,
                agent_evidence_n_input,
                return_metadata_input,
                paper_dir_input,
                index_dir_input,
                recurse_input,
                concurrency_input,
                sync_input,
                evidence_k_input,
                evidence_citations_input,
                evidence_retrieval_input,
                evidence_cutoff_input,
                evidence_summary_length_input,
                evidence_skip_summary_input,
                max_sources_input,
                max_attempts_input,
                answer_length_input,
                max_concurrent_input,
                filter_background_input,
                get_evidence_input,
                group_contexts_input,
                chunk_size_input,
                page_limit_input,
                block_parsing_input,
                doc_details_input,
                overlap_input,
                disable_valid_input,
                defer_embedding_input,
                chunking_algorithm_input,
                use_json_input,
                summary_prompt_input,
                qa_prompt_input,
                select_prompt_input,
                system_prompt_input,
            ],
            outputs=[status_output],
        )

    return config_ui
