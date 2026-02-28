import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState, JudicialOpinion, CriterionResult, AuditReport, ConflictEntry
from typing import List
from decimal import Decimal, ROUND_HALF_UP

# --- Judicial Layer (Phas 3) ---

def Prosecutor(state: AgentState):
    """
    The Pessimist: Scans for gaps, security flaws, and iterative failures.
    """
    print("--- JUDGE: PROSECUTOR (Adversarial) ---")
    llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(JudicialOpinion)
    
    opinions = []
    for dim in state["rubric_dimensions"]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Prosecutor Auditor. Your goal is to find weakness and technical debt. "
                       "Be adversarial. Look for laziness, security flaws, and gaps. "
                       "Rubric Criterion: {name}\nSuccess Pattern: {success}\nFailure Pattern: {failure}"),
            ("user", "Evidence Found: {evidences}")
        ])
        
        # Filter evidence for this dimension
        relevant_ev = [e.model_dump() for sublist in state["evidences"].values() for e in sublist if e.goal in dim["name"] or dim["target_artifact"] in e.location]
        
        chain = prompt | llm
        opinion = chain.invoke({
            "name": dim["name"],
            "success": dim["success_pattern"],
            "failure": dim.get("failure_pattern", "None"),
            "evidences": json.dumps(relevant_ev)
        })
        opinion.judge = "Prosecutor"
        opinion.criterion_id = dim["id"]
        opinions.append(opinion)
    
    return {"opinions": opinions}

def Defense(state: AgentState):
    """
    The Optimist: Rewards intent, modularity, and creative workarounds.
    """
    print("--- JUDGE: DEFENSE (Optimist) ---")
    llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(JudicialOpinion)
    
    opinions = []
    for dim in state["rubric_dimensions"]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Defense Attorney Auditor. Highlight strengths and viable workarounds. "
                       "Reward effort, intent, and progress. "
                       "Rubric Criterion: {name}\nSuccess Pattern: {success}\nFailure Pattern: {failure}"),
            ("user", "Evidence Found: {evidences}")
        ])
        
        relevant_ev = [e.model_dump() for sublist in state["evidences"].values() for e in sublist if e.goal in dim["name"] or dim["target_artifact"] in e.location]
        
        chain = prompt | llm
        opinion = chain.invoke({
            "name": dim["name"],
            "success": dim["success_pattern"],
            "failure": dim.get("failure_pattern", "None"),
            "evidences": json.dumps(relevant_ev)
        })
        opinion.judge = "Defense"
        opinion.criterion_id = dim["id"]
        opinions.append(opinion)
    
    return {"opinions": opinions}

def TechLead(state: AgentState):
    """
    The Arbiter: Focused on architectural soundness and practical viability.
    """
    print("--- JUDGE: TECH LEAD (Pragmatic) ---")
    llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(JudicialOpinion)
    
    opinions = []
    for dim in state["rubric_dimensions"]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the Tech Lead Auditor. Focus on technical soundness and maintainability. "
                       "Be pragmatic. Provide the 'Ground Truth' technical verdict. "
                       "Rubric Criterion: {name}\nSuccess Pattern: {success}\nFailure Pattern: {failure}"),
            ("user", "Evidence Found: {evidences}")
        ])
        
        relevant_ev = [e.model_dump() for sublist in state["evidences"].values() for e in sublist if e.goal in dim["name"] or dim["target_artifact"] in e.location]
        
        chain = prompt | llm
        opinion = chain.invoke({
            "name": dim["name"],
            "success": dim["success_pattern"],
            "failure": dim.get("failure_pattern", "None"),
            "evidences": json.dumps(relevant_ev)
        })
        opinion.judge = "TechLead"
        opinion.criterion_id = dim["id"]
        opinions.append(opinion)
    
    return {"opinions": opinions}

def ChiefJustice(state: AgentState):
    """
    The Final Authority: Synthesizes opinions using a deterministic,
    rule-driven scoring pipeline.
    Pipeline: Hard Caps -> Authoritative Score -> Weighted Fallback -> Clamp
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


def EvidenceAggregator(state: AgentState):
    """
    The Forensic Firewall (Fan-In): Synchronizes findings and identifies
    hallucinations BEFORE judges see the evidence.
    Emits structured ConflictEntry objects with dimension-level links.
    """
    print("--- EVIDENCE AGGREGATOR (Metacognitive Barrier) ---")
    
    repo_ev = state["evidences"].get("repo", [])
    doc_ev = state["evidences"].get("doc", [])
    
    conflicts = []
    
    # --- Fact-Check: Cross-reference doc claims against repo evidence ---
    for doc_e in doc_ev:
        # Find matching repo evidence by goal
        repo_match = next(
            (r for r in repo_ev if r.goal == doc_e.goal),
            None
        )
        if doc_e.found and (not repo_match or not repo_match.found):
            # Map goal to dimension_id
            dim_id = _goal_to_dimension_id(doc_e.goal, state.get("rubric_dimensions", []))
            conflicts.append(ConflictEntry(
                tag="FACTCHECK",
                dimension_id=dim_id,
                message=f"PDF claims '{doc_e.goal}' but RepoInvestigator found NO supporting evidence."
            ))
    
    # --- Security Check: Flag unsafe tool usage ---
    for ev in repo_ev:
        if ev.goal == "Safe Tool Engineering" and ev.found:
            # Check if the evidence itself reports unsafe patterns
            if ev.rationale and ("os.system" in ev.rationale.lower() or "unsafe" in ev.rationale.lower()):
                conflicts.append(ConflictEntry(
                    tag="SECURITY",
                    dimension_id="safe_tool_engineering",
                    message=f"Security risk detected: {ev.rationale[:200]}"
                ))

    return {"conflict_log": conflicts}


def _goal_to_dimension_id(goal: str, dimensions: list) -> str:
    """
    Maps a goal string (dimension name) to its dimension_id.
    Falls back to a slugified version of the goal.
    """
    for dim in dimensions:
        if dim["name"] == goal:
            return dim["id"]
    # Fallback: slugify
    return goal.lower().replace(" ", "_")
