from langgraph.graph import StateGraph, END, START
from src.state import AgentState, Evidence
from src.nodes.detectives import RepoInvestigator, DocAnalyst, VisionInspector
import os

# --- Synchronization & Metacognitive Validation ---

def evidence_aggregator(state: AgentState):
    """
    Fan-in node to synchronize evidence and perform deterministic arbitration.
    AST (1.0) overrides Doc/Vision (< 0.8) claims.
    """
    print("--- EVIDENCE AGGREGATOR (Deterministic Arbitration) ---")
    
    expected_keys = {"repo", "doc", "vision"}
    actual_keys = set(state["evidences"].keys())
    
    conflicts = []
    
    # 1. Structural Completeness Audit
    missing = expected_keys - actual_keys
    if missing:
        msg = f"Incomplete Evidence: Missing forensic dimensions: {missing}"
        conflicts.append(msg)
    
    # 2. Deterministic Arbitration & Conflict Logging
    # Example: If Doc claims 'Metacognition' but Repo AST finds no StateGraph logic
    repo_ev = state["evidences"].get("repo", [])
    doc_ev = state["evidences"].get("doc", [])
    vision_ev = state["evidences"].get("vision", [])

    # Find the AST Parallelism evidence
    ast_parallel = next((e for e in repo_ev if e.goal == "Verify Graph Parallelism"), None)
    doc_claim = next((e for e in doc_ev if e.goal == "Verify Metacognitive Claims"), None)
    
    if ast_parallel and doc_claim:
        # Deterministic Override: If AST says NO but Doc says YES
        if not ast_parallel.found and doc_claim.found:
            conflicts.append("High Severity Structural Mismatch: PDF claims complex architecture but AST shows no StateGraph.")
        
    # High Severity Mismatch: If both Doc and Vision contradict AST
    vision_claim = next((e for e in vision_ev if e.goal == "Verify Architectural Diagram"), None)
    if ast_parallel and not ast_parallel.found and doc_claim and doc_claim.found and vision_claim and vision_claim.found:
         conflicts.append("CRITICAL: Holistic Mismatch - Multi-artifact hallucination detected (Doc & Vision claim graph, AST denies).")

    if not conflicts:
        print("PASSED: Metacognitive check - Structural audit successful.")
    else:
        for c in conflicts:
            print(f"CONFLICT DETECTED: {c}")
    
    return {"conflict_log": conflicts}

# --- Graph Construction ---

def create_graph():
    builder = StateGraph(AgentState)

    # Add Detective Nodes
    builder.add_node("RepoInvestigator", RepoInvestigator)
    builder.add_node("DocAnalyst", DocAnalyst)
    builder.add_node("VisionInspector", VisionInspector)
    
    # Add Aggregator Node
    builder.add_node("evidence_aggregator", evidence_aggregator)

    # Define Parallel Fan-Out from START
    builder.add_edge(START, "RepoInvestigator")
    builder.add_edge(START, "DocAnalyst")
    builder.add_edge(START, "VisionInspector")

    # Define Fan-In to Aggregator
    builder.add_edge("RepoInvestigator", "evidence_aggregator")
    builder.add_edge("DocAnalyst", "evidence_aggregator")
    builder.add_edge("VisionInspector", "evidence_aggregator")

    # End after aggregation
    builder.add_edge("evidence_aggregator", END)

    return builder.compile()

graph = create_graph()
