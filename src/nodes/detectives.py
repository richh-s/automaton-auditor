from src.state import AgentState, Evidence
from src.tools.repo_tools import RepoTools
from src.tools.doc_tools import DocTools
from src.tools.vision_tools import VisionTools
import os
import tempfile
import subprocess

# --- Detective Layer (Forensic Sub-Agents) ---

def RepoInvestigator(state: AgentState):
    """
    Forensic code analysis.
    Uses Deep AST Parsing to verify structure and Git Forensics for narrative.
    """
    print(f"--- REPO INVESTIGATOR (Deep AST & Git Forensics) ---")
    repo_url = state.get("repo_url", "")
    evidences = []

    if not repo_url:
         print("DEBUG: No repo URL provided.")
         return {"evidences": {"repo": [Evidence(
                goal="Environment Clone",
                found=False,
                location="None",
                rationale="No repository URL provided in state.",
                confidence=1.0
            )]}}

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"DEBUG: Using tmpdir: {tmpdir}")
        # 1. Stateless Sandbox Clone
        try:
            print(f"DEBUG: Cloning {repo_url}...")
            clone_res = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, "."],
                cwd=tmpdir,
                capture_output=True,
                check=False,
                timeout=300
            )
            print(f"DEBUG: Clone result code: {clone_res.returncode}")
            if clone_res.returncode != 0:
                print(f"DEBUG: Clone failed: {clone_res.stderr.decode()}")
            
            # 2. Comprehensive Forensic Scan
            source_files = []
            for root, _, files in os.walk(tmpdir):
                if any(x in root for x in [".git", "node_modules", "__pycache__"]):
                    continue
                for f in files:
                    if f.endswith((".py", ".ts", ".js")):
                        source_files.append(os.path.join(root, f))
            
            print(f"DEBUG: Found {len(source_files)} potential source files.")
            
            # Find the best candidate for the "Graph"
            graph_candidate = os.path.join(tmpdir, "src/graph.py")
            if not os.path.exists(graph_candidate):
                 print("DEBUG: src/graph.py not found. Searching for candidates...")
                 candidates = [f for f in source_files if "graph" in f.lower()]
                 if candidates:
                     graph_candidate = candidates[0]
                     print(f"DEBUG: Selected candidate: {graph_candidate}")
                 elif source_files:
                     graph_candidate = source_files[0] 
                     print(f"DEBUG: Fallback selected: {graph_candidate}")
            
            if os.path.exists(graph_candidate):
                print(f"DEBUG: Analyzing {graph_candidate}...")
                graph_data = RepoTools.analyze_graph_structure(graph_candidate)
                evidences.append(Evidence(
                    goal="Verify Graph Parallelism",
                    found=graph_data.state_graph_instance_found,
                    location=os.path.relpath(graph_candidate, tmpdir),
                    rationale=f"Pattern: {graph_data.node_type}. Line: {graph_data.initialization_line}.",
                    confidence=1.0 if graph_data.state_graph_instance_found else 0.5
                ))
            else:
                print("DEBUG: No graph candidate found.")
            
            # 3. Reducer Verification (Fallback)
            state_candidate = os.path.join(tmpdir, "src/state.py")
            if os.path.exists(state_candidate):
                print(f"DEBUG: Analyzing {state_candidate} for reducers...")
                reducer_data = RepoTools.verify_reducer_robustness(state_candidate)
                evidences.append(Evidence(
                    goal="Verify Reducer Robustness",
                    found=reducer_data.is_robust,
                    location="src/state.py",
                    rationale=f"Found reducers: {reducer_data.reducers_found}.",
                    confidence=1.0 if reducer_data.annotated_found else 0.0
                ))

            # 5. Git History Analysis
            print("DEBUG: Extracting git history...")
            git_data = RepoTools.extract_git_history(tmpdir)
            evidences.append(Evidence(
                goal="Verify Development Narrative",
                found=git_data.commit_count > 0,
                location="git history",
                rationale=f"Pattern: {git_data.development_pattern}. Commits: {git_data.commit_count}.",
                confidence=0.95
            ))

        except Exception as e:
            print(f"DEBUG: Repo Investigator Exception: {e}")
            evidences.append(Evidence(
                goal="Environment Clone",
                found=False,
                location=repo_url,
                rationale=f"Cloning failed: {str(e)}",
                confidence=1.0
            ))

    return {"evidences": {"repo": evidences}}

def DocAnalyst(state: AgentState):
    """
    Forensic document analysis using RAG-lite.
    """
    print("--- DOC ANALYST (Citation-Preserving RAG-lite) ---")
    pdf_path = state.get("pdf_path")
    evidences = []

    if os.path.exists(pdf_path):
        chunks = DocTools.ingest_pdf(pdf_path)
        
        # Simulated Query: "Check for Metacognition"
        metacog_results = DocTools.rag_lite_query("metacognition", chunks)
        if metacog_results:
            top = metacog_results[0]
            evidences.append(Evidence(
                goal="Verify Metacognitive Claims",
                found=True,
                location=f"{pdf_path}:p{top.page_number}",
                rationale=f"Found match on page {top.page_number} with confidence {top.confidence:.2f}.",
                confidence=top.confidence
            ))
    else:
        evidences.append(Evidence(
            goal="Locate PDF Report",
            found=False,
            location=pdf_path,
            rationale="Report file missing from workspace.",
            confidence=1.0
        ))

    return {"evidences": {"doc": evidences}}

def VisionInspector(state: AgentState):
    """
    Forensic diagram analysis with strict logic gates.
    """
    print("--- VISION INSPECTOR (Multimodal Discrimination) ---")
    pdf_path = state.get("pdf_path")
    evidences = []

    if os.path.exists(pdf_path):
        images = VisionTools.extract_images_from_pdf(pdf_path)
        if images:
            # Analyze first image
            vision_data = VisionTools.analyze_diagram(images[0])
            evidences.append(Evidence(
                goal="Verify Architectural Diagram",
                found=vision_data.diagram_type == "LangGraph",
                location=f"{pdf_path}:img1",
                rationale=f"Type: {vision_data.diagram_type}. START/END: {vision_data.contains_START}/{vision_data.contains_END}.",
                confidence=min(0.8, vision_data.confidence) # Capped at 0.8
            ))

    return {"evidences": {"vision": evidences}}
