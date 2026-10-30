"""The four FCAR local deterministic checks per specs.md."""

from dataclasses import dataclass
import re
from typing import List, Optional, Tuple

from fcar_local.whitelist import Whitelist


@dataclass
class Finding:
    """Represents a single rule violation."""

    check: str
    token: str
    line: int
    message: str


@dataclass
class CheckResult:
    """Consolidated results of all checks on a resume."""

    findings: List[Finding]
    warnings: List[str]

    @property
    def is_pass(self) -> bool:
        """Returns True if there are zero findings."""
        return len(self.findings) == 0


# --- Check 1: Forbidden Tokens Scan ---

def _build_forbidden_pattern(token: str) -> re.Pattern:
    """Build a case-insensitive boundary regex for a forbidden token."""
    escaped = re.escape(token)
    if token.endswith(("+", "#")):
        # For tokens like C++ or C#, boundary cannot use \b after symbols
        pattern = r"(?<![A-Za-z0-9])" + escaped + r"(?![A-Za-z0-9+#])"
    else:
        pattern = r"(?<![A-Za-z0-9])" + escaped + r"(?![A-Za-z0-9])"
    return re.compile(pattern, re.IGNORECASE)


# Per-token matcher refinements (FCAR round 1). The generic boundary matcher
# misses common spellings and false-fires on one verb; these patterns encode
# the intent of specs.md section 2 for the affected tokens:
# - React: also "ReactJS" / "React.js" (but never "Reactive" / "Preact").
# - C++: also versioned forms "C++17" / "C++20".
# - Hugging Face: also the spaceless "HuggingFace".
# - Excel: the capitalised noun only (a skill claim, e.g. "Microsoft Excel",
#   "proficient in Excel"). The lowercase verb ("I excel at debugging") is
#   honest prose and must pass; skills-section Excel fails via Check 2 anyway.
_SPECIAL_FORBIDDEN_PATTERNS = {
    "React": re.compile(r"(?<![A-Za-z0-9])React(?:\.js|js)?(?![A-Za-z0-9])", re.IGNORECASE),
    "C++": re.compile(r"(?<![A-Za-z0-9])C\+\+(?:\d{2})?(?![A-Za-z0-9+#])"),
    "Hugging Face": re.compile(r"(?<![A-Za-z0-9])Hugging\s?Face(?![A-Za-z0-9])", re.IGNORECASE),
    "Excel": re.compile(r"(?<![A-Za-z0-9])(?i:Microsoft\s+|MS\s+)?Excel(?![A-Za-z0-9])"),
}


def _pattern_for(token: str) -> re.Pattern:
    if token in _SPECIAL_FORBIDDEN_PATTERNS:
        return _SPECIAL_FORBIDDEN_PATTERNS[token]
    return _build_forbidden_pattern(token)


def check_forbidden_tokens(lines: List[str], whitelist: Whitelist) -> List[Finding]:
    """Check 1: Scan for forbidden tokens anywhere in the text.

    Case-insensitive, token-boundary match.
    'Go' is matched as Golang anywhere, or as 'Go' in the skills section (handled in Check 2).
    Plain prose uses of 'go' (e.g. 'go live', 'go-to-market') never fail.
    """
    findings: List[Finding] = []
    compiled_patterns = [
        (tok, _pattern_for(tok)) for tok in whitelist.forbidden_tokens
    ]

    for line_idx, line in enumerate(lines, start=1):
        for token_name, pattern in compiled_patterns:
            for match in pattern.finditer(line):
                findings.append(
                    Finding(
                        check="forbidden_tokens",
                        token=match.group(0),
                        line=line_idx,
                        message=f"Forbidden token '{match.group(0)}' found",
                    )
                )

    return findings


# --- Check 2: Skills Section Verification ---

# Headings matching skills / technical skills / tech stack / technologies / core competencies
_SKILLS_HEADING_RE = re.compile(
    r"^\s*(?:#+\s*)?(?:technical\s+skills|skills(?:\s*&\s*tools)?|tech\s+stack|technologies(?:\s+used)?|core\s+competencies)(?:\s*[:|—–-]\s*(.*))?$",
    re.IGNORECASE,
)

