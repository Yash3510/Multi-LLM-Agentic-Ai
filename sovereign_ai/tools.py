import ast
import operator
import re


class Calculator:
    operations = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                  ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}

    def calculate(self, expression: str):
        return self._evaluate(ast.parse(expression, mode="eval").body)

    def _evaluate(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in self.operations:
            return self.operations[type(node.op)](self._evaluate(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in self.operations:
            right = self._evaluate(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Exponent is too large")
            return self.operations[type(node.op)](self._evaluate(node.left), right)
        raise ValueError("Only numeric arithmetic is allowed")


class ToolRegistry:
    """Allow-listed in-process tools; no shell or unrestricted host execution."""

    def __init__(self, file_service=None):
        self.calculator = Calculator()
        self.file_service = file_service

    def execute(self, request: str):
        match = re.search(r"(?:calculate|compute)\s+([0-9+*/().%\s-]+)", request, re.I)
        if match:
            return "Calculator result: " + str(self.calculator.calculate(match.group(1).strip()))
        return None
