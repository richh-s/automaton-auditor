import ast
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

class GraphForensics(BaseModel):
    state_graph_instance_found: bool = False
    graph_variable_name: Optional[str] = None
    edges: List[Dict[str, str]] = []
    fan_out_count: int = 0
    fan_in_count: int = 0
    conditional_edges_count: int = 0
    is_compiled: bool = False
    compiled_on_correct_instance: bool = False

class ReducerForensics(BaseModel):
    annotated_found: bool = False
    reducers_found: List[str] = []
    is_robust: bool = False

class GitForensics(BaseModel):
    commit_count: int = 0
    time_delta_seconds: float = 0
    development_pattern: str = "Unknown"
    commits: List[Dict[str, Any]] = []

class SafetyForensics(BaseModel):
    unsafe_calls_found: List[str] = []
    is_safe: bool = True

class RepoTools:
    @staticmethod
    def analyze_graph_structure(path: str) -> GraphForensics:
        """
        Performs deep AST parsing to verify StateGraph structure.
        """
        forensics = GraphForensics()
        try:
            with open(path, "r") as f:
                tree = ast.parse(f.read())
        except Exception:
            return forensics

        adjacency_map = {}
        
        class GraphVisitor(ast.NodeVisitor):
            def visit_Assign(self, node):
                # Detect StateGraph instantiation
                if isinstance(node.value, ast.Call):
                    if getattr(node.value.func, "id", None) == "StateGraph":
                        forensics.state_graph_instance_found = True
                        if isinstance(node.targets[0], ast.Name):
                            forensics.graph_variable_name = node.targets[0].id
                self.generic_visit(node)

            def visit_Call(self, node):
                # Track builder.add_edge(src, dst)
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == "add_edge":
                        if len(node.args) >= 2:
                            src = self._get_val(node.args[0])
                            dst = self._get_val(node.args[1])
                            if src and dst:
                                forensics.edges.append({"src": src, "dst": dst})
                                adjacency_map.setdefault(src, []).append(dst)
                    
                    # Track conditional edges
                    elif node.func.attr == "add_conditional_edges":
                        forensics.conditional_edges_count += 1
                    
                    # Confirm .compile() on correct variable
                    elif node.func.attr == "compile":
                        forensics.is_compiled = True
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id == forensics.graph_variable_name:
                                forensics.compiled_on_correct_instance = True
                self.generic_visit(node)

            def _get_val(self, node):
                if isinstance(node, ast.Constant):
                    return str(node.value)
                if isinstance(node, ast.Name):
                    return node.id
                return None

        visitor = GraphVisitor()
        visitor.visit(tree)
        
        # Compute fan-out/fan-in
        if "START" in adjacency_map:
            forensics.fan_out_count = len(adjacency_map["START"])
            
        dest_counts = {}
        for edges in adjacency_map.values():
            for dst in edges:
                dest_counts[dst] = dest_counts.get(dst, 0) + 1
        
        forensics.fan_in_count = max(dest_counts.values()) if dest_counts else 0
        
        return forensics

    @staticmethod
    def verify_reducer_robustness(path: str) -> ReducerForensics:
        """
        Verifies use of Annotated and operator reducers.
        """
        forensics = ReducerForensics()
        try:
            with open(path, "r") as f:
                tree = ast.parse(f.read())
        except Exception:
            return forensics

        class ReducerVisitor(ast.NodeVisitor):
            def visit_AnnAssign(self, node):
                # Check for Annotated[...]
                if isinstance(node.annotation, ast.Subscript):
                    if getattr(node.annotation.value, "id", None) == "Annotated":
                        forensics.annotated_found = True
                        # Check for operator.add or operator.ior in arguments
                        for slice_item in self._get_slice_items(node.annotation.slice):
                            if isinstance(slice_item, ast.Attribute):
                                if slice_item.attr in ["add", "ior"]:
                                    forensics.reducers_found.append(slice_item.attr)
                self.generic_visit(node)

            def _get_slice_items(self, node):
                if isinstance(node, ast.Tuple):
                    return node.elts
                return [node]

        visitor = ReducerVisitor()
        visitor.visit(tree)
        
        if forensics.annotated_found and len(set(forensics.reducers_found)) >= 2:
            forensics.is_robust = True
            
        return forensics

    @staticmethod
    def verify_tool_safety(path: str) -> SafetyForensics:
        """
        Scans for unsafe Python functions (os.system, eval, exec).
        """
        forensics = SafetyForensics()
        unsafe_targets = {"os.system", "eval", "exec"}
        
        try:
            with open(path, "r") as f:
                tree = ast.parse(f.read())
        except Exception:
            return forensics

        class SafetyVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                func_name = self._get_name(node.func)
                if func_name in unsafe_targets:
                    forensics.unsafe_calls_found.append(func_name)
                    forensics.is_safe = False
                self.generic_visit(node)

            def _get_name(self, node):
                if isinstance(node, ast.Name):
                    return node.id
                if isinstance(node, ast.Attribute):
                    val = self._get_name(node.value)
                    if val:
                        return f"{val}.{node.attr}"
                return None

        visitor = SafetyVisitor()
        visitor.visit(tree)
        return forensics

    @staticmethod
    def extract_git_history(repo_path: str) -> GitForensics:
        """
        Extracts machine-readable git history and classifies development patterns.
        """
        forensics = GitForensics()
        try:
            # git log --pretty=format:%H|%cI|%s --reverse
            cmd = ["git", "-C", repo_path, "log", "--pretty=format:%H|%cI|%s", "--reverse"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=10)
            
            if result.returncode != 0:
                return forensics
                
            lines = result.stdout.strip().split("\n")
            if not lines or (len(lines) == 1 and not lines[0]):
                return forensics
                
            forensics.commit_count = len(lines)
            
            commit_data = []
            for line in lines:
                parts = line.split("|")
                if len(parts) >= 3:
                    commit_data.append({
                        "hash": parts[0],
                        "date": parts[1],
                        "summary": parts[2]
                    })
            
            forensics.commits = commit_data
            
            if len(commit_data) >= 2:
                first_date = datetime.fromisoformat(commit_data[0]["date"].replace("Z", "+00:00"))
                last_date = datetime.fromisoformat(commit_data[-1]["date"].replace("Z", "+00:00"))
                delta = (last_date - first_date).total_seconds()
                forensics.time_delta_seconds = delta
                
                if delta < 600: # 10 minutes
                    forensics.development_pattern = "Monolithic Dump"
                else:
                    forensics.development_pattern = "Iterative Development"
            else:
                forensics.development_pattern = "Single Commit Pattern"
                
        except Exception:
            pass
            
        return forensics
