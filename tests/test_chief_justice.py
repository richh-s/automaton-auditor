"""
Tests for ChiefJustice conflict resolution and report generation.
Covers each deterministic rule individually.
"""
import unittest
import os
import tempfile
from decimal import Decimal, ROUND_HALF_UP

from src.state import (
    AgentState, JudicialOpinion, CriterionResult, AuditReport, ConflictEntry
)
from src.nodes.judges import ChiefJustice, _build_remediation_plan
from src.report_writer import write_forensic_report


def _make_opinion(judge: str, criterion_id: str, score: int, argument: str = "Test argument.", cited_evidence=None):
    """Helper to create a JudicialOpinion."""
    return JudicialOpinion(
        judge=judge,
        criterion_id=criterion_id,
        score=score,
        argument=argument,
        cited_evidence=cited_evidence or ["src/graph.py"]
    )


def _make_state(
    opinions,
    conflicts=None,
    dimensions=None,
):
    """Helper to create a minimal AgentState for ChiefJustice."""
    if dimensions is None:
        dimensions = [
            {"id": "graph_orchestration", "name": "Graph Orchestration Architecture",
             "target_artifact": "github_repo", "forensic_instruction": "", "success_pattern": "", "failure_pattern": ""},
            {"id": "safe_tool_engineering", "name": "Safe Tool Engineering",
             "target_artifact": "github_repo", "forensic_instruction": "", "success_pattern": "", "failure_pattern": ""},
        ]
    return {
        "repo_url": "https://github.com/test/repo",
        "pdf_path": "test.pdf",
        "rubric_dimensions": dimensions,
        "synthesis_rules": {},
        "evidences": {},
        "opinions": opinions,
        "conflict_log": conflicts or [],
        "final_report": None,
    }


class TestSecurityOverride(unittest.TestCase):
    """Rule: Security conflicts cap dimension score at 3."""

    def test_security_override_caps_at_3(self):
        opinions = [
            _make_opinion("Prosecutor", "safe_tool_engineering", 5),
            _make_opinion("Defense", "safe_tool_engineering", 5),
            _make_opinion("TechLead", "safe_tool_engineering", 5),
        ]
        conflicts = [
            ConflictEntry(tag="SECURITY", dimension_id="safe_tool_engineering",
                          message="os.system detected")
        ]
        state = _make_state(opinions, conflicts)
        result = ChiefJustice(state)
        report = result["final_report"]
        
        safe_criterion = next(c for c in report.criteria if c.dimension_id == "safe_tool_engineering")
        self.assertLessEqual(safe_criterion.final_score, 3)

    def test_security_does_not_affect_other_dimensions(self):
        opinions = [
            _make_opinion("Prosecutor", "graph_orchestration", 5),
            _make_opinion("Defense", "graph_orchestration", 5),
            _make_opinion("TechLead", "graph_orchestration", 5),
            _make_opinion("Prosecutor", "safe_tool_engineering", 5),
            _make_opinion("Defense", "safe_tool_engineering", 5),
            _make_opinion("TechLead", "safe_tool_engineering", 5),
        ]
        conflicts = [
            ConflictEntry(tag="SECURITY", dimension_id="safe_tool_engineering",
                          message="os.system detected")
        ]
        state = _make_state(opinions, conflicts)
        result = ChiefJustice(state)
        report = result["final_report"]
        
        graph_criterion = next(c for c in report.criteria if c.dimension_id == "graph_orchestration")
        self.assertEqual(graph_criterion.final_score, 5)


class TestFactSupremacy(unittest.TestCase):
    """Rule: FACTCHECK conflicts penalize Defense (set to 1)."""

    def test_fact_supremacy_penalizes_defense(self):
        opinions = [
            _make_opinion("Prosecutor", "graph_orchestration", 3),
            _make_opinion("Defense", "graph_orchestration", 5),
            _make_opinion("TechLead", "graph_orchestration", 3),
        ]
        conflicts = [
            ConflictEntry(tag="FACTCHECK", dimension_id="graph_orchestration",
                          message="PDF claims parallel but no code found")
        ]
        state = _make_state(opinions, conflicts)
        result = ChiefJustice(state)
        report = result["final_report"]
        
        graph_criterion = next(c for c in report.criteria if c.dimension_id == "graph_orchestration")
        # Without penalty: (3*0.4 + 3*0.3 + 5*0.3) = 3.6 -> 4
        # With penalty (Defense=1): TechLead >= 4? No (3). So weighted: (3*0.4 + 3*0.3 + 1*0.3) = 2.4 -> 2
        self.assertLess(graph_criterion.final_score, 4)


class TestDissentRequirement(unittest.TestCase):
    """Rule: Dissent required when max(scores) - min(scores) > 2."""

    def test_dissent_required_when_variance_gt_2(self):
        opinions = [
            _make_opinion("Prosecutor", "graph_orchestration", 1, "This is terrible."),
            _make_opinion("Defense", "graph_orchestration", 5, "This is amazing."),
            _make_opinion("TechLead", "graph_orchestration", 3, "It works."),
        ]
        state = _make_state(opinions)
        result = ChiefJustice(state)
        report = result["final_report"]
        
        criterion = next(c for c in report.criteria if c.dimension_id == "graph_orchestration")
        self.assertIsNotNone(criterion.dissent_summary)
        self.assertIn("Major disagreement", criterion.dissent_summary)

    def test_no_dissent_when_variance_lte_2(self):
        opinions = [
            _make_opinion("Prosecutor", "graph_orchestration", 3),
            _make_opinion("Defense", "graph_orchestration", 4),
            _make_opinion("TechLead", "graph_orchestration", 4),
        ]
        state = _make_state(opinions)
        result = ChiefJustice(state)
        report = result["final_report"]
        
        criterion = next(c for c in report.criteria if c.dimension_id == "graph_orchestration")
        self.assertIsNone(criterion.dissent_summary)


