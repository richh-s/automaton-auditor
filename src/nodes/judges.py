import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState, JudicialOpinion, CriterionResult, AuditReport
from typing import List

# --- Judicial Layer (Phas 3) ---

def Prosecutor(state: AgentState):
    """
    The Pessimist: Looks for failures, violations, and spaghetti code.
    """
    print("--- JUDGE: PROSECUTOR (Pessimist) ---")
    llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(JudicialOpinion)
    
    # Load rubric
    with open("rubric.json", "r") as f:
        rubric = json.load(f)
    
    # For simplicity in this interim implementation, we'll judge the first dimension
    dim = rubric["dimensions"][0]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Prosecutor Auditor. Your goal is to find weakness in the implementation. "
                   "Use the provided evidence. Rubric: {rubric_item}"),
        ("user", "Evidence: {evidences}")
    ])
    
    # Serialize evidences (Pydantic objects) for LLM
    serializable_evidences = {
        k: [e.model_dump() for e in v] for k, v in state["evidences"].items()
    }
    
    chain = prompt | llm
    opinion = chain.invoke({
        "rubric_item": json.dumps(dim),
        "evidences": json.dumps(serializable_evidences)
    })
    
    return {"opinions": [opinion]}

def Defense(state: AgentState):
    """
    The Optimist: Highlights strengths, modularity, and compliance.
    """
    print("--- JUDGE: DEFENSE (Optimist) ---")
    llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(JudicialOpinion)
    
    with open("rubric.json", "r") as f:
        rubric = json.load(f)
    
    dim = rubric["dimensions"][0]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a Defense Attorney Auditor. Highlight the BEST parts of the code. "
                   "Rubric: {rubric_item}"),
        ("user", "Evidence: {evidences}")
    ])
    
    # Serialize evidences (Pydantic objects) for LLM
    serializable_evidences = {
        k: [e.model_dump() for e in v] for k, v in state["evidences"].items()
    }
    
    chain = prompt | llm
    opinion = chain.invoke({
        "rubric_item": json.dumps(dim),
        "evidences": json.dumps(serializable_evidences)
    })
    
    return {"opinions": [opinion]}

def TechLead(state: AgentState):
    """
    The Arbiter: Resolves conflicts and provides technical remediation.
    """
    print("--- JUDGE: TECH LEAD (Arbiter) ---")
    llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(JudicialOpinion)
    
    with open("rubric.json", "r") as f:
        rubric = json.load(f)
    
    dim = rubric["dimensions"][0]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are the Tech Lead. Synthesize the evidence and provide a balanced judgment. "
                   "Rubric: {rubric_item}"),
        ("user", "Evidence: {evidences}")
    ])
    
    # Serialize evidences (Pydantic objects) for LLM
    serializable_evidences = {
        k: [e.model_dump() for e in v] for k, v in state["evidences"].items()
    }
    
    chain = prompt | llm
    opinion = chain.invoke({
        "rubric_item": json.dumps(dim),
        "evidences": json.dumps(serializable_evidences)
    })
    
    return {"opinions": [opinion]}

def ChiefJustice(state: AgentState):
    """
    Synthesizes all opinions into a final AuditReport.
    """
    print("--- SUPREME COURT: CHIEF JUSTICE ---")
    # For now, a deterministic synthesis or a small LLM call
    # We'll use the opinions to build the final report
    
    # Mock synthesis for interim
    report = AuditReport(
        repo_url=state["repo_url"],
        executive_summary="Forensic audit complete. See criteria breakdown.",
        overall_score=sum(o.score for o in state["opinions"]) / len(state["opinions"]) if state["opinions"] else 0,
        criteria=[
            CriterionResult(
                dimension_id="graph_architecture",
                dimension_name="StateGraph Architecture",
                final_score=state["opinions"][-1].score if state["opinions"] else 1,
                judge_opinions=state["opinions"],
                remediation="Adopt more modular state machines."
            )
        ],
        remediation_plan="Implement Phase 3 fully."
    )
    
    return {"final_report": report}

def EvidenceAggregator(state: AgentState):
    """
    Synchronization node (Fan-In).
    Ensures all detectives have finished.
    """
    print("--- EVIDENCE AGGREGATOR (Fan-In) ---")
    return state
