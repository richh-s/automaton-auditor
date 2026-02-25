import unittest
import os
import tempfile
import ast
from src.tools.repo_tools import RepoTools
from src.tools.doc_tools import DocTools

class TestForensics(unittest.TestCase):
    def test_ast_parallel_detection(self):
        """
        Tests if the AST visitor correctly detects parallel fan-out.
        """
        code = """
from langgraph.graph import StateGraph, START, END
builder = StateGraph(dict)
builder.add_node("a", lambda x: x)
builder.add_node("b", lambda x: x)
builder.add_edge(START, "a")
builder.add_edge(START, "b")
builder.compile()
        """
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        
        try:
            results = RepoTools.analyze_graph_structure(tmp_path)
            self.assertTrue(results.state_graph_instance_found)
            self.assertEqual(results.graph_variable_name, "builder")
            self.assertEqual(results.fan_out_count, 2)
            self.assertTrue(results.is_compiled)
            self.assertTrue(results.compiled_on_correct_instance)
        finally:
            os.remove(tmp_path)

    def test_reducer_verification(self):
        """
        Tests if AST visitor correctly detects Annotated reducers.
        """
        code = """
import operator
from typing import Annotated, TypedDict, List, Dict

class State(TypedDict):
    evidences: Annotated[Dict, operator.ior]
    opinions: Annotated[List, operator.add]
        """
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        
        try:
            results = RepoTools.verify_reducer_robustness(tmp_path)
            self.assertTrue(results.annotated_found)
            self.assertIn("ior", results.reducers_found)
            self.assertIn("add", results.reducers_found)
            self.assertTrue(results.is_robust)
        finally:
            os.remove(tmp_path)

    def test_git_delta_classification(self):
        """
        Note: This test requires a real git repo. 
        We test the logic by mocking or using current repo.
        """
        results = RepoTools.extract_git_history(".")
        self.assertGreater(results.commit_count, 0)
        self.assertIn(results.development_pattern, ["Iterative Development", "Monolithic Dump", "Single Commit Pattern"])

    def test_doc_rag_lite_confidence(self):
        """
        Tests confidence range for RAG-lite retrieval.
        """
        from src.tools.doc_tools import DocEvidence
        chunks = [
            DocEvidence(chunk_id="1", page_number=1, content="This is about metacognition and deep agents.", confidence=0.85),
            DocEvidence(chunk_id="2", page_number=2, content="This is about vision and images.", confidence=0.85)
        ]
        
        results = DocTools.rag_lite_query("metacognition", chunks)
        self.assertEqual(len(results), 1)
        self.assertTrue(0.6 <= results[0].confidence <= 0.85)

    # --- Failure Mode Tests (Rubric Enhancement) ---

    def test_unsafe_code_detection(self):
        """
        Tests if RepoTools correctly detects os.system and eval.
        """
        code = "import os\nos.system('rm -rf /')\neval('1+1')"
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        
        try:
            results = RepoTools.verify_tool_safety(tmp_path)
            self.assertFalse(results.is_safe)
            self.assertIn("os.system", results.unsafe_calls_found)
            self.assertIn("eval", results.unsafe_calls_found)
        finally:
            os.remove(tmp_path)

    def test_no_graph_detection(self):
        """
        Tests if RepoTools handles files with no StateGraph logic.
        """
        code = "print('hello world')"
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        
        try:
            results = RepoTools.analyze_graph_structure(tmp_path)
            self.assertFalse(results.state_graph_instance_found)
        finally:
            os.remove(tmp_path)

    def test_missing_pdf_handling(self):
        """
        Tests if DocTools handles missing files gracefully.
        """
        results = DocTools.ingest_pdf("non_existent_file.pdf")
        self.assertEqual(results, [])

if __name__ == "__main__":
    unittest.main()
