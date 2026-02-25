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
*Note: Forensic tools use simulated/local logic for certain LLM features but require valid LangSmith keys for full observability.*

---

## 🛠️ Usage

### Running the Forensic Graph
The auditor can be executed against any target repository or technical report. If no arguments are provided, it defaults to auditing its own repository.

```bash
# General usage
uv run python main.py --repo <REPO_URL> --pdf <PATH_TO_PDF>

# Example: Auditing an external project
uv run python main.py \
  --repo https://github.com/langchain-ai/langgraph \
  --pdf docs/architecture_spec.pdf
```

### Running Tests
To validate the forensic tools and orchestration logic including failure mode handling:
```bash
uv run python -m unittest tests/test_forensics.py
```

---

## 📂 Project Structure
- `src/graph.py`: The architecture of the LangGraph state machine.
- `src/state.py`: Pydantic definitions and robust reducers.
- `src/nodes/detectives.py`: Implementation of forensic agent nodes.
- `src/tools/`: Specialized modules for AST, PDF, and Git analysis.
- `reports/`: Location for generated forensic audit reports.
- `tests/`: Forensic test suite with high failure-mode coverage.
