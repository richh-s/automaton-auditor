# Week 2 Reflection: Peer Feedback Integration & MinMax Optimization

## Phase 1 → Phase 2: What Peer Agents Revealed

During Week 1, peer auditors were deployed against early prototypes of this agent. The following **deep architectural flaws** were uncovered through cross-agent analysis:

### Flaw 1: Spaghetti Script Detection Blind Spot
**Peer Finding:** Several Week 1 submissions passed basic `StateGraph` detection but were actually spaghetti scripts with massive `switch/case` blocks and no modular node separation. The initial detector only checked for `StateGraph` keyword presence via regex — it couldn't distinguish between a proper graph orchestration and a monolithic script that happened to import `StateGraph`.

**Response (Week 2 Update):**
- Replaced all regex-based detection with **deep AST parsing** via `ast.NodeVisitor` subclasses in `src/tools/repo_tools.py`.
- Added `is_spaghetti` heuristic in `analyze_graph_structure()` that flags large `switch/case` blocks (>15 cases) as architectural violations.
- Added `compiled_on_correct_instance` check to verify `.compile()` is called on the actual `StateGraph` variable, not some unrelated object.

### Flaw 2: Reducer Absence = Silent Data Loss
**Peer Finding:** Multiple peers used plain `Dict` or `List` for state without `Annotated` reducers. When their detectives ran in parallel, only the last-finishing node's data survived — all prior evidence was silently overwritten. The original auditor did not check for this pattern.

**Response (Week 2 Update):**
- Implemented `verify_reducer_robustness()` in `repo_tools.py` — a dedicated AST visitor that checks for `Annotated[..., operator.add]` and `Annotated[..., operator.ior]` type hints.
- Added `ReducerForensics` model to report exactly which reducers are present and whether the state is "robust" (requires both `add` and `ior`).
- Updated own `AgentState` to use `operator.ior` for evidences dict-merge and `operator.add` for list-append, preventing the same flaw in this agent.

### Flaw 3: Unsafe Shell Execution in Tool Layer
**Peer Finding:** Two peer submissions used raw `os.system("git clone ...")` with unsanitized URLs — a shell injection vulnerability. The Week 1 auditor had no mechanism to detect or penalize this.

**Response (Week 2 Update):**
- Added `verify_tool_safety()` AST scanner that detects `os.system`, `eval`, and `exec` calls.
- Added `SafetyForensics` model with `unsafe_calls_found` list.
- Integrated into `EvidenceAggregator` — security violations now emit `ConflictEntry(tag="SECURITY")` which hard-caps dimension score at 3 in the ChiefJustice pipeline.
- Added `synthesis_rules.security_override` to the rubric itself.

### Flaw 4: Hallucinated Evidence in Reports
**Peer Finding:** Some peers' PDF reports claimed features that didn't exist in their code (e.g., "We implemented parallel Judges" but the graph was purely sequential). The Week 1 auditor had no cross-referencing capability.

**Response (Week 2 Update):**
- Built the `EvidenceAggregator` as a **metacognitive barrier** between Detectives and Judges.
- Cross-references doc claims (from `DocAnalyst`) against repo evidence (from `RepoInvestigator`) — if the PDF claims a feature but repo evidence contradicts it, a `FACTCHECK` conflict is emitted.
- `FACTCHECK` conflicts trigger `fact_supremacy` rule: Defense score is overridden to 1, preventing inflated scores for hallucinated claims.

---

## Self-Evaluation: Detecting Our Own Flaws

The MinMax principle requires that **any flaw we can detect in peers, we must also guard against in ourselves.** This agent implements:

| Flaw Detected in Peers | Self-Guard in This Agent |
|------------------------|--------------------------|
| No AST parsing (regex only) | `repo_tools.py` uses 3 `ast.NodeVisitor` subclasses |
| Missing reducers | `state.py` uses `Annotated[..., operator.ior]` and `Annotated[..., operator.add]` |
| Unsafe `os.system` calls | Uses `subprocess.run()` with `check=True`, `capture_output=True`, `timeout=600` inside `tempfile.TemporaryDirectory()` |
| Hallucinated evidence | `EvidenceAggregator` cross-references all doc claims against repo findings |
| No dissent explanation | `ChiefJustice` generates explicit dissent summaries when score variance > 2 |

---

## Commit Trail Evidence

The git history demonstrates iterative integration of these fixes:

```
791649f feat: refine typed state with identity-compatible reducers        ← Flaw 2 fix
ba445b2 feat: implement parallel detective fan-out and evidence aggregation ← Architecture upgrade
7eeb327 feat: implement metacognitive validation in evidence_aggregator    ← Flaw 4 fix
9a4dbd4 feat: implement deep ast placeholders and metacognitive barrier    ← Flaw 1 fix
2105e3a feat: complete Phase 1 orchestration and Phase 2 advanced forensic tools ← Flaw 3 fix
64b3aef feat: Implement structured conflict logging, Chief Justice resolution  ← Synthesis rules
```

Each flaw discovered through peer analysis has a corresponding commit implementing the fix and detection capability.
