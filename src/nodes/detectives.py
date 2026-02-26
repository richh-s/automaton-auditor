from src.state import AgentState, Evidence
from src.tools.repo_tools import RepoTools
from src.tools.doc_tools import DocTools
from src.tools.vision_tools import VisionTools
import os
import tempfile
import subprocess
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# --- Infrastructure Layer (Phase 3) ---

def ContextBuilder(state: AgentState):
    """
    The Context Builder: Loads the rubric and prepares dimensions for dispatch.
    """
    print("--- CONTEXT BUILDER: Loading Forensic Constitution ---")
    with open("rubric.json", "r") as f:
        rubric = json.load(f)
    
    return {
        "rubric_dimensions": rubric["dimensions"],
        "synthesis_rules": rubric["synthesis_rules"]
    }

# --- Detective Layer (Forensic Sub-Agents) ---

def RepoInvestigator(state: AgentState):
    """
    Forensic code analysis.
    Uses LLM to interpret specialized forensic instructions and extract evidence.
    """
    print(f"--- REPO INVESTIGATOR (Forensic Logic) ---")
    repo_url = state.get("repo_url", "")
    tasks = [d for d in state.get("rubric_dimensions", []) if d["target_artifact"] == "github_repo"]
    evidences = []

    if not repo_url:
         return {"evidences": {"repo": []}}

    llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(Evidence)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # 1. Clone
            subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", repo_url, "."], cwd=tmpdir, check=True, capture_output=True, timeout=600)
            
            # 2. Extract context for the LLM
            git_history = str(subprocess.run(["git", "log", "--oneline", "-n", "20"], cwd=tmpdir, capture_output=True).stdout.decode())
            
            # 3. Dynamic Forensic Execution
            for task in tasks:
                print(f"DEBUG: Executing Instruction for '{task['name']}'")
                
                # Context gathering based on task hint
                context = f"Git History:\n{git_history}\n"
                if "state" in task["forensic_instruction"].lower():
                    # Quick scan for state files
                    for root, _, files in os.walk(tmpdir):
                        for f in files:
                            if "state" in f or "graph" in f:
                                with open(os.path.join(root, f), "r") as src:
                                    context += f"--- {f} ---\n{src.read()[:2000]}\n"

                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a Forensic Code Detective. Execute the following instruction on the provided context. "
                               "Return an Evidence object. Instruction: {instruction}"),
                    ("user", "Context:\n{context}")
                ])
                
                chain = prompt | llm
                ev = chain.invoke({"instruction": task["forensic_instruction"], "context": context})
                ev.goal = task["name"] # Align goal with dimension name
                evidences.append(ev)

        except Exception as e:
            print(f"DEBUG: Repo Error: {e}")
            evidences.append(Evidence(goal="Cloning", found=False, location=repo_url, rationale=str(e), confidence=1.0))

    return {"evidences": {"repo": evidences}}

def DocAnalyst(state: AgentState):
    """
    Forensic document analysis using RAG-lite and instruction-following.
    """
    print("--- DOC ANALYST (Instruction-Following RAG) ---")
    pdf_path = state.get("pdf_path")
    tasks = [d for d in state.get("rubric_dimensions", []) if d["target_artifact"] == "pdf_report"]
    evidences = []

    if not pdf_path or not os.path.exists(pdf_path):
        return {"evidences": {"doc": []}}

    llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(Evidence)
    chunks = DocTools.ingest_pdf(pdf_path)

    for task in tasks:
        # Simple search for instruction keywords
        keywords = ["Metacognition", "Dialectical", "Fan-In", "Integrity"]
        query = next((k for k in keywords if k.lower() in task["forensic_instruction"].lower()), "architecture")
        
        rag_results = DocTools.rag_lite_query(query, chunks)
        context = "\n".join([f"Page {r.page_number}: {r.content}" for r in rag_results])

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a Forensic Document Analyst. Extract evidence for the following instruction. "
                       "Instruction: {instruction}"),
            ("user", "Context from PDF:\n{context}")
        ])
        
        chain = prompt | llm
        ev = chain.invoke({"instruction": task["forensic_instruction"], "context": context})
        ev.goal = task["name"]
        evidences.append(ev)

    return {"evidences": {"doc": evidences}}

def VisionInspector(state: AgentState):
    """
    Forensic diagram analysis with strict instruction gates.
    """
    print("--- VISION INSPECTOR (Instruction-Following Vision) ---")
    pdf_path = state.get("pdf_path")
    tasks = [d for d in state.get("rubric_dimensions", []) if d["target_artifact"] == "pdf_images"]
    evidences = []

    if not pdf_path or not os.path.exists(pdf_path):
        return {"evidences": {"vision": []}}

    images = VisionTools.extract_images_from_pdf(pdf_path)
    if not images:
        return {"evidences": {"vision": []}}

    # For now, we use a single visual check for all image-related tasks
    # In a full impl, we'd iterate and match
    vision_data = VisionTools.analyze_diagram(images[0])
    
    for task in tasks:
        ev = Evidence(
            goal=task["name"],
            found=vision_data.diagram_type == "LangGraph",
            location=f"{pdf_path}:img1",
            rationale=f"Detected {vision_data.diagram_type}. {task['forensic_instruction'][:50]}...",
            confidence=vision_data.confidence
        )
        evidences.append(ev)

    return {"evidences": {"vision": evidences}}
