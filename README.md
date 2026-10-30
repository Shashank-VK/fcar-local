# FCAR Local Checker (`fcar-local`)

A deterministic, offline Python command-line checker that C2 runs on tailored resumes **before** LLM (Gemini Flash) review. It executes in milliseconds, uses Python 3 standard library only, makes zero network calls, and performs zero LLM inferences.

Its single purpose is catching mechanical honesty violations: forbidden skill claims, unverified skills, repo links to non-existent GitHub repositories, and banned test-count phrasing.

---

## How C2 Runs It Before LLM Review

In the C2 resume generation and certification pipeline, `fcar-local` serves as an instantaneous deterministic gate immediately after text extraction from the generated PDF:

```
[Tailored Resume Text]
         │
         ▼
 ┌───────────────┐
 │  fcar-local   │  ── Exit 1 (FAIL) ──> Reject immediately (0 LLM cost)
 └───────┬───────┘
         │ Exit 0 (PASS)
         ▼
 ┌───────────────┐
 │ LLM Review    │  ── (Gemini Flash qualitative fit evaluation)
 └───────────────┘
```

If `fcar-local` detects any violation (exit code 1), the candidate resume is rejected immediately without burning LLM tokens or time. Only resumes passing this mechanical honesty gate proceed to the LLM review.

### Usage

```bash
# Basic run on a resume text file
python3 fcar_check.py resume.txt

# Read from stdin
cat resume.txt | python3 fcar_check.py -

# Output structured JSON
python3 fcar_check.py resume.txt --json

# Downgrade missing skills section check to a warning
python3 fcar_check.py resume.txt --allow-no-skills

# Specify a custom whitelist file
python3 fcar_check.py resume.txt --whitelist /path/to/custom_whitelist.json
```

---

## The Four Checks

Every check failure reports the exact offending token, line number, and check name:

1. **Check 1: Forbidden Tokens Scan**
   - Scans for banned tokens anywhere in the text using case-insensitive token-boundary matching (`React`, `Golang`, `C++`, `C#`, `Power BI`, `PyTorch`, `TensorFlow`, `Hugging Face`, `Excel`, `Infyntrek`).
   - Plain prose uses of the English word "go" (e.g. "go-to-market", "go live") always pass.
   - "Golang" fails anywhere in the text; "Go" claimed as a programming language in the skills section fails under Check 2.

2. **Check 2: Skills Section Verification**
   - Automatically detects the skills section under common headings (`Technical Skills`, `Skills`, `Tech Stack`, `Technologies`, `Core Competencies`).
   - Tokenizes entries on commas, semicolons, bullets, slashes, pipes, and newlines.
   - Every token must normalize to an entry in `verified_skills`. Any unverified token (e.g., `Kubernetes`) fails by name and line number.
   - Missing skills section fails by default; `--allow-no-skills` downgrades this failure to a printed warning.

3. **Check 3: Repo Links & Jarvis Rule**
   - Every `github.com/Shashank-VK/<slug>` URL must match a slug in `known_repos`. Unverified repository links fail.
   - `Jarvis` is a local-only desktop project per `PROJECT_LIST.md`. A mention of `Jarvis` without a GitHub link passes cleanly; any `Jarvis` mention carrying a GitHub URL fails.

4. **Check 4: Test-Count Phrasing Rule**
   - Disallows test-count ratio claims: "23/23 passing", "23/23 tests", "43/43 passing at push". A bare ratio with no test suffix ("Available 24/7", "improved from 3/5 to 4/5", a CGPA) is not a test claim and passes.
   - The only accepted honest phrasing is `"N tests in the suite"` (or `"N tests"`).
   - Numerical metrics like `"CGPA 8.9/10"` and date ranges like `"09/2024 to 12/2025"` pass without false alarms.

---

## Exit Codes

- **`0` (PASS)**: All checks passed with zero findings.
- **`1` (FAIL)**: One or more rule violations detected. Findings are printed to stdout with check name, line number, and token.
- **`2` (Usage / Input Error)**: Invalid command-line arguments, missing resume file, unreadable stdin, or corrupted/invalid `whitelist.json`.

---

## Output Formats

### Human-Readable (Default)

**Pass:**
```
FCAR LOCAL: PASS
```

**Fail:**
```
FCAR LOCAL: FAIL
- [forbidden_tokens] line 10: 'React' (Forbidden token 'React' found)
- [skills_section] line 5: 'Kubernetes' (Unknown skill 'Kubernetes' not found in verified whitelist)
- [repo_links] line 14: 'github.com/Shashank-VK/fake-repo' (Unverified repo link: github.com/Shashank-VK/fake-repo (repo 'fake-repo' is unknown))
- [test_count_phrasing] line 18: '23/23 passing' (Banned test-count phrasing '23/23 passing' (only honest form is 'N tests in the suite'))
```

### JSON Mode (`--json`)

```json
{
  "status": "FAIL",
  "findings": [
    {
      "check": "forbidden_tokens",
      "token": "React",
      "line": 10,
      "message": "Forbidden token 'React' found"
    }
  ],
  "warnings": []
}
```

---

## How to Update the Whitelist

Never modify python code to add skills, projects, or repos. All verification rules are grounded in `whitelist.json`:

1. Open `whitelist.json`.
2. To add newly verified skills: add to `verified_skills` and document which project stack proves it in `project_stacks`.
3. To add newly published repositories: add the repo slug to `known_repos`.
4. Update `_meta.sources` to document the canonical source of truth for the added claims.
5. Run the test suite: `.venv/bin/python -m pytest` to ensure schema integrity and consistency.

---

## Honest Limits

- **Mechanical Honesty Only**: `fcar-local` only verifies factual mechanical claims: presence of forbidden keywords, whitelist skill verification, repository existence, and test-phrasing discipline.
- **No Fit Judgement**: It does not evaluate job-description match, keyword density, role relevance, or career suitability.
- **No Content Rewriting**: It does not modify resumes or generate replacement text.
- **LLM Review Follows**: The qualitative evaluation and fit scoring remain the responsibility of the upstream Gemini Flash LLM review pass.

## Matcher notes (FCAR round 1, 2026-10-23)

- Forbidden-token spelling variants are covered: ReactJS / React.js count as
  React; C++17 / C++20 count as C++; the spaceless HuggingFace counts as
  Hugging Face. Innocent lookalikes pass: "Reactive", "Preact".
- Excel fails as a capitalised noun (a skill claim: "Microsoft Excel",
  "proficient in Excel"); the lowercase verb ("I excel at debugging") passes.
  Excel in the skills section fails via Check 2 regardless of case.
- whitelist.json is source-exact: every skill and every per-project stack entry
  must be stated by a declared source. Stack entries union into the global
  verified set, so an inference in one stack would legitimise a skill globally.
