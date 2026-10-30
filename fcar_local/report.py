"""Report formatters for human-readable and JSON output per specs.md."""

import json
from typing import Any, Dict

from fcar_local.checks import CheckResult


def format_human(result: CheckResult) -> str:
    """Format CheckResult for human console display."""
    lines = []
    if result.is_pass:
        lines.append("FCAR LOCAL: PASS")
        for warning in result.warnings:
            lines.append(f"WARNING: {warning}")
    else:
        lines.append("FCAR LOCAL: FAIL")
        for finding in result.findings:
            lines.append(
                f"- [{finding.check}] line {finding.line}: '{finding.token}' ({finding.message})"
            )
        for warning in result.warnings:
            lines.append(f"WARNING: {warning}")

    return "\n".join(lines)


def format_json(result: CheckResult, indent: int = 2) -> str:
    """Format CheckResult as a JSON string."""
    data: Dict[str, Any] = {
        "status": "PASS" if result.is_pass else "FAIL",
        "findings": [
            {
                "check": f.check,
                "token": f.token,
                "line": f.line,
                "message": f.message,
            }
            for f in result.findings
        ],
        "warnings": result.warnings,
    }
    return json.dumps(data, indent=indent)
