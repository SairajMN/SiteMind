from __future__ import annotations

import ast
import builtins
import re
from typing import Any

_ALLOWED_IMPORTS = frozenset({"math", "statistics", "json", "re"})
_FORBIDDEN_NAMES = frozenset(
    {
        "open",
        "exec",
        "eval",
        "__import__",
        "compile",
        "input",
        "breakpoint",
        "exit",
        "quit",
        "help",
        "license",
        "copyright",
        "credits",
    }
)


class SandboxError(ValueError):
    pass


def _safe_import(name: str, *args: Any, **kwargs: Any) -> Any:
    if name not in _ALLOWED_IMPORTS:
        raise SandboxError(f"Import not allowed: {name}")
    return builtins.__import__(name, *args, **kwargs)


def _validate_ast(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split(".")[0]
                if base not in _ALLOWED_IMPORTS:
                    raise SandboxError(f"Import not allowed: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] not in _ALLOWED_IMPORTS:
                raise SandboxError(f"Import not allowed: {node.module}")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in _FORBIDDEN_NAMES:
                raise SandboxError(f"Call not allowed: {node.func.id}")


def extract_python(code: str) -> str:
    match = re.search(r"```python\s*(.*?)```", code, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return code.strip()


def execute_coder(code: str, context: dict[str, Any]) -> dict[str, Any]:
    """Run Coder-emitted Python with solve(context) entrypoint."""
    source = extract_python(code)
    tree = ast.parse(source, mode="exec")
    _validate_ast(tree)

    import math
    import statistics

    safe_builtins = {
        "abs": abs,
        "min": min,
        "max": max,
        "len": len,
        "sum": sum,
        "sorted": sorted,
        "round": round,
        "range": range,
        "list": list,
        "dict": dict,
        "float": float,
        "int": int,
        "str": str,
        "bool": bool,
        "True": True,
        "False": False,
        "None": None,
    }
    namespace: dict[str, Any] = {
        "__builtins__": safe_builtins,
        "__import__": _safe_import,
        "math": math,
        "statistics": statistics,
    }

    exec(compile(tree, "<coder>", "exec"), namespace)  # noqa: S102 — intentional sandbox

    solve = namespace.get("solve")
    if not callable(solve):
        raise SandboxError("Code must define solve(context)")

    result = solve(context)
    if not isinstance(result, dict):
        return {"result": result}
    return result
