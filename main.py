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
        "synthesis_rules": {},
        "evidences": {}, 
        "opinions": [],
        "conflict_log": [],
        "final_report": None
    }
    
    print("\nInvoking Graph Orchestrator...")
    result = graph.invoke(initial_state)
    print("\n--- PHASE 1 COMPLETE ---")
    
    report = result.get("final_report")
    if report:
        print(f"\n{'='*60}")
        print(f"FORENSIC AUDIT REPORT")
        print(f"{'='*60}")
        print(f"\nExecutive Summary: {report.executive_summary}")
        print(f"Overall Score: {report.overall_score:.2f}/5.0")
        print(f"\n--- Per-Dimension Breakdown ---")
        for c in report.criteria:
            print(f"\n  [{c.dimension_id}] {c.dimension_name}")
            print(f"    Final Score: {c.final_score}/5")
            if c.dissent_summary:
                print(f"    DISSENT: {c.dissent_summary}")
            for op in c.judge_opinions:
                print(f"      {op.judge} ({op.score}/5): {op.argument[:120]}...")
        print(f"\nRemediation Plan: {report.remediation_plan}")
        print(f"{'='*60}")
    
    # Also print conflicts
    conflicts = result.get("conflict_log", [])
    if conflicts:
        print(f"\n⚠️  FORENSIC CONFLICTS DETECTED:")
        for c in conflicts:
            print(f"  - {c}")
    
    # Print raw evidence keys
    evidences = result.get("evidences", {})
    print(f"\n--- Evidence Sources ---")
    for src, evs in evidences.items():
        print(f"  [{src}]: {len(evs)} evidence items")
        for ev in evs:
            print(f"    - {ev.goal}: found={ev.found}, conf={ev.confidence:.2f}")

if __name__ == "__main__":
    main()
