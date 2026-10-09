"""Deterministic Python Sandbox Adapter: Isolated execution of math, NumPy, and SymPy."""

import sys
import os
import ast
import json
import time
import subprocess
import tempfile
from typing import Dict, Any, Optional, Tuple, Set

from privearch.schemas import ToolCallResult
from privearch.tools.base import BaseToolAdapter


# Disallowed modules and builtins for sandboxed safety
DISALLOWED_MODULES: Set[str] = {
    "socket", "http", "urllib", "requests", "paramiko", "telnetlib",
    "ftplib", "subprocess", "ctypes", "multiprocessing", "threading",
    "pty", "winreg"
}

DISALLOWED_CALLS: Set[str] = {
    "os.system", "os.popen", "os.remove", "os.unlink", "os.rmdir",
    "shutil.rmtree", "eval", "exec", "__import__", "compile"
}


class ASTSecurityAuditor(ast.NodeVisitor):
    """AST visitor that checks for disallowed operations in Python scripts."""
    def __init__(self, strict: bool = True):
        self.strict = strict
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            root_mod = alias.name.split('.')[0]
            if root_mod in DISALLOWED_MODULES:
                self.violations.append(f"Import of disallowed module: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            root_mod = node.module.split('.')[0]
            if root_mod in DISALLOWED_MODULES:
                self.violations.append(f"Import from disallowed module: '{node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Detect calls like os.system()
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                full_name = f"{node.func.value.id}.{node.func.attr}"
                if full_name in DISALLOWED_CALLS:
                    self.violations.append(f"Disallowed function call: '{full_name}'")
        elif isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "compile", "__import__"}:
                self.violations.append(f"Disallowed builtin call: '{node.func.id}'")
        self.generic_visit(node)


class PythonSandboxAdapter(BaseToolAdapter):
    """
    Executes mathematical and scientific Python code deterministically.
    Pre-configured with NumPy, SciPy, SymPy, and Matplotlib.
    """

    def __init__(self, default_timeout: float = 6.0, strict_sandbox: bool = True):
        self.default_timeout = default_timeout
        self.strict_sandbox = strict_sandbox

    @property
    def name(self) -> str:
        return "python_sandbox"

    @property
    def description(self) -> str:
        return (
            "Deterministic scientific execution environment with SymPy, NumPy, "
            "SciPy, and Matplotlib for non-hallucinatory mathematical computations."
        )

    def is_available(self) -> bool:
        """Check if python and core scientific libraries can be imported."""
        try:
            import numpy
            import sympy
            return True
        except ImportError:
            return False

    def validate_code_safety(self, code: str) -> Tuple[bool, str]:
        """Parse code into AST and check for unsafe calls."""
        if not self.strict_sandbox:
            return True, ""
        try:
            tree = ast.parse(code)
            auditor = ASTSecurityAuditor(strict=True)
            auditor.visit(tree)
            if auditor.violations:
                return False, "; ".join(auditor.violations)
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax Error: {e}"

    def execute(self, params: Dict[str, Any]) -> ToolCallResult:
        """
        Execute python script or expression.
        params:
          - code: Python code string to run
          - timeout: Max execution seconds (default 6.0)
          - return_variables: Optional list of variable names to retrieve
        """
        code = params.get("code", "").strip()
        timeout = float(params.get("timeout", self.default_timeout))
        return_vars = params.get("return_variables", [])

        if not code:
            return ToolCallResult(
                tool_name=self.name,
                success=False,
                error="No code provided for execution."
            )

        # 1. AST Security Audit
        safe, reason = self.validate_code_safety(code)
        if not safe:
            return ToolCallResult(
                tool_name=self.name,
                success=False,
                error=f"Security Violation: {reason}",
                metadata={"security_flag": True}
            )

        # 2. Build execution payload with scientific prelude and serialization wrapper
        runner_script = self._wrap_code_for_execution(code, return_vars)

        t_start = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, "-c", runner_script],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            elapsed_ms = round((time.time() - t_start) * 1000, 2)

            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()

            if proc.returncode != 0:
                return ToolCallResult(
                    tool_name=self.name,
                    success=False,
                    stdout=stdout,
                    stderr=stderr,
                    execution_time_ms=elapsed_ms,
                    error=stderr or f"Process exited with code {proc.returncode}"
                )

            # Try parsing serialized JSON output if present
            output_data = stdout
            metadata = {}
            if "__PRIVEARCH_OUTPUT_JSON__" in stdout:
                parts = stdout.split("__PRIVEARCH_OUTPUT_JSON__")
                stdout_clean = parts[0].strip()
                try:
                    payload = json.loads(parts[1].strip())
                    output_data = payload.get("result", stdout_clean)
                    metadata = payload.get("variables", {})
                    stdout = stdout_clean
                except json.JSONDecodeError:
                    pass

            return ToolCallResult(
                tool_name=self.name,
                success=True,
                output=output_data,
                stdout=stdout,
                stderr=stderr,
                execution_time_ms=elapsed_ms,
                metadata=metadata
            )

        except subprocess.TimeoutExpired:
            return ToolCallResult(
                tool_name=self.name,
                success=False,
                error=f"Execution timed out after {timeout} seconds.",
                execution_time_ms=round(timeout * 1000, 2)
            )
        except Exception as ex:
            return ToolCallResult(
                tool_name=self.name,
                success=False,
                error=str(ex),
                execution_time_ms=round((time.time() - t_start) * 1000, 2)
            )

    def evaluate_expression(self, expression: str, variables: Optional[Dict[str, Any]] = None) -> ToolCallResult:
        """
        Evaluate a single mathematical or symbolic expression.
        Variables are pre-populated as floats or SymPy symbols.
        """
        var_assignments = []
        if variables:
            for k, v in variables.items():
                if isinstance(v, (int, float)):
                    var_assignments.append(f"{k} = {v}")
                else:
                    var_assignments.append(f"{k} = {repr(v)}")

        var_code = "\n".join(var_assignments)
        code = f"{var_code}\n_ans = {expression}\nprint(_ans)"
        params = {"code": code, "return_variables": ["_ans"]}
        res = self.execute(params)
        if res.success and "_ans" in res.metadata:
            res.output = res.metadata["_ans"]
        return res

    def _wrap_code_for_execution(self, user_code: str, return_vars: list) -> str:
        """Prepend scientific prelude and append output serialization using base64 wrapper."""
        import base64
        encoded_user_code = base64.b64encode(user_code.encode("utf-8")).decode("ascii")
        escaped_vars = json.dumps(return_vars)
        wrapper = f'''
import sys
import json
import base64
import math
import numpy as np
import scipy
import sympy as sp

# Scientific prelude
globals().update({{"np": np, "sp": sp, "math": math}})

__captured_vars = {{}}
__last_result = None

try:
    _scope = globals()
    _raw_code = base64.b64decode("{encoded_user_code}").decode("utf-8")
    exec(_raw_code, _scope)

    # Collect requested variables
    for _var in {escaped_vars}:
        if _var in _scope:
            val = _scope[_var]
            if hasattr(val, "evalf"):
                try:
                    val = float(val.evalf())
                except Exception:
                    val = str(val)
            elif isinstance(val, (np.integer, np.floating)):
                val = float(val)
            elif isinstance(val, np.ndarray):
                val = val.tolist()
            __captured_vars[_var] = val

    if "_ans" in _scope:
        __last_result = _scope["_ans"]
        if hasattr(__last_result, "evalf"):
            try:
                __last_result = float(__last_result.evalf())
            except Exception:
                __last_result = str(__last_result)
        elif isinstance(__last_result, (np.integer, np.floating)):
            __last_result = float(__last_result)

    print("__PRIVEARCH_OUTPUT_JSON__")
    print(json.dumps({{"result": __last_result, "variables": __captured_vars}}))

except Exception as _e:
    import traceback
    sys.stderr.write(traceback.format_exc())
    sys.exit(1)
'''
        return wrapper

