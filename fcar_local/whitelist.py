"""Whitelist loader and schema validator for fcar-local.

UNION CONTRACT: project_stacks entries are unioned into the global verified
skills set (mirroring the AGENTS.md FCAR rubric, which appends each project's
canonical stack as verified evidence). Consequence: a stack entry is a GLOBAL
claim. Every entry in whitelist.json must therefore be stated verbatim by a
declared source - an inference in one project's stack silently legitimises
that skill on every resume. FCAR audits the data file against the sources.
"""


import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class WhitelistError(Exception):
    """Raised when whitelist loading or schema validation fails."""
    pass


REQUIRED_KEYS = (
    "_meta",
    "verified_skills",
    "project_stacks",
    "known_repos",
    "forbidden_tokens",
)


@dataclass
class Whitelist:
    """Canonical verified whitelist data structure."""

    _meta: Dict[str, Any]
    verified_skills: List[str]
    project_stacks: Dict[str, List[str]]
    known_repos: List[str]
    forbidden_tokens: List[str]

    normalized_verified_skills: Set[str] = field(init=False)
    normalized_known_repos: Set[str] = field(init=False)

    def __post_init__(self) -> None:
        # Build normalized lookups for fast case-insensitive checks
        self.normalized_verified_skills = {
            s.strip().lower() for s in self.verified_skills if s and s.strip()
        }
        # Also include individual skills from project_stacks if not already present
        for stack in self.project_stacks.values():
            for item in stack:
                if item and item.strip():
                    self.normalized_verified_skills.add(item.strip().lower())

        self.normalized_known_repos = {
            r.strip().lower() for r in self.known_repos if r and r.strip()
        }

    def is_verified_skill(self, token: str) -> bool:
        """Check if a normalized token is recognized as a verified skill."""
        return token.strip().lower() in self.normalized_verified_skills

    def is_known_repo(self, slug: str) -> bool:
        """Check if a repository slug is recognized."""
        return slug.strip().lower() in self.normalized_known_repos


def get_default_whitelist_path() -> Path:
    """Return canonical path to whitelist.json next to the project root."""
    return Path(__file__).resolve().parent.parent / "whitelist.json"


def load_whitelist(path: Optional[Path | str] = None) -> Whitelist:
    """Load and validate whitelist.json from the specified path or default.

    Raises:
        WhitelistError: if the file cannot be found, is invalid JSON, or fails schema validation.
    """
    if path is None:
        target_path = get_default_whitelist_path()
    else:
        target_path = Path(path)

    if not target_path.is_file():
        raise WhitelistError(f"Whitelist file not found: {target_path}")

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise WhitelistError(f"Invalid JSON in whitelist '{target_path}': {exc}") from exc
    except Exception as exc:
        raise WhitelistError(f"Error reading whitelist '{target_path}': {exc}") from exc

    if not isinstance(data, dict):
        raise WhitelistError(f"Whitelist root must be a JSON object, got {type(data).__name__}")

    for key in REQUIRED_KEYS:
        if key not in data:
            raise WhitelistError(f"Whitelist missing required top-level key: '{key}'")

    if not isinstance(data["_meta"], dict):
        raise WhitelistError("Key '_meta' must be an object")

    if not isinstance(data["verified_skills"], list):
        raise WhitelistError("Key 'verified_skills' must be a list")

    if not isinstance(data["project_stacks"], dict):
        raise WhitelistError("Key 'project_stacks' must be an object")

    if not isinstance(data["known_repos"], list):
        raise WhitelistError("Key 'known_repos' must be a list")

    if not isinstance(data["forbidden_tokens"], list):
        raise WhitelistError("Key 'forbidden_tokens' must be a list")

    return Whitelist(
        _meta=data["_meta"],
        verified_skills=data["verified_skills"],
        project_stacks=data["project_stacks"],
        known_repos=data["known_repos"],
        forbidden_tokens=data["forbidden_tokens"],
    )
