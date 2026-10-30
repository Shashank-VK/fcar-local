"""Tests for whitelist loader and data schema (fcar-001)."""

import json
from pathlib import Path
import pytest

from fcar_local.whitelist import WhitelistError, load_whitelist, REQUIRED_KEYS


def test_load_default_whitelist():
    """Verify standard whitelist.json loads cleanly and validates."""
    wl = load_whitelist()
    assert wl._meta is not None
    assert len(wl.verified_skills) > 0
    assert len(wl.known_repos) > 0
    assert len(wl.forbidden_tokens) > 0
    assert "flask" in wl.normalized_verified_skills
    assert "voicepilot" in wl.normalized_known_repos


def test_flask_attestation_metadata():
    """Verify _meta object documents Flask attestation and canonical sources."""
    wl = load_whitelist()
    meta = wl._meta
    assert "sources" in meta
    assert any("AGENTS.md" in s for s in meta["sources"])
    assert any("PROJECT_LIST.md" in s for s in meta["sources"])
    assert "flask_attestation_rule" in meta
    assert "attestation" in meta["flask_attestation_rule"].lower()
    assert "2026-10-22" in meta["flask_attestation_rule"]


def test_data_review_skills_traceability():
    """Data review: verify that every verified skill traces to project stacks or canonical metadata."""
    wl = load_whitelist()
    # Skills from all project stacks
    stack_skills = {
        s.strip().lower()
        for stack in wl.project_stacks.values()
        for s in stack
    }
    # Skills verified without a per-project stack, each traced to a named source
    # (FCAR round 1, 2026-10-23: this set previously blessed invented entries -
    # java, git, linux, oop/solid, numpy, big data, prisma, express, supertest,
    # vitest, cd - which is why the FCAR data audit now owns this list):
    #   analytics        - PROJECT_LIST.md (Green Grid AI: "Pandas analytics")
    #   ci               - inventory (CI in .github: voicepilot/groundedqa/evalforge)
    #   dsa              - PROJECT_LIST.md / his CodeChef practice record
    #   machine learning - NPTEL "Introduction to Machine Learning" certification
    #   rest             - PROJECT_LIST.md / AGENTS.md (REST APIs across projects)
    #   voice ai         - PROJECT_LIST.md (VoicePilot category)
    general_canon = {
        "analytics", "ci", "dsa", "machine learning", "rest", "voice ai",
    }
    all_allowed = stack_skills | general_canon

    unmapped = []
    for skill in wl.verified_skills:
        norm = skill.strip().lower()
        if norm not in all_allowed:
            unmapped.append(skill)

    assert unmapped == [], f"Skills without traceable project or canonical backing: {unmapped}"


@pytest.mark.parametrize("missing_key", REQUIRED_KEYS)
def test_reject_missing_required_key(tmp_path: Path, missing_key: str):
    """Loader must validate schema and reject a whitelist missing any required key."""
    wl = load_whitelist()
    data = {
        "_meta": wl._meta,
        "verified_skills": wl.verified_skills,
        "project_stacks": wl.project_stacks,
        "known_repos": wl.known_repos,
        "forbidden_tokens": wl.forbidden_tokens,
    }
    del data[missing_key]

    test_file = tmp_path / "invalid_whitelist.json"
    test_file.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(WhitelistError, match=f"missing required top-level key: '{missing_key}'"):
        load_whitelist(test_file)


def test_reject_invalid_json(tmp_path: Path):
    """Loader rejects non-JSON or corrupted file."""
    bad_file = tmp_path / "corrupt.json"
    bad_file.write_text("{not valid json", encoding="utf-8")

    with pytest.raises(WhitelistError, match="Invalid JSON"):
        load_whitelist(bad_file)


def test_reject_missing_file():
    """Loader rejects non-existent whitelist path."""
    with pytest.raises(WhitelistError, match="not found"):
        load_whitelist("/tmp/nonexistent_whitelist_path_12345.json")
