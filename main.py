from src.graph import graph

def main():
    print("--- AUTOMATON AUDITOR: PHASE 1 START ---")
    
    # Explicit Identity Initialization for Master Thinker Concurrency Control
    initial_state = {
        "repo_url": "https://github.com/richh-s/automaton-auditor",
        "pdf_path": "report.pdf",
        "rubric_dimensions": [],
        "evidences": {}, # Identity value for operator.ior
        "opinions": [],  # Identity value for operator.add
        "conflict_log": [], # Future-proofed resolution tracking
    }
    
    print("Invoking Graph Orchestrator...")
    result = graph.invoke(initial_state)
    print("--- PHASE 1 COMPLETE ---")

if __name__ == "__main__":
    main()
