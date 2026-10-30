#!/usr/bin/env python3
"""FCAR Local Check - CLI entry point per specs.md.

Usage:
    fcar_check.py <resume.txt|-> [--json] [--allow-no-skills] [--whitelist PATH]

Exit codes:
    0: PASS
    1: FAIL
    2: Usage or input error
"""

import argparse
from pathlib import Path
import sys

from fcar_local.checks import run_all_checks
from fcar_local.report import format_human, format_json
from fcar_local.whitelist import WhitelistError, load_whitelist


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="fcar_check.py",
        description="Deterministic offline pre-flight honesty checker for tailored resumes.",
    )
    parser.add_argument(
        "resume",
        help="Path to resume text file, or '-' to read from standard input.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_mode",
        help="Emit output formatted as JSON.",
    )
    parser.add_argument(
        "--allow-no-skills",
        action="store_true",
        dest="allow_no_skills",
        help="Downgrade missing skills section check from failure to a warning.",
    )
    parser.add_argument(
        "--whitelist",
        type=str,
        default=None,
        help="Path to custom whitelist.json (defaults to whitelist.json in project root).",
    )
    return parser.parse_args(argv)


def read_resume_text(target: str) -> str:
    """Read resume content from file or stdin."""
    if target == "-":
        try:
            return sys.stdin.read()
        except Exception as exc:
            sys.stderr.write(f"Error reading stdin: {exc}\n")
            sys.exit(2)

    resume_path = Path(target)
    if not resume_path.is_file():
        sys.stderr.write(f"Error: resume file not found: {target}\n")
        sys.exit(2)

    try:
        with open(resume_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as exc:
        sys.stderr.write(f"Error reading resume file '{target}': {exc}\n")
        sys.exit(2)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Parse arguments (argparse exits with code 2 on syntax/usage error)
    args = parse_args(argv)

    # Load whitelist
    try:
        whitelist = load_whitelist(args.whitelist)
    except WhitelistError as exc:
        sys.stderr.write(f"Whitelist error: {exc}\n")
        sys.exit(2)
    except Exception as exc:
        sys.stderr.write(f"Unexpected error loading whitelist: {exc}\n")
        sys.exit(2)

    # Read resume text
    text = read_resume_text(args.resume)

    # Run checks
    result = run_all_checks(
        text=text,
        whitelist=whitelist,
        allow_no_skills=args.allow_no_skills,
    )

    # Output report
    if args.json_mode:
        output = format_json(result)
    else:
        output = format_human(result)

    print(output)

    return 0 if result.is_pass else 1


if __name__ == "__main__":
    sys.exit(main())
