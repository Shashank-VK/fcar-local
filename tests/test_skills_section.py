"""Tests for Check 2: Skills-section verification (fcar-003)."""

import pytest
from fcar_local.checks import run_all_checks
from fcar_local.whitelist import load_whitelist


@pytest.fixture(scope="module")
def whitelist():
    return load_whitelist()


def test_clean_skills_section_passes(whitelist):
    """A clean skills section with verified skills passes."""
    resume_text = """SHASHANKAREDDY KARAMUDI
Bengaluru, Karnataka | +91 9980955236 | shashankvkaramudi51@gmail.com
github.com/Shashank-VK

TECHNICAL SKILLS
Python, Flask, FastAPI, Docker, SQL, PostgreSQL, pytest

EXPERIENCE
Development Intern | JB Arrow Star
Engineered backend modules.
"""
    result = run_all_checks(resume_text, whitelist)
    assert result.is_pass


def test_flask_passes_in_skills_section(whitelist):
    """Flask passes as a verified skill per attestation rule."""
    resume_text = """SHASHANKAREDDY KARAMUDI
Bengaluru, Karnataka | +91 9980955236 | shashankvkaramudi51@gmail.com
github.com/Shashank-VK

TECHNICAL SKILLS
Python, Flask, SQLAlchemy, SQLite, Docker

EXPERIENCE
Development Intern | JB Arrow Star
Backend modules.
"""
    result = run_all_checks(resume_text, whitelist)
    assert result.is_pass
    assert not any(f.token.lower() == "flask" for f in result.findings)


def test_unknown_token_kubernetes_fails_by_name(whitelist):
    """Skills section containing 'Kubernetes' fails naming it and reporting line."""
    resume_text = """SHASHANKAREDDY KARAMUDI
github.com/Shashank-VK

TECHNICAL SKILLS
Python, Kubernetes, Docker

EXPERIENCE
Development Intern | JB Arrow Star
"""
    result = run_all_checks(resume_text, whitelist)
    assert not result.is_pass
    skill_fails = [f for f in result.findings if f.check == "skills_section"]
    assert any("kubernetes" in f.token.lower() for f in skill_fails)
    assert any(f.line == 5 for f in skill_fails)


def test_skills_section_go_fails(whitelist):
    """'Go' claimed in the skills section fails as an unverified language claim."""
    resume_text = """SHASHANKAREDDY KARAMUDI
github.com/Shashank-VK

TECHNICAL SKILLS
Python, Go, Docker

EXPERIENCE
Development Intern | JB Arrow Star
"""
    result = run_all_checks(resume_text, whitelist)
    assert not result.is_pass
    skill_fails = [f for f in result.findings if f.check == "skills_section"]
    assert any(f.token == "Go" and f.line == 5 for f in skill_fails)


def test_no_skills_section_fails_by_default(whitelist):
    """A resume missing a skills section fails by default."""
    resume_text = """SHASHANKAREDDY KARAMUDI
github.com/Shashank-VK

EXPERIENCE
Development Intern | JB Arrow Star
Engineered backend modules.
"""
    result = run_all_checks(resume_text, whitelist, allow_no_skills=False)
    assert not result.is_pass
    assert any(f.check == "skills_section" and f.token == "<missing>" for f in result.findings)


def test_no_skills_section_passes_with_warning_when_allowed(whitelist):
    """With allow_no_skills=True, missing skills section downgrades to a printed warning."""
    resume_text = """SHASHANKAREDDY KARAMUDI
github.com/Shashank-VK

EXPERIENCE
Development Intern | JB Arrow Star
Engineered backend modules.
"""
    result = run_all_checks(resume_text, whitelist, allow_no_skills=True)
    assert result.is_pass
    assert len(result.warnings) == 1
    assert "Missing skills section" in result.warnings[0]


@pytest.mark.parametrize(
    "heading",
    [
        "TECHNICAL SKILLS",
        "Technical Skills:",
        "Skills",
        "Tech Stack",
        "Technologies",
        "Core Competencies",
        "## Technical Skills",
    ],
)
def test_various_skills_headings_recognized(whitelist, heading):
    """Skills section is recognized under all canonical heading variations."""
    resume_text = f"""SHASHANKAREDDY KARAMUDI
github.com/Shashank-VK

{heading}
Python, Docker, SQL, Flask

EXPERIENCE
Development Intern | JB Arrow Star
"""
    result = run_all_checks(resume_text, whitelist)
    assert result.is_pass, f"Heading '{heading}' failed to parse: {result.findings}"
