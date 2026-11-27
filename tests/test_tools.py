import pytest

from agent_lab.tools import CalculatorError, calculate, execute_tool


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("1 + 1", "2"),
        ("(12 + 8) * 3", "60"),
        ("2 ** 10", "1024"),
        ("7 / 2", "3.5"),
    ],
)
def test_calculate(expression: str, expected: str) -> None:
    assert calculate(expression) == expected


def test_calculate_rejects_code() -> None:
    with pytest.raises(CalculatorError):
        calculate("__import__('os').system('echo hi')")


def test_calculate_rejects_bad_syntax() -> None:
    with pytest.raises(CalculatorError):
        calculate("1 +")


def test_calculate_rejects_division_by_zero() -> None:
    with pytest.raises(CalculatorError):
        calculate("1 / 0")


def test_calculate_rejects_boolean() -> None:
    with pytest.raises(CalculatorError):
        calculate("True")


def test_execute_tool_reports_bad_json() -> None:
    result = execute_tool("calculator", "{not-json}")
    assert result.startswith("错误：")


def test_execute_tool_reports_unknown_tool() -> None:
    result = execute_tool("missing", "{}")
    assert result == "错误：未知工具 missing"
