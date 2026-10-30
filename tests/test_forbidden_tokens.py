"""Tests for Check 1: Forbidden-token scan (fcar-002)."""

import pytest
from fcar_local.checks import run_all_checks
from fcar_local.whitelist import load_whitelist


@pytest.fixture(scope="module")
def whitelist():
    return load_whitelist()


CLEAN_RESUME_TEMPLATE = """SHASHANKAREDDY KARAMUDI
Bengaluru, Karnataka | +91 9980955236 | shashankvkaramudi51@gmail.com
github.com/Shashank-VK

TECHNICAL SKILLS
Python, Flask, Docker, SQL, PostgreSQL

EXPERIENCE
Development Intern | JB Arrow Star
{extra_content}

SELECTED PROJECTS
VoicePilot — Voice AI Agent — github.com/Shashank-VK/voicepilot
43 tests in the suite. STT to LLM to TTS voice agent pipeline.
"""


@pytest.mark.parametrize(
    "token",
    [
        "React",
        "Golang",
        "C++",
        "C#",
        "Power BI",
        "PyTorch",
        "TensorFlow",
        "Hugging Face",
        "Excel",
        "Infyntrek",
    ],
)
def test_each_forbidden_token_fails_with_name_and_line(whitelist, token):
    """Resume fixtures containing each forbidden token fail naming that exact token + line."""
    resume_text = CLEAN_RESUME_TEMPLATE.format(
        extra_content=f"Led migration using {token} in production environments."
    )
    result = run_all_checks(resume_text, whitelist)

    assert not result.is_pass, f"Expected forbidden token '{token}' to fail"
    matches = [f for f in result.findings if f.check == "forbidden_tokens"]
    assert len(matches) >= 1
    # Check that token is named
    assert any(token.lower() == f.token.lower() for f in matches)
    # Check that line number corresponds to where extra_content is (line 10)
    assert any(f.line == 10 for f in matches)


def test_prose_go_passes(whitelist):
    """Prose uses of the word 'go' ('go-to-market', 'go live') pass without failing Check 1."""
    resume_text = CLEAN_RESUME_TEMPLATE.format(
        extra_content="Defined go-to-market architecture; assisted the engineering team to go live smoothly."
    )
    result = run_all_checks(resume_text, whitelist)
    assert result.is_pass, f"Expected prose 'go' to pass, got findings: {result.findings}"


def test_golang_fails_anywhere_in_text(whitelist):
    """'Golang' fails anywhere in the resume as a forbidden token."""
    resume_text = CLEAN_RESUME_TEMPLATE.format(
        extra_content="Engineered microservices using Golang."
    )
    result = run_all_checks(resume_text, whitelist)
    assert not result.is_pass
    findings = [f for f in result.findings if f.check == "forbidden_tokens"]
    assert any(f.token.lower() == "golang" and f.line == 10 for f in findings)


def test_token_boundary_precision(whitelist):
    """Words containing substrings of forbidden tokens (e.g. Reactor) must not false-trigger."""
    resume_text = CLEAN_RESUME_TEMPLATE.format(
        extra_content="Designed an event reactor pattern for network dispatch."
    )
    result = run_all_checks(resume_text, whitelist)
    assert result.is_pass, f"Did not expect 'reactor' to match 'React': {result.findings}"
