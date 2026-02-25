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
    print("--- REPO INVESTIGATOR (Deep AST & Git Forensics) ---")
    repo_url = state.get("repo_url")
    evidences = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Stateless Sandbox Clone
        try:
            subprocess.run(
                ["git", "clone", repo_url, "."],
                cwd=tmpdir,
                capture_output=True,
                check=False,
                timeout=30
            )
            
            # 2. Deep AST Analysis
            # In a real scenario, we'd find the graph file. Here we assume src/graph.py
            graph_path = os.path.join(tmpdir, "src/graph.py")
            if os.path.exists(graph_path):
                graph_data = RepoTools.analyze_graph_structure(graph_path)
                evidences.append(Evidence(
                    goal="Verify Graph Parallelism",
                    found=graph_data.state_graph_instance_found,
                    location="src/graph.py",
                    rationale=f"AST found {len(graph_data.edges)} edges. Fan-out: {graph_data.fan_out_count}.",
                    confidence=1.0 if graph_data.state_graph_instance_found else 0.0,
                    metadata=graph_data.dict()
                ))
            
            # 3. Reducer Verification
            state_path = os.path.join(tmpdir, "src/state.py")
            if os.path.exists(state_path):
                reducer_data = RepoTools.verify_reducer_robustness(state_path)
                evidences.append(Evidence(
                    goal="Verify Reducer Robustness",
                    found=reducer_data.is_robust,
                    location="src/state.py",
                    rationale=f"Found reducers: {reducer_data.reducers_found}.",
                    confidence=1.0 if reducer_data.annotated_found else 0.0,
                    metadata=reducer_data.dict()
                ))

            # 4. Tool Safety Check
            if os.path.exists(graph_path):
                safety_data = RepoTools.verify_tool_safety(graph_path)
                evidences.append(Evidence(
                    goal="Verify Tool Safety",
                    found=safety_data.is_safe,
                    location="src/graph.py",
                    rationale=f"Found unsafe calls: {safety_data.unsafe_calls_found}." if not safety_data.is_safe else "No unsafe calls (os.system, eval) detected.",
                    confidence=1.0,
                    metadata=safety_data.dict()
                ))

            # 5. Git History Analysis
            git_data = RepoTools.extract_git_history(tmpdir)
            evidences.append(Evidence(
                goal="Verify Development Narrative",
                found=git_data.commit_count > 0,
                location="git history",
                rationale=f"Pattern: {git_data.development_pattern}. Commits: {git_data.commit_count}.",
                confidence=0.95,
                metadata=git_data.dict()
            ))

        except Exception as e:
            print(f"Repo Investigator Failed: {e}")
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
                confidence=top.confidence,
                metadata={"chunk_id": top.chunk_id, "page": top.page_number}
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
                confidence=min(0.8, vision_data.confidence), # Capped at 0.8
                metadata=vision_data.dict()
            ))

    return {"evidences": {"vision": evidences}}
