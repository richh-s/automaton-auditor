import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState, JudicialOpinion, CriterionResult, AuditReport
from typing import List

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
    The Final Authority: Synthesizes opinions using Forensic Synthesis Rules.
    (Weighted Arbitration, Security Overrides, Hallucination Penalties)
    """
    print("--- SUPREME COURT: CHIEF JUSTICE ---")
    
    rules = state["synthesis_rules"]
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

        # Rule: Functionality Weight (Tech Lead carries highest weight if modular)
        # We'll use 40% Tech Lead, 30% Prosecutor, 30% Defense
        score = (t_score * 0.4) + (p_score * 0.3) + (d_score * 0.3)
        
        # Rule: Fact Supremacy (Check for hallucinations in opinions)
        # If Defense claims something found but detectives log a conflict...
        dim_conflicts = [c for c in conflicts if dim["name"] in c or dim["id"] in c]
        if dim_conflicts:
            score -= 1.0 # Fact-check penalty
        
        # Rule: Dissent Requirement (Variance > 2)
        dissent = None
        if p_op and d_op and abs(p_op.score - d_op.score) > 2:
            dissent = f"Major disagreement: Prosecutor ({p_op.score}) vs Defense ({d_op.score}). {p_op.argument[:50]}... vs {d_op.argument[:50]}..."

        criteria_results.append(CriterionResult(
            dimension_id=dim_id,
            dimension_name=dim["name"],
            final_score=int(max(1, min(5, score))),
            judge_opinions=dim_ops,
            dissent_summary=dissent,
            remediation=t_op.argument if t_op else "Follow success pattern."
        ))
        dimension_scores[dim_id] = score

    overall_score = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0
    
    # Rule: Security Override (Confirmed flaws cap total score at 3)
    security_flaws = [c for c in conflicts if "Safe" in c or "Security" in c]
    if security_flaws:
        overall_score = min(3.0, overall_score)

    report = AuditReport(
        repo_url=state["repo_url"],
        executive_summary=f"Forensic audit complete with {len(conflicts)} detected conflicts.",
        overall_score=float(overall_score),
        criteria=criteria_results,
        remediation_plan="Resolve security overrides and align report claims with AST truth."
    )
    
    return {"final_report": report}

def EvidenceAggregator(state: AgentState):
    """
    The Forensic Firewall (Fan-In): Synchronizes findings and identifies 
    hallucinations BEFORE judges see the evidence.
    """
    print("--- EVIDENCE AGGREGATOR (Metacognitive Barrier) ---")
    
    repo_ev = state["evidences"].get("repo", [])
    doc_ev = state["evidences"].get("doc", [])
    
    conflicts = []
    
    # Authority Rule: StateGraph Check
    doc_claim = next((e for e in doc_ev if "Graph" in e.goal or "Architecture" in e.goal), None)
    repo_fact = next((e for e in repo_ev if "Graph" in e.goal or "Parallelism" in e.goal), None)
    
    if doc_claim and doc_claim.found and (not repo_fact or not repo_fact.found):
        conflicts.append(f"Fact-Check Failure: Doc claims '{doc_claim.goal}' but RepoInvestigator found NO evidence.")

    return {"conflict_log": conflicts}
