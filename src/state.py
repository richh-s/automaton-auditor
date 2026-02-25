import operator
from typing import Annotated, Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# --- Detective Output ---


class Evidence(BaseModel):
    """
    Structured forensic evidence collected by detective agents.
    """
    goal: str = Field(description="The specific forensic objective being verified")
    found: bool = Field(description="Whether the targeted artifact or pattern exists")
    content: Optional[str] = Field(default=None, description="Snippets or raw data extracted for proof")
    location: str = Field(description="File path, line number, or git commit hash")
    rationale: str = Field(description="Step-by-step reasoning for the finding")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured forensic metadata (AST types, git timestamps, etc.)",
    )


# --- Judge Output ---


class JudicialOpinion(BaseModel):
    """
    Synthesized judgment on a specific rubric criterion.
    """
    judge: Literal["Prosecutor", "Defense", "TechLead"] = Field(description="The persona providing the opinion")
    criterion_id: str = Field(description="The ID of the rubric dimension being evaluated")
    score: int = Field(ge=1, le=5, description="Score on a 1-5 scale per rubric guidelines")
    argument: str = Field(description="Detailed justification for the assigned score")
    cited_evidence: List[str] = Field(description="List of Evidence goal names supported this judgment")


# --- Chief Justice Output ---


class CriterionResult(BaseModel):
    """
    Final consensus result for a specific dimension.
    """
    dimension_id: str = Field(description="The ID of the dimension")
    dimension_name: str = Field(description="Human-readable name of the dimension")
    final_score: int = Field(ge=1, le=5, description="The weighted average score")
    judge_opinions: List[JudicialOpinion] = Field(description="Collection of opinions from the parallel judicial swarm")
    dissent_summary: Optional[str] = Field(
        default=None,
        description="Detailed explanation of score variance if threshold is exceeded",
    )
    remediation: str = Field(
        description="Actionable technical steps to improve the score",
    )


class AuditReport(BaseModel):
    """
    The final forensic audit report.
    """
    repo_url: str = Field(description="The URL of the target repository")
    executive_summary: str = Field(description="High-level overview of the audit findings")
    overall_score: float = Field(description="Aggregated score across all dimensions")
    criteria: List[CriterionResult] = Field(description="Breakdown of results by dimension")
    remediation_plan: str = Field(description="Comprehensive technical roadmap for fixes")


# --- Graph State ---


class AgentState(TypedDict):
    """
    The global state container for the Automaton Auditor graph.
    Designed for safe parallel execution using commutitave reducers.
    """
    repo_url: str # Target URL
    pdf_path: str # Path to report.pdf
    rubric_dimensions: List[Dict] # Collection of evaluation criteria
    
    # eviences uses operator.ior (dict merge) to allow multiple nodes
    # to contribute to different keys without overwriting each other.
    evidences: Annotated[
        Dict[str, List[Evidence]], operator.ior
    ]
    
    # opinions and conflict_log use operator.add (list append)
    # ensuring all parallel branch outputs are collected.
    opinions: Annotated[
        List[JudicialOpinion], operator.add
    ]
    conflict_log: Annotated[
        List[str], operator.add
    ]
    
    final_report: AuditReport
