import argparse
import os
from dotenv import load_dotenv
from src.graph import graph

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Automaton Auditor: Forensic Swarm Orchestrator")
    parser.add_argument("--repo", type=str, default="https://github.com/richh-s/automaton-auditor", help="Target GitHub Repository URL to audit")
    parser.add_argument("--pdf", type=str, default="report.pdf", help="Path to the technical report PDF to analyze")
    args = parser.parse_args()

    print(f"--- AUTOMATON AUDITOR: PHASE 1 START ---")
    print(f"Target Repo: {args.repo}")
    print(f"Target PDF:  {args.pdf}")
    
    # Explicit Identity Initialization for Master Thinker Concurrency Control
    initial_state = {
        "repo_url": args.repo,
        "pdf_path": args.pdf,
        "rubric_dimensions": [],
        "evidences": {}, 
        "opinions": [],  
        "final_report": None # Initial value
    }
    
    print("\nInvoking Graph Orchestrator...")
    result = graph.invoke(initial_state)
    print("\n--- PHASE 1 COMPLETE ---")
    
    report = result.get("final_report")
    if report:
        print(f"\nFinal Executive Summary:\n{report.executive_summary}")
        print(f"Overall Score: {report.overall_score}/5.0")

if __name__ == "__main__":
    main()
