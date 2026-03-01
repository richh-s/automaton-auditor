"""
ChiefJusticeNode: Deterministic conflict resolution and synthesis.

This module contains the ChiefJustice node that synthesizes all judicial opinions
into a final AuditReport using hardcoded deterministic rules:
  - Security Override: SECURITY conflicts cap dimension score at 3
  - Fact Supremacy: FACTCHECK conflicts override Defense score to 1
  - TechLead Authority: TechLead is sole authority on graph_orchestration when >= 4
  - Dissent Requirement: Mandatory dissent_summary when score spread > 2
  - Round-Half-Up: Uses Decimal(ROUND_HALF_UP) to avoid banker's rounding

The final AuditReport is serialized to Markdown via report_writer.py.
"""

import json
from typing import List
from decimal import Decimal, ROUND_HALF_UP

from src.state import AgentState, JudicialOpinion, CriterionResult, AuditReport, ConflictEntry


def ChiefJusticeNode(state: AgentState):
    """
    The Final Authority: Synthesizes opinions using a deterministic,
    rule-driven scoring pipeline.
    
    Pipeline:
      1. Hard Caps (SECURITY override, FACTCHECK penalty)
      2. Authoritative Score (TechLead dominance on architecture)
      3. Weighted Fallback (TL*0.4 + P*0.3 + D*0.3)
      4. Clamp & Round (Decimal ROUND_HALF_UP, integer 1-5)
    
    Produces an AuditReport which gets serialized to Markdown as the
    final_report in AgentState.
    """
    print("--- SUPREME COURT: CHIEF JUSTICE ---")
    
    conflicts = state.get("conflict_log", [])
    criteria_results = []
    dimension_scores = {}
    
    for dim in state["rubric_dimensions"]:
        dim_id = dim["id"]
        dim_ops = [o for o in state["opinions"] if o.criterion_id == dim_id]
        
        if not dim_ops:
            continue
            
        p_op = next((o for o in dim_ops if o.judge == "Prosecutor"), None)
        d_op = next((o for o in dim_ops if o.judge == "Defense"), None)
        t_op = next((o for o in dim_ops if o.judge == "TechLead"), None)
        
        p_score = p_op.score if p_op else 1
        d_score = d_op.score if d_op else 1
        t_score = t_op.score if t_op else 1

        # --- Step 1: Hard Caps & Overrides ---
        security_capped = False
        dim_security = [c for c in conflicts if c.tag == "SECURITY" and c.dimension_id == dim_id]
        dim_factcheck = [c for c in conflicts if c.tag == "FACTCHECK" and c.dimension_id == dim_id]

        if dim_security:
            security_capped = True  # Will cap after scoring

        if dim_factcheck:
            d_score = 1  # Hallucination penalty: Defense is overruled

        # --- Step 2: Authoritative Score (dimension-specific) ---
        score = None
        if dim_id == "graph_orchestration" and t_score >= 4:
            score = float(t_score)  # TechLead is sole authority for architecture

        # --- Step 3: Weighted Fallback (only if no authoritative rule applied) ---
        if score is None:
            score = (t_score * 0.4) + (p_score * 0.3) + (d_score * 0.3)

        # Apply security cap after scoring
        if security_capped:
            score = min(score, 3.0)

        # --- Step 4: Clamping & Rounding (Decimal ROUND_HALF_UP) ---
        score = float(Decimal(str(score)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        score = max(1.0, min(5.0, score))
        final_score = int(score)

        # --- Dissent Detection (symmetric: max - min across all 3 judges) ---
        all_scores = [p_score, d_score, t_score]
        variance = max(all_scores) - min(all_scores)
        dissent = None
        if variance > 2:
            high_judge = max(dim_ops, key=lambda o: o.score)
            low_judge = min(dim_ops, key=lambda o: o.score)
            dissent = (
                f"Major disagreement (spread={variance}): "
                f"{high_judge.judge} ({high_judge.score}/5) vs "
                f"{low_judge.judge} ({low_judge.score}/5). "
                f"High: {high_judge.argument[:80]}... "
                f"Low: {low_judge.argument[:80]}..."
            )

        criteria_results.append(CriterionResult(
            dimension_id=dim_id,
            dimension_name=dim["name"],
            final_score=final_score,
            judge_opinions=dim_ops,
            dissent_summary=dissent,
            remediation=t_op.argument if t_op else "Follow success pattern."
        ))
        dimension_scores[dim_id] = final_score

    # --- Overall Score ---
    overall_score = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0.0
    
    # Global security override: any security conflict caps total at 3
    global_security = [c for c in conflicts if c.tag == "SECURITY"]
    if global_security:
        overall_score = min(3.0, overall_score)

    report = AuditReport(
        repo_url=state["repo_url"],
        executive_summary=f"Forensic audit complete. {len(criteria_results)} dimensions evaluated, {len(conflicts)} conflicts detected.",
        overall_score=float(overall_score),
        criteria=criteria_results,
        remediation_plan=_build_remediation_plan(criteria_results)
    )
    
    return {"final_report": report}


def _build_remediation_plan(criteria: List[CriterionResult]) -> str:
    """
    Aggregates remediation steps: grouped by severity (lowest score first),
    deduplicated.
    """
    sorted_criteria = sorted(criteria, key=lambda c: c.final_score)
    seen = set()
    lines = []
    for c in sorted_criteria:
        if c.remediation and c.remediation not in seen:
            seen.add(c.remediation)
            lines.append(f"- **[{c.dimension_name}]** (Score: {c.final_score}/5): {c.remediation}")
    return "\n".join(lines) if lines else "No specific remediation required."
