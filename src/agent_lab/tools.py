from __future__ import annotations

import ast
import json
import operator
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class CalculatorError(ValueError):
    """Raised when an expression is not a safe arithmetic expression."""


_BINARY_OPERATORS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    ):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise CalculatorError("指数过大")
        return _BINARY_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
        return _UNARY_OPERATORS[type(node.op)](_evaluate(node.operand))
    raise CalculatorError("只支持数字和 + - * / % ** 运算")


def calculate(expression: str) -> str:
    """Evaluate a basic arithmetic expression without using eval()."""
    expression = expression.strip()
    if not expression or len(expression) > 200:
        raise CalculatorError("表达式为空或过长")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise CalculatorError("表达式语法错误") from exc
    try:
        value = _evaluate(tree)
    except ZeroDivisionError as exc:
        raise CalculatorError("除数不能为零") from exc
    except OverflowError as exc:
        raise CalculatorError("结果超出范围") from exc
    if value.is_integer():
        return str(int(value))
    return f"{value:.10g}"


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    func: Callable[[dict[str, Any]], str]

    def schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def _run_calculator(arguments: dict[str, Any]) -> str:
    expression = arguments.get("expression")
    if not isinstance(expression, str):
        raise CalculatorError("缺少 expression 参数")
    return calculate(expression)


CALCULATOR = Tool(
    name="calculator",
    description="计算基础算术表达式，支持 + - * / % ** 和括号。",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "要计算的表达式，例如 (12 + 8) * 3",
            }
        },
        "required": ["expression"],
    },
    func=_run_calculator,
)

TOOLS: dict[str, Tool] = {CALCULATOR.name: CALCULATOR}


def execute_tool(name: str, arguments: str) -> str:
    """Execute a registered tool and always return a string for the model."""
    tool = TOOLS.get(name)
    if tool is None:
        return f"错误：未知工具 {name}"
    try:
        parsed = json.loads(arguments or "{}")
        if not isinstance(parsed, dict):
            raise CalculatorError("参数必须是 JSON 对象")
        return tool.func(parsed)
    except ValueError as exc:
        return f"错误：{exc}"
