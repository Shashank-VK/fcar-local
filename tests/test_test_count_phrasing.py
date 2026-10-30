"""Tests for Check 4: Test-count phrasing rule (fcar-005)."""

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
Python, Flask, Docker

SELECTED PROJECTS
VoicePilot — github.com/Shashank-VK/voicepilot
{claim}

EDUCATION
B.Tech CSE | CMR University — CGPA 8.9/10 | Expected 2027
"""


def test_twenty_three_over_twenty_three_passing_fails(whitelist):
    """'23/23 passing' phrasing fails with exact token and line number."""
    resume_text = CLEAN_RESUME_BASE.format(claim="23/23 passing at push. STT to LLM pipeline.")
    result = run_all_checks(resume_text, whitelist)
    assert not result.is_pass
    tc_fails = [f for f in result.findings if f.check == "test_count_phrasing"]
    assert len(tc_fails) >= 1
    assert any("23/23" in f.token for f in tc_fails)
    assert any(f.line == 10 for f in tc_fails)


@pytest.mark.parametrize(
    "banned_claim",
    [
        "23/23 passing",
        "23/23 tests",
        "43/43 passing at push",
    ],
)
def test_banned_ratio_phrasing_fails(whitelist, banned_claim):
    """'N/N passing|tests|passed' phrasing fails (specs.md section 4)."""
    resume_text = CLEAN_RESUME_BASE.format(claim=banned_claim)
    result = run_all_checks(resume_text, whitelist)
    assert not result.is_pass
    assert any(f.check == "test_count_phrasing" for f in result.findings)


def test_twenty_three_tests_in_the_suite_passes(whitelist):
    """'23 tests in the suite' is the honest phrasing and passes cleanly."""
    resume_text = CLEAN_RESUME_BASE.format(claim="23 tests in the suite. Comprehensive unit tests.")
    result = run_all_checks(resume_text, whitelist)
    assert result.is_pass, f"Expected '23 tests in the suite' to pass, got: {result.findings}"


def test_cgpa_decimal_and_dates_do_not_false_trigger(whitelist):
    """Numbers like 'CGPA 8.9/10' or dates must not trigger test count phrasing failures."""
    resume_text = CLEAN_RESUME_BASE.format(
        claim="Engineered system from 09/2024 to 12/2025. 43 tests in the suite."
    )
    result = run_all_checks(resume_text, whitelist)
    assert result.is_pass, f"Expected no false triggers, got: {result.findings}"


@pytest.mark.parametrize(
    "ok_claim",
    [
        "Full test suite: 28/28 verified",   # bare ratio, no banned suffix
        "Available 24/7 for support rotations",
        "Improved the eval score from 3/5 to 4/5",
    ],
)
def test_bare_ratios_pass(whitelist, ok_claim):
    """A bare N/N ratio is not a test-count claim and must pass (FCAR round 1)."""
    resume_text = CLEAN_RESUME_BASE.format(claim=ok_claim)
    result = run_all_checks(resume_text, whitelist)
    assert not any(f.check == "test_count_phrasing" for f in result.findings), result.findings
