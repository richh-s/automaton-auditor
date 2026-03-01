# Automaton Auditor: Orchestrating Deep LangGraph Swarms

The **Automaton Auditor** is a production-grade multi-agent system designed for autonomous governance and quality assurance in AI-Native enterprises. It operates as a **Digital Courtroom**, utilizing a hierarchical swarm of specialized agents to perform forensic analysis, apply nuanced judgment, and provide actionable technical remediation.

## 🏛️ Infrastructure & Forensic Tools

The Automaton Auditor implements a resilient and deterministic forensic architecture using a multi-agent approach.

### Key Features:
- **Parallel Forensic Swarm**: Fan-out/fan-in architecture triggering multiple detective nodes concurrently.
- **Metacognitive synchronization barrier**: `evidence_aggregator` node audits forensic completeness before finalization.
- **Advanced Forensic Tools**: 
    - `RepoInvestigator`: Deep AST parsing and Git history analysis.
    - `DocAnalyst`: Citation-preserving PDF RAG-lite retrieval.
    - `VisionInspector`: Image extraction and layout analysis.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.14+**
- **uv**: The project uses `uv` for lightning-fast dependency management. [Install uv](https://github.com/astral-sh/uv).

### 2. Installation
Clone the repository and install dependencies using `uv`:
```bash
git clone <repo-url>
cd automaton-auditor
uv sync
```

### 3. Environment Setup
Copy the example environment file and add your credentials:
```bash
cp .env.example .env
```
### 4. Docker (Optional)
The auditor is containerized for forensic isolation. Build and run with:
```bash
docker build -t automaton-auditor .
docker run --env-file .env automaton-auditor --repo <URL> --pdf <PATH>
```

---

## 🛠️ Usage

### Running the Forensic Graph
The auditor can be executed against any target repository or technical report. If no arguments are provided, it defaults to auditing its own repository.

```bash
# General usage via uv
uv run python main.py --repo <REPO_URL> --pdf <PATH_TO_PDF>

# Example: Auditing an external project
uv run python main.py \
  --repo https://github.com/langchain-ai/langgraph \
  --pdf reports/architecture_spec.pdf
```

### Running Tests
To validate forensic tools and orchestration:
```bash
uv run pytest tests/
```

---

## 🔄 Peer Feedback Loop (MinMax Optimization)

This agent was iteratively refined based on peer feedback loops. See [`REFLECTION.md`](REFLECTION.md) for self-guard mechanisms.

### Audit Results
Detailed audit reports are organized in the `audit/` directory for submission:
- **Self-Audit**: [`audit/report_onself_generated/forensic_report.md`](audit/report_onself_generated/forensic_report.md)
- **Peer-Audit**: [`audit/report_onpeer_generated/forensic_report.md`](audit/report_onpeer_generated/forensic_report.md)
- **Peer-Received**: [`audit/report_bypeer_received/`](audit/report_bypeer_received/) (Placeholder for peer's audit on this repo)

---

## 📂 Project Structure
- `src/graph.py`: Complete StateGraph with parallel fan-out/fan-in.
- `src/state.py`: Finalized state definitions and robust reducers.
- `src/nodes/`:
    - `detectives.py`: RepoInvestigator, DocAnalyst, and VisionInspector.
    - `judges.py`: Prosecutor, Defense, and TechLead personas.
    - `justice.py`: ChiefJusticeNode with deterministic conflict resolution rules.
- `src/tools/`:
    - `repo_tools.py`: AST-based forensic tools for repo analysis.
    - `doc_tools.py`: PDF parsing and cross-referencing tools.
    - `vision_tools.py`: Image extraction logic.
- `audit/`: Submission reports (Self-generated, Peer-generated, Peer-received).
- `reports/`:
    - `final_report.pdf`: The official PDF technical report for this project.
- `pyproject.toml`: Minimal locked dependencies managed via `uv`.
- `Dockerfile`: Containerized runtime for the auditor.
- `REFLECTION.md`: Documentation of the MinMax peer feedback loop.
- `rubric.json`: Machine-readable rubric (9 dimensions, 4 synthesis rules).


