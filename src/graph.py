from langgraph.graph import StateGraph, END, START
from src.state import AgentState

# --- Detective Layer (Forensic Sub-Agents) ---

def repo_investigator(state: AgentState):
    """Forensic code analysis."""
    print("--- REPO INVESTIGATOR ---")
    # In a real scenario, this would populate state["evidences"]
    return {"evidences": {"repo": []}}

def doc_analyst(state: AgentState):
    """Forensic document analysis."""
    print("--- DOC ANALYST ---")
    return {"evidences": {"doc": []}}

def vision_inspector(state: AgentState):
    """Forensic diagram analysis (Symmetry placeholder for Phase 2)."""
    print("--- VISION INSPECTOR (Preserving Orchestration Symmetry) ---")
    return {"evidences": {"vision": []}}

# --- Synchronization & Metacognitive Validation ---

def evidence_aggregator(state: AgentState):
    """
    Fan-in node to synchronize evidence and perform metacognitive validation.
    Verifies completeness and flags missing evidence dimensions.
    """
    print("--- EVIDENCE AGGREGATOR (Metacognitive Validation) ---")
    
    expected_keys = {"repo", "doc", "vision"}
    actual_keys = set(state["evidences"].keys())
    
    missing = expected_keys - actual_keys
    if missing:
        print(f"FAILED: Metacognitive check - Missing evidence dimensions: {missing}")
        # In a real scenario, this would trigger a retry or flag for the Judge
    else:
        print("PASSED: Metacognitive check - All forensic dimensions synchronized.")
        
    return state

# --- Graph Construction ---

def create_graph():
    builder = StateGraph(AgentState)

    # Add Detective Nodes
    builder.add_node("repo_investigator", repo_investigator)
    builder.add_node("doc_analyst", doc_analyst)
    builder.add_node("vision_inspector", vision_inspector)
    
    # Add Aggregator Node
    builder.add_node("evidence_aggregator", evidence_aggregator)

    # Define Parallel Fan-Out from START
    builder.add_edge(START, "repo_investigator")
    builder.add_edge(START, "doc_analyst")
    builder.add_edge(START, "vision_inspector")

    # Define Fan-In to Aggregator
    builder.add_edge("repo_investigator", "evidence_aggregator")
    builder.add_edge("doc_analyst", "evidence_aggregator")
    builder.add_edge("vision_inspector", "evidence_aggregator")

    # End after aggregation (Judicial layer is Phase 2/3)
    builder.add_edge("evidence_aggregator", END)

    return builder.compile()

graph = create_graph()
