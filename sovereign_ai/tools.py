import ast
import csv
import hashlib
import operator
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from .deliverables import DeliverableService
from .sandbox import DockerSandbox


class Calculator:
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}

    def calculate(self, expression):
        return self._evaluate(ast.parse(expression, mode="eval").body)

    def _evaluate(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.operations:
            return self.operations[type(node.op)](self._evaluate(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in self.operations:
            right = self._evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10: raise ValueError("Exponent is too large")
            return self.operations[type(node.op)](self._evaluate(node.left), right)
        raise ValueError("Only numeric arithmetic is allowed")


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict
    permissions: tuple
    risk_level: str
    timeout: int
    execute: object


class ToolRegistry:
    """Explicit allow-list for local tools; agents cannot call arbitrary functions."""

    def __init__(self, file_service=None, db=None, workspace=None):
        self.calculator = Calculator(); self.file_service = file_service; self.db = db
        self.workspace = Path(workspace or (file_service.storage_dir if file_service else Path.cwd())).resolve(); self.workspace.mkdir(parents=True, exist_ok=True)
        self.deliverables = DeliverableService(self.workspace)
        self.sandbox = DockerSandbox()
        self._tools = {}; self._register_defaults()

    def register_tool(self, tool):
        if tool.name in self._tools: raise ValueError("Tool already registered: " + tool.name)
        self._tools[tool.name] = tool

    def get_tool(self, name):
        if name not in self._tools: raise KeyError("Unknown tool: " + name)
        return self._tools[name]

    def list_tools(self): return list(self._tools.values())

    def validate_input(self, tool, arguments):
        missing = [name for name in tool.input_schema.get("required", []) if name not in arguments]
        if missing: raise ValueError("Missing required inputs: " + ", ".join(missing))

    def check_permission(self, tool, permission="read", approved=False):
        if permission not in tool.permissions: raise PermissionError(f"Permission '{permission}' denied for {tool.name}")
        if tool.risk_level == "HIGH" and not approved: raise PermissionError(f"Human approval required for high-risk tool: {tool.name}")

    def execute_tool(self, name, arguments, permission="read", approved=False, task_id=None, agent="jarvis"):
        tool = self.get_tool(name); started = time.monotonic()
        try:
            self.validate_input(tool, arguments); self.check_permission(tool, permission, approved)
            result = {"success": True, "tool": name, "result": tool.execute(arguments)}
        except Exception as exc:
            result = {"success": False, "tool": name, "error": str(exc)}
        result["duration_ms"] = round((time.monotonic() - started) * 1000); self._audit(task_id, agent, tool, arguments, result); return result

    def execute(self, request):
        match = re.search(r"(?:calculate|compute)\s+([0-9+*/().%\s-]+)", request, re.I)
        if match:
            result = self.execute_tool("calculate", {"expression": match.group(1).strip()})
            return "Calculator result: " + str(result["result"]) if result["success"] else None
        file_match = re.search(r"create\s+(?:a\s+)?file\s+(?:named|called)\s+([\w.-]+)(?:\s+containing\s*:\s*(.*))?", request, re.I)
        if file_match:
            result = self.execute_tool("write_file", {"path": file_match.group(1), "content": file_match.group(2) or ""}, permission="write")
            return "Created local workspace file: " + str(result["result"]) if result["success"] else "Tool failure: " + result["error"]
        folder_match = re.search(r"create\s+(?:a\s+)?(?:folder|directory)\s+(?:named|called)\s+([\w.-]+)", request, re.I)
        if folder_match:
            result = self.execute_tool("create_directory", {"path": folder_match.group(1)}, permission="write")
            return "Created local workspace folder: " + str(result["result"]) if result["success"] else "Tool failure: " + result["error"]
        return None

    def _safe_path(self, value):
        path = (self.workspace / value).resolve()
        if path != self.workspace and self.workspace not in path.parents: raise PermissionError("Path escapes the approved workspace")
        return path

    def _register_defaults(self):
        self.register_tool(Tool("calculate", "Deterministic arithmetic", {"required": ["expression"]}, ("read",), "LOW", 5, lambda a: self.calculator.calculate(a["expression"])))
        self.register_tool(Tool("read_file", "Read an approved local text file", {"required": ["path"]}, ("read",), "LOW", 10, lambda a: self._safe_path(a["path"]).read_text(encoding="utf-8")))
        self.register_tool(Tool("write_file", "Write a text deliverable", {"required": ["path", "content"]}, ("write",), "MEDIUM", 10, self._write))
        self.register_tool(Tool("move_file", "Move a file within the workspace", {"required": ["source", "destination"]}, ("write",), "MEDIUM", 10, self._move))
        self.register_tool(Tool("copy_file", "Copy a file within the workspace", {"required": ["source", "destination"]}, ("read", "write"), "MEDIUM", 10, self._copy))
        self.register_tool(Tool("create_directory", "Create a workspace directory", {"required": ["path"]}, ("write",), "MEDIUM", 10, lambda a: str(self._safe_path(a["path"]).mkdir(parents=True, exist_ok=True) or self._safe_path(a["path"]))))
        self.register_tool(Tool("search_files", "Search text in workspace files", {"required": ["query"]}, ("read",), "LOW", 10, self._search))
        self.register_tool(Tool("csv_summary", "Summarize a local CSV", {"required": ["path"]}, ("read",), "LOW", 10, self._csv_summary))
        self.register_tool(Tool("delete_file", "Delete a workspace file", {"required": ["path"]}, ("delete",), "HIGH", 10, lambda a: str(self._safe_path(a["path"]).unlink() or self._safe_path(a["path"]))))
        self.register_tool(Tool("generate_txt", "Generate a local text deliverable", {"required": ["name", "content"]}, ("write",), "MEDIUM", 10, lambda a: self.deliverables.text(self._artifact_name(a["name"]), a["content"])))
        self.register_tool(Tool("generate_csv", "Generate a local CSV deliverable", {"required": ["name", "headers", "rows"]}, ("write",), "MEDIUM", 10, lambda a: self.deliverables.csv(self._artifact_name(a["name"]), a["headers"], a["rows"])))
        self.register_tool(Tool("generate_xlsx", "Generate a local spreadsheet deliverable", {"required": ["name", "sheet", "headers", "rows"]}, ("write",), "MEDIUM", 10, lambda a: self.deliverables.xlsx(self._artifact_name(a["name"]), a["sheet"], a["headers"], a["rows"])))
        self.register_tool(Tool("generate_docx", "Generate a local DOCX deliverable", {"required": ["name", "title", "paragraphs"]}, ("write",), "MEDIUM", 10, lambda a: self.deliverables.docx(self._artifact_name(a["name"]), a["title"], a["paragraphs"])))
        self.register_tool(Tool("generate_pptx", "Generate a local PPTX deliverable", {"required": ["name", "title", "body"]}, ("write",), "MEDIUM", 10, lambda a: self.deliverables.pptx(self._artifact_name(a["name"]), a["title"], a["body"])))
        self.register_tool(Tool("execute_python", "Execute code in the isolated Docker sandbox", {"required": ["code"]}, ("execute",), "HIGH", 30, self._sandbox_result))

    def _sandbox_result(self, arguments):
        result = self.sandbox.run(arguments["code"], arguments.get("files"))
        return {"success": result.success, "stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code, "timed_out": result.timed_out, "error": result.error}

    def _write(self, args):
        path = self._safe_path(args["path"]); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(args["content"], encoding="utf-8"); return str(path)

    def _move(self, args):
        source, destination = self._safe_path(args["source"]), self._safe_path(args["destination"])
        if not source.is_file(): raise FileNotFoundError(args["source"])
        destination.parent.mkdir(parents=True, exist_ok=True); return str(shutil.move(str(source), str(destination)))

    def _copy(self, args):
        source, destination = self._safe_path(args["source"]), self._safe_path(args["destination"])
        if not source.is_file(): raise FileNotFoundError(args["source"])
        destination.parent.mkdir(parents=True, exist_ok=True); return str(shutil.copy2(source, destination))

    def _artifact_name(self, name):
        path = self._safe_path(name)
        return str(path.relative_to(self.workspace))

    def _search(self, args):
        return [{"path": str(path.relative_to(self.workspace)), "matches": path.read_text(encoding="utf-8", errors="ignore").count(args["query"])} for path in self.workspace.rglob("*") if path.is_file() and args["query"] in path.read_text(encoding="utf-8", errors="ignore")]

    def _csv_summary(self, args):
        with self._safe_path(args["path"]).open(newline="", encoding="utf-8") as stream: rows = list(csv.DictReader(stream))
        return {"rows": len(rows), "columns": list(rows[0]) if rows else []}

    def _audit(self, task_id, agent, tool, arguments, result):
        if self.db: self.db.execute("INSERT INTO audit_events(username,action,details) VALUES(?,?,?)", (agent, "tool_invocation", str({"task_id": task_id, "tool": tool.name, "risk_level": tool.risk_level, "input_hash": hashlib.sha256(str(arguments).encode()).hexdigest(), "success": result["success"], "duration_ms": result["duration_ms"]})))
