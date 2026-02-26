from langgraph.graph import StateGraph, END, START
from src.state import AgentState, Evidence
from src.nodes.detectives import ContextBuilder, RepoInvestigator, DocAnalyst, VisionInspector
from src.nodes.judges import Prosecutor, Defense, TechLead, ChiefJustice, EvidenceAggregator
import os

def failure_node(state: AgentState):
    """
    Terminal node reached if no forensic artifacts are available for analysis.
    """
    print("--- FORENSIC ABORT: No artifacts available ---")
    return state

def create_graph():
    builder = StateGraph(AgentState)

    # Add Infrastructure & Detective Nodes
    builder.add_node("ContextBuilder", ContextBuilder)
    builder.add_node("RepoInvestigator", RepoInvestigator)
    builder.add_node("DocAnalyst", DocAnalyst)
    builder.add_node("VisionInspector", VisionInspector)
    
    # Add Judicial Nodes
    builder.add_node("EvidenceAggregator", EvidenceAggregator)
    builder.add_node("Prosecutor", Prosecutor)
    builder.add_node("Defense", Defense)
    builder.add_node("TechLead", TechLead)
    builder.add_node("ChiefJustice", ChiefJustice)
    
    builder.add_node("failure_node", failure_node)

    # --- Router Logic ---
    def start_router(state: AgentState):
        runnable = []
        if state.get("repo_url"):
            runnable.append("RepoInvestigator")
        if state.get("pdf_path") and os.path.exists(state.get("pdf_path", "")):
            runnable.append("DocAnalyst")
            runnable.append("VisionInspector")
            
        if not runnable:
            return "failure_node" # Return string instead of list for single edge
        return runnable

    # 1. START -> ContextBuilder (Always)
    builder.add_edge(START, "ContextBuilder")

    # 2. ContextBuilder -> Detectives (Parallel Fan-Out)
    builder.add_conditional_edges(
        "ContextBuilder",
        start_router,
        {
            "RepoInvestigator": "RepoInvestigator",
            "DocAnalyst": "DocAnalyst",
            "VisionInspector": "VisionInspector",
            "failure_node": "failure_node"
        }
    )

    # 3. Detectives -> Aggregator (Fan-In)
    builder.add_edge("RepoInvestigator", "EvidenceAggregator")
    builder.add_edge("DocAnalyst", "EvidenceAggregator")
    builder.add_edge("VisionInspector", "EvidenceAggregator")
    
    # 4. Aggregator -> Judges (Parallel Fan-Out)
    builder.add_edge("EvidenceAggregator", "Prosecutor")
    builder.add_edge("EvidenceAggregator", "Defense")
    builder.add_edge("EvidenceAggregator", "TechLead")
    
    # 5. Judges -> Chief Justice (Fan-In)
    builder.add_edge("Prosecutor", "ChiefJustice")
    builder.add_edge("Defense", "ChiefJustice")
    builder.add_edge("TechLead", "ChiefJustice")
    
    # 6. Terminal Paths
    builder.add_edge("ChiefJustice", END)
    builder.add_edge("failure_node", END)

    return builder.compile()

graph = create_graph()