# Major section headings that signal the end of the skills block
_NEXT_SECTION_HEADING_RE = re.compile(
    r"^\s*(?:#+\s*)?(?:experience|work\s+experience|professional\s+experience|"
    r"selected\s+projects|projects|key\s+projects|"
    r"education|education\s+&\s+certifications|certifications|"
    r"professional\s+summary|summary|"
    r"achievements|awards|publications)(?:\s*[:|—–-])?\s*$",
    re.IGNORECASE,
)

# Delimiters for splitting skills: commas, bullets, pipes, slashes, semicolons
_SKILL_DELIMITERS_RE = re.compile(r"[,;|•\u2022\u00b7*\u25cf\u2043\u2219\u25cb\u25aa\u25fe/]+|\s{2,}")


def _extract_skills_block(
    lines: List[str],
) -> Tuple[Optional[List[Tuple[int, str]]], int]:
    """Locate the skills block and return list of (line_num, line_text), plus heading line."""
    skills_lines: List[Tuple[int, str]] = []
    in_skills = False
    heading_line = -1

    for line_idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not in_skills:
            m = _SKILLS_HEADING_RE.match(stripped)
            if m:
                in_skills = True
                heading_line = line_idx
                # Check if there is inline content after heading (e.g. 'Skills: Python, SQL')
                inline_content = (m.group(1) or "").strip()
                if inline_content:
                    skills_lines.append((line_idx, inline_content))
                continue
        else:
            # Inside skills section: check if we reached a new section heading
            if _NEXT_SECTION_HEADING_RE.match(stripped):
                break
            # Also break if line looks like an all-caps section header (>= 3 chars)
            if re.match(r"^[A-Z][A-Z\s&/]{2,}$", stripped) and not any(
                delim in stripped for delim in (",", ";", "•", "|")
            ):
                break
            if stripped:
                skills_lines.append((line_idx, line))

    if not in_skills:
        return None, -1
    return skills_lines, heading_line


def check_skills_section(
    lines: List[str], whitelist: Whitelist, allow_no_skills: bool = False
) -> Tuple[List[Finding], List[str]]:
    """Check 2: Locate and verify skills block against whitelist.

    Missing skills section fails unless allow_no_skills=True.
    Tokens are split on commas, bullets, pipes, slashes, semicolons, newlines.
    Every token must normalize into verified-skills whitelist.
    'Go' in the skills section fails as an unverified language claim.
    """
    findings: List[Finding] = []
    warnings: List[str] = []

    skills_lines, heading_line = _extract_skills_block(lines)
    if skills_lines is None:
        if allow_no_skills:
            warnings.append("Missing skills section (allowed via --allow-no-skills)")
            return findings, warnings
        findings.append(
            Finding(
                check="skills_section",
                token="<missing>",
                line=1,
                message="Missing skills section (tailored resume must have a skills section)",
            )
        )
        return findings, warnings

    for line_num, line_text in skills_lines:
        raw_tokens = _SKILL_DELIMITERS_RE.split(line_text)
        for raw in raw_tokens:
            token = raw.strip(" \t\r\n•·*-:;,()[]{}")
            if not token:
                continue

            # Check for language claim 'Go' in skills
            if token.lower() == "go":
                findings.append(
                    Finding(
                        check="skills_section",
                        token=token,
                        line=line_num,
                        message="Forbidden language claim 'Go' in skills section (must be Golang, which is forbidden)",
                    )
                )
                continue

            # Check if token directly normalizes to a verified skill
            if whitelist.is_verified_skill(token):
                continue

            # Check parenthetical compound e.g. "Express (Node.js)" where both parts may be verified
            paren_match = re.match(r"^([^(]+)\(([^)]+)\)$", token)
            if paren_match:
                p1 = paren_match.group(1).strip()
                p2 = paren_match.group(2).strip()
                if whitelist.is_verified_skill(p1) and whitelist.is_verified_skill(p2):
                    continue

            findings.append(
                Finding(
                    check="skills_section",
                    token=token,
                    line=line_num,
                    message=f"Unknown skill '{token}' not found in verified whitelist",
                )
            )

    return findings, warnings


# --- Check 3: Repo Links & Jarvis Rule ---

_GITHUB_SLUG_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/Shashank-VK/([A-Za-z0-9_.-]+)",
    re.IGNORECASE,
)
_JARVIS_RE = re.compile(r"\bjarvis\b", re.IGNORECASE)
_ANY_GITHUB_RE = re.compile(r"github\.com[/\w.-]*", re.IGNORECASE)


