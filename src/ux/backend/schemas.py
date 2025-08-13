from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Filters(BaseModel):
    years: Optional[List[int]] = None
    venues: Optional[List[str]] = None
    fields: Optional[List[str]] = None


class RewriteRequest(BaseModel):
    original: str = Field(..., description="Original user question")
    use_llm: bool = Field(True, description="Use LLM-based rewrite when available")


class RewriteResponse(BaseModel):
    rewritten: str
    filters: Filters = Field(default_factory=Filters)
    same_as_original: bool = False


class CurationSpec(BaseModel):
    relevance_cutoff: float = Field(0.0, ge=0.0, le=1.0)
    per_doc_cap: Optional[int] = Field(None, ge=1)
    max_sources: Optional[int] = Field(None, ge=1)


class RunMode(str, Enum):
    bias = "bias"
    hard = "hard"


class RunRequest(BaseModel):
    question: str
    settings_name: Optional[str] = Field(
        default="optimized_ollama", description="Name of JSON in configs/"
    )
    files: Optional[List[str]] = None
    rewrite: Optional[RewriteResponse] = None
    mode: RunMode = RunMode.bias
    curation: CurationSpec = Field(default_factory=CurationSpec)
    stream_answer: bool = True


class PhaseName(str, Enum):
    retrieval = "retrieval"
    summaries = "summaries"
    answer = "answer"


class PhaseStatus(str, Enum):
    start = "start"
    end = "end"


class Event(BaseModel):
    type: str
    data: Dict[str, Any]
    ts_ms: Optional[int] = None


class PhaseEvent(Event):
    type: Literal["phase"] = "phase"
    data: Dict[str, Any]  # {phase: PhaseName, status: PhaseStatus}


class MetricEvent(Event):
    type: Literal["metric"] = "metric"
    data: Dict[str, Any]  # e.g., {contexts_selected, evidence_k, elapsed_s}


class LogEvent(Event):
    type: Literal["log"] = "log"
    data: Dict[str, Any]  # {message}


class AnswerEvent(Event):
    type: Literal["answer"] = "answer"
    data: Dict[str, Any]  # {markdown}


class SessionSummary(BaseModel):
    question: str
    rewritten: Optional[str] = None
    filters: Optional[Filters] = None
    curation: CurationSpec
    answer_markdown: Optional[str] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class ExportBundle(BaseModel):
    session: SessionSummary
    trace: List[Event] = Field(default_factory=list)
