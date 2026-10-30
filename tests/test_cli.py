"""Tests for CLI contract and execution timing (fcar-006)."""

import json
from pathlib import Path
import subprocess
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLI_PATH = PROJECT_ROOT / "fcar_check.py"
CLEAN_FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "clean_resume.txt"


def run_cli(args: list[str], stdin_data: str | None = None) -> subprocess.CompletedProcess:
    """Helper to run fcar_check.py as a subprocess with the active python interpreter."""
    cmd = [sys.executable, str(CLI_PATH)] + args
    return subprocess.run(
        cmd,
        input=stdin_data,
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
    )


def test_cli_pass_exit_code_zero():
    """CLI exits with code 0 on a clean passing resume."""
    proc = run_cli([str(CLEAN_FIXTURE)])
    assert proc.returncode == 0
    assert "FCAR LOCAL: PASS" in proc.stdout


def test_cli_fail_exit_code_one(tmp_path: Path):
    """CLI exits with code 1 on a resume that violates rules."""
    failing_resume = tmp_path / "failing_resume.txt"
    failing_resume.write_text(
        """SHASHANKAREDDY KARAMUDI
TECHNICAL SKILLS
Python, React, Docker
EXPERIENCE
JB Arrow Star
""",
        encoding="utf-8",
    )
    proc = run_cli([str(failing_resume)])
    assert proc.returncode == 1
    assert "FCAR LOCAL: FAIL" in proc.stdout
    assert "React" in proc.stdout


def test_cli_missing_file_exit_code_two():
    """CLI exits with code 2 when resume file does not exist."""
    proc = run_cli(["/tmp/definitely_missing_file_xyz_987.txt"])
    assert proc.returncode == 2
    assert "not found" in proc.stderr.lower()


def test_cli_invalid_argument_exit_code_two():
    """CLI exits with code 2 on unknown flags or usage errors."""
    proc = run_cli(["--unrecognized-flag"])
    assert proc.returncode == 2


def test_cli_invalid_whitelist_exit_code_two(tmp_path: Path):
    """CLI exits with code 2 if specified whitelist is invalid."""
    bad_wl = tmp_path / "bad_wl.json"
    bad_wl.write_text("{}", encoding="utf-8")
    proc = run_cli([str(CLEAN_FIXTURE), "--whitelist", str(bad_wl)])
    assert proc.returncode == 2
    assert "Whitelist error" in proc.stderr


def test_cli_stdin_support():
    """CLI reads from stdin when '-' is provided as filename."""
    content = CLEAN_FIXTURE.read_text(encoding="utf-8")
    proc = run_cli(["-"], stdin_data=content)
    assert proc.returncode == 0
    assert "FCAR LOCAL: PASS" in proc.stdout


def test_cli_json_mode(tmp_path: Path):
    """CLI with --json emits valid JSON reporting pass or fail."""
    # Test PASS JSON
    proc = run_cli([str(CLEAN_FIXTURE), "--json"])
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["status"] == "PASS"
    assert data["findings"] == []

    # Test FAIL JSON
    bad_file = tmp_path / "bad.txt"
    bad_file.write_text("TECHNICAL SKILLS\nKubernetes\n", encoding="utf-8")
    proc_fail = run_cli([str(bad_file), "--json"])
    assert proc_fail.returncode == 1
    data_fail = json.loads(proc_fail.stdout)
    assert data_fail["status"] == "FAIL"
    assert len(data_fail["findings"]) > 0
    assert any("Kubernetes" in f["token"] for f in data_fail["findings"])


def test_cli_allow_no_skills_flag(tmp_path: Path):
    """CLI with --allow-no-skills passes a resume without skills section with exit 0."""
    no_skills_file = tmp_path / "no_skills.txt"
    no_skills_file.write_text("SHASHANKAREDDY KARAMUDI\nEXPERIENCE\nDev\n", encoding="utf-8")

    # Without flag: exit 1
    proc_fail = run_cli([str(no_skills_file)])
    assert proc_fail.returncode == 1

    # With flag: exit 0 and prints warning
    proc_pass = run_cli([str(no_skills_file), "--allow-no-skills"])
    assert proc_pass.returncode == 0
    assert "FCAR LOCAL: PASS" in proc_pass.stdout
    assert "WARNING:" in proc_pass.stdout


def test_cli_timing_under_one_second():
    """Timing verification: CLI run on resume-sized fixture must execute in < 1s."""
    start_time = time.perf_counter()
    proc = run_cli([str(CLEAN_FIXTURE)])
    elapsed = time.perf_counter() - start_time

    assert proc.returncode == 0
    assert elapsed < 1.0, f"CLI took {elapsed:.3f}s, expected < 1.0s"