def check_repo_links(lines: List[str], whitelist: Whitelist) -> List[Finding]:
    """Check 3: Verify all github.com/Shashank-VK/<slug> links against known repos.

    Jarvis with a GitHub link fails; Jarvis alone without a link passes.
    """
    findings: List[Finding] = []

    _BARE_LINK_RE = re.compile(r"^\s*(?:https?://)?(?:www\.)?github\.com[/\w.-]*\s*$", re.IGNORECASE)

    for line_idx, line in enumerate(lines, start=1):
        # 1. Check Jarvis with any GitHub link (same line, or a bare link on the next line)
        if _JARVIS_RE.search(line):
            next_is_bare_link = (
                line_idx < len(lines) and _BARE_LINK_RE.match(lines[line_idx]) is not None
            )
            if _ANY_GITHUB_RE.search(line) or next_is_bare_link:
                findings.append(
                    Finding(
                        check="repo_links",
                        token="Jarvis with GitHub link",
                        line=line_idx,
                        message="Jarvis is a local-only project; linking a GitHub repository is forbidden",
                    )
                )

        # 2. Check each github.com/Shashank-VK/<slug> link
        for m in _GITHUB_SLUG_RE.finditer(line):
            full_match = m.group(0)
            slug = m.group(1).rstrip(".,/):;?\"'")
            if not slug:
                continue

            if not whitelist.is_known_repo(slug):
                # If the slug is 'jarvis', avoid duplicate finding if already reported above
                if slug.lower() == "jarvis" and any(
                    f.check == "repo_links" and f.line == line_idx for f in findings
                ):
                    continue
                findings.append(
                    Finding(
                        check="repo_links",
                        token=full_match,
                        line=line_idx,
                        message=f"Unverified repo link: {full_match} (repo '{slug}' is unknown)",
                    )
                )

    return findings


# --- Check 4: Test-Count Phrasing Rule ---

# Banned test phrasing: 'N/N passing' / 'N/N passed' / 'N/N tests' ONLY.
# A bare ratio is not a test claim ("Available 24/7", "improved from 3/5 to
# 4/5", CGPA "8.9/10", dates) and must pass — specs.md section 4.
_TEST_COUNT_RATIO_RE = re.compile(
    r"(?<![\d./])\b(\d{1,3}\s*/\s*\d{1,3})\b(?!\s*/\s*\d)\s+(?:passing|tests|passed)\b",
    re.IGNORECASE,
)


def check_test_count_phrasing(lines: List[str]) -> List[Finding]:
    """Check 4: Verify test count phrasing.

    'N/N passing' and 'N/N tests' style claims fail.
    The only honest phrasing is 'N tests in the suite' or 'N tests'.
    """
    findings: List[Finding] = []

    for line_idx, line in enumerate(lines, start=1):
        for m in _TEST_COUNT_RATIO_RE.finditer(line):
            match_str = m.group(0)
            findings.append(
                Finding(
                    check="test_count_phrasing",
                    token=match_str,
                    line=line_idx,
                    message=f"Banned test-count phrasing '{match_str}' (only honest form is 'N tests in the suite')",
                )
            )

    return findings


# --- Orchestrator ---

def run_all_checks(
    text: str, whitelist: Whitelist, allow_no_skills: bool = False
) -> CheckResult:
    """Run all four checks on the resume text."""
    lines = text.splitlines()

    findings: List[Finding] = []
    warnings: List[str] = []

    # Check 1: Forbidden tokens anywhere
    findings.extend(check_forbidden_tokens(lines, whitelist))

    # Check 2: Skills section verification
    skills_findings, skills_warnings = check_skills_section(
        lines, whitelist, allow_no_skills=allow_no_skills
    )
    findings.extend(skills_findings)
    warnings.extend(skills_warnings)

    # Check 3: Repo links & Jarvis rule
    findings.extend(check_repo_links(lines, whitelist))

    # Check 4: Test-count phrasing
    findings.extend(check_test_count_phrasing(lines))

    # Sort findings by line number then check name for deterministic output
    findings.sort(key=lambda f: (f.line, f.check, f.token))

    return CheckResult(findings=findings, warnings=warnings)