class TestTechLeadAuthority(unittest.TestCase):
    """Rule: TechLead is sole authority on graph_orchestration when score >= 4."""

    def test_techlead_authoritative_on_architecture(self):
        opinions = [
            _make_opinion("Prosecutor", "graph_orchestration", 1),
            _make_opinion("Defense", "graph_orchestration", 1),
            _make_opinion("TechLead", "graph_orchestration", 4),
        ]
        state = _make_state(opinions)
        result = ChiefJustice(state)
        report = result["final_report"]
        
        criterion = next(c for c in report.criteria if c.dimension_id == "graph_orchestration")
        # TechLead >= 4, so score = TechLead score = 4
        self.assertEqual(criterion.final_score, 4)

    def test_techlead_not_authoritative_when_below_4(self):
        opinions = [
            _make_opinion("Prosecutor", "graph_orchestration", 1),
            _make_opinion("Defense", "graph_orchestration", 1),
            _make_opinion("TechLead", "graph_orchestration", 3),
        ]
        state = _make_state(opinions)
        result = ChiefJustice(state)
        report = result["final_report"]
        
        criterion = next(c for c in report.criteria if c.dimension_id == "graph_orchestration")
        # Weighted: (3*0.4 + 1*0.3 + 1*0.3) = 1.8 -> 2
        self.assertEqual(criterion.final_score, 2)


class TestClampingAndRounding(unittest.TestCase):
    """Scores always integer 1-5, using Decimal ROUND_HALF_UP."""

    def test_scores_clamped_1_to_5(self):
        opinions = [
            _make_opinion("Prosecutor", "safe_tool_engineering", 1),
            _make_opinion("Defense", "safe_tool_engineering", 1),
            _make_opinion("TechLead", "safe_tool_engineering", 1),
        ]
        # Add a security penalty on top of already-low scores
        conflicts = [
            ConflictEntry(tag="SECURITY", dimension_id="safe_tool_engineering",
                          message="test"),
            ConflictEntry(tag="FACTCHECK", dimension_id="safe_tool_engineering",
                          message="test"),
        ]
        state = _make_state(opinions, conflicts)
        result = ChiefJustice(state)
        report = result["final_report"]
        
        for c in report.criteria:
            self.assertGreaterEqual(c.final_score, 1)
            self.assertLessEqual(c.final_score, 5)

    def test_round_half_up(self):
        """2.5 should round to 3, not 2 (banker's rounding)."""
        # Need scores that produce exactly 2.5
        # Weighted: (t*0.4 + p*0.3 + d*0.3) = 2.5
        # t=4, p=2, d=1: (1.6 + 0.6 + 0.3) = 2.5 ✓
        opinions = [
            _make_opinion("Prosecutor", "safe_tool_engineering", 2),
            _make_opinion("Defense", "safe_tool_engineering", 1),
            _make_opinion("TechLead", "safe_tool_engineering", 4),
        ]
        state = _make_state(opinions)
        result = ChiefJustice(state)
        report = result["final_report"]
        
        criterion = next(c for c in report.criteria if c.dimension_id == "safe_tool_engineering")
        # 2.5 rounds to 3 with ROUND_HALF_UP
        self.assertEqual(criterion.final_score, 3)


class TestReportWriter(unittest.TestCase):
    """Report must contain required sections and content."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_report_contains_required_sections(self):
        report = AuditReport(
            repo_url="https://github.com/test/repo",
            executive_summary="Test audit complete. 2 dimensions, 1 conflict.",
            overall_score=3.5,
            criteria=[
                CriterionResult(
                    dimension_id="graph_orchestration",
                    dimension_name="Graph Orchestration Architecture",
                    final_score=4,
                    judge_opinions=[
                        _make_opinion("Prosecutor", "graph_orchestration", 2, "Gaps found.", ["src/graph.py:L14"]),
                        _make_opinion("Defense", "graph_orchestration", 5, "Great effort.", ["report.pdf:p3"]),
                        _make_opinion("TechLead", "graph_orchestration", 4, "Solid architecture.", ["src/graph.py:L14"]),
                    ],
                    dissent_summary="Major disagreement (spread=3): Defense (5/5) vs Prosecutor (2/5).",
                    remediation="Add conditional edges for error handling in src/graph.py"
                ),
                CriterionResult(
                    dimension_id="safe_tool_engineering",
                    dimension_name="Safe Tool Engineering",
                    final_score=3,
                    judge_opinions=[
                        _make_opinion("Prosecutor", "safe_tool_engineering", 3, "Acceptable."),
                        _make_opinion("Defense", "safe_tool_engineering", 3, "Good enough."),
                        _make_opinion("TechLead", "safe_tool_engineering", 3, "Functional."),
                    ],
                    dissent_summary=None,
                    remediation="Ensure all subprocess calls have timeout parameters"
                ),
            ],
            remediation_plan="- Fix graph edges\n- Add timeouts"
        )

        path = write_forensic_report(report, output_dir=self.tmpdir)
        
        self.assertTrue(os.path.exists(path))
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Required content checks
        self.assertIn("https://github.com/test/repo", content)
        self.assertIn("3.5/5.0", content)
        self.assertIn("## Executive Summary", content)
        self.assertIn("## Criterion Breakdown", content)
        self.assertIn("## Remediation Plan", content)
        self.assertIn("Major disagreement", content)
        # At least one citation
        self.assertIn("src/graph.py", content)
        # Remediation present
        self.assertIn("conditional edges", content)


if __name__ == "__main__":
    unittest.main()
