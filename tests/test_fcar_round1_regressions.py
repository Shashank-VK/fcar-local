"""Regression tests for the FCAR round-1 findings (2026-10-23).

Each test pins one reviewer finding: a matcher evasion, a false positive,
a heading-parse bug, or a pruned whitelist entry.
"""

import pytest
from fcar_local.checks import run_all_checks
from fcar_local.whitelist import load_whitelist


@pytest.fixture(scope="module")
def whitelist():
    return load_whitelist()


BASE = """SHASHANKAREDDY KARAMUDI
github.com/Shashank-VK

TECHNICAL SKILLS
Python, Flask, Docker

SELECTED PROJECTS
VoicePilot - github.com/Shashank-VK/voicepilot
{claim}
"""


def _checks(result, name):
    return [f for f in result.findings if f.check == name]


@pytest.mark.parametrize("claim", [
    "Built the UI in ReactJS for internal tooling",
    "Built the UI in React.js for internal tooling",
    "Modern C++20 services in production",
    "Used HuggingFace models for embeddings",
])
def test_forbidden_spelling_variants_fail(whitelist, claim):
    result = run_all_checks(BASE.format(claim=claim), whitelist)
    assert _checks(result, "forbidden_tokens"), claim


@pytest.mark.parametrize("claim", [
    "Wrote Reactive form handling in vanilla JS",   # 'Reactive' is not 'React'
    "I excel at debugging distributed systems",     # lowercase verb, honest prose
    "Available 24/7 for on-call rotations",          # bare ratio, not a test claim
])
def test_innocent_lookalikes_pass(whitelist, claim):
    result = run_all_checks(BASE.format(claim=claim), whitelist)
    assert result.is_pass, (claim, result.findings)


def test_excel_as_skill_claim_fails(whitelist):
    result = run_all_checks(BASE.format(claim="Proficient in Excel and Python"), whitelist)
    assert _checks(result, "forbidden_tokens")


def test_heading_with_suffix_words_parses(whitelist):
    text = BASE.replace("TECHNICAL SKILLS\nPython, Flask, Docker",
                        "Skills & Tools: Python, Flask, Docker")
    result = run_all_checks(text, whitelist)
    assert result.is_pass, result.findings
    text2 = BASE.replace("TECHNICAL SKILLS\nPython, Flask, Docker",
                         "Technologies Used: Python, Flask, Docker")
    result2 = run_all_checks(text2, whitelist)
    assert result2.is_pass, result2.findings


def test_multi_space_separated_skills_pass(whitelist):
    text = BASE.replace("Python, Flask, Docker", "Python   Docker   PostgreSQL")
    result = run_all_checks(text, whitelist)
    assert result.is_pass, result.findings


def test_jarvis_with_bare_link_on_next_line_fails(whitelist):
    text = BASE.format(claim="Jarvis - local voice assistant\ngithub.com/Shashank-VK/voicepilot")
    result = run_all_checks(text, whitelist)
    assert _checks(result, "repo_links")


@pytest.mark.parametrize("pruned", ["Java", "Prisma", "NumPy", "Big Data", "Git", "Linux"])
def test_pruned_entries_absent(whitelist, pruned):
    assert pruned not in whitelist.verified_skills
    for stack in whitelist.project_stacks.values():
        assert pruned not in stack
