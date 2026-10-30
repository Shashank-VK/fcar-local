"""Tests for Check 3: Repo links and Jarvis rule (fcar-004)."""

import pytest
from fcar_local.checks import run_all_checks
from fcar_local.whitelist import load_whitelist


@pytest.fixture(scope="module")
def whitelist():
    return load_whitelist()


CLEAN_RESUME_BASE = """SHASHANKAREDDY KARAMUDI
Bengaluru, Karnataka | +91 9980955236 | shashankvkaramudi51@gmail.com
github.com/Shashank-VK

TECHNICAL SKILLS
Python, Flask, FastAPI, Docker

SELECTED PROJECTS
{projects}
"""


def test_known_repo_flask_ledger_api_passes(whitelist):
    """Link to known repo flask-ledger-api passes."""
    resume_text = CLEAN_RESUME_BASE.format(
        projects="Flask Ledger API — github.com/Shashank-VK/flask-ledger-api\n34 tests in the suite."
    )
    result = run_all_checks(resume_text, whitelist)
    assert result.is_pass


def test_invented_repo_slug_fails_naming_it(whitelist):
    """Link to an invented/unverified repo slug fails naming it and the line number."""
    resume_text = CLEAN_RESUME_BASE.format(
        projects="Quantum AI Engine — github.com/Shashank-VK/quantum-super-ai\n12 tests in the suite."
    )
    result = run_all_checks(resume_text, whitelist)
    assert not result.is_pass
    repo_fails = [f for f in result.findings if f.check == "repo_links"]
    assert any("quantum-super-ai" in f.token for f in repo_fails)
    assert any(f.line == 9 for f in repo_fails)


def test_jarvis_with_github_link_fails(whitelist):
    """Jarvis mention carrying a GitHub link fails."""
    resume_text = CLEAN_RESUME_BASE.format(
        projects="Jarvis — Voice Assistant — github.com/Shashank-VK/jarvis\nLocal voice assistant."
    )
    result = run_all_checks(resume_text, whitelist)
    assert not result.is_pass
    repo_fails = [f for f in result.findings if f.check == "repo_links"]
    assert len(repo_fails) >= 1
    assert any("jarvis" in f.token.lower() or "jarvis" in f.message.lower() for f in repo_fails)


def test_jarvis_alone_passes(whitelist):
    """Jarvis mention without a GitHub link passes (local-only project per PROJECT_LIST.md)."""
    resume_text = CLEAN_RESUME_BASE.format(
        projects="Jarvis — Voice Assistant\nLocal offline desktop voice assistant built in Python."
    )
    result = run_all_checks(resume_text, whitelist)
    assert result.is_pass, f"Expected Jarvis alone to pass, got: {result.findings}"
