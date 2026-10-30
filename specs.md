# specs.md — FCAR Local Script (BUILDER-OS locked specification)

## Overview
A deterministic, offline Python checker that C2 runs on a tailored resume BEFORE the
LLM (Gemini Flash) review. Seconds, no network, no LLM. It catches the mechanical
honesty failures: forbidden skill claims (React/Golang/C++ and friends), skills that
trace to no verified project, repo links to repos that don't exist, and banned
test-count phrasing. It does NOT judge fit or quality — the LLM FCAR still runs after it.

## Inputs
- A resume text file (plain text extracted from the PDF), or "-" for stdin.
- whitelist.json (shipped in this project, versioned): the canonical verified data —
  * global verified skills (each traceable to PROJECT_LIST.md, the AGENTS.md FCAR
    stacks, or a shipped repo),
  * per-project tech stacks (VoicePilot, GroundedQA, EvalForge, Green Grid AI,
    SQL Analytics Lab, ProjectFlow, mcp-agent-demo, the 5 PoW artifacts, the Flask
    trio, qa-e2e-lab, wildlife-detection, apertureID),
  * known repo slugs under github.com/Shashank-VK,
  * the Flask rule: Flask is verified (his attestation 2026-10-22 + 3 shipped repos),
  * forbidden tokens: React, Golang, C++, C#, Power BI, PyTorch, TensorFlow,
    Hugging Face (as a skill claim), Excel (as a personal skill), Infyntrek, Jarvis.

## Checks (each failure reports the exact token + line number)
1. FORBIDDEN TOKENS anywhere in the text (case-insensitive, token-boundary match).
   "Go" is matched as a language claim only in the skills section or as "Golang"
   anywhere — plain prose uses of the word "go" never fail.
2. SKILLS SECTION: locate the skills block (headings matching skills / technical
   skills / tech stack / technologies / core competencies, case-insensitive), split
   into tokens on commas, bullets, pipes, slashes and newlines; every token must
   normalize into the verified-skills whitelist, else FAIL naming it. Missing skills
   section = FAIL (a tailored resume always has one); --allow-no-skills downgrades
   that single check to a printed warning.
3. REPO LINKS: every github.com/Shashank-VK/<slug> URL must be in the known-repo set,
   else FAIL ("unverified repo link"). A Jarvis mention carrying a GitHub link fails;
   Jarvis without a link is allowed (local-only project, listed in PROJECT_LIST.md).
4. TEST-COUNT PHRASING: "N/N passing" or "N/N tests" style claims fail — the only
   honest form is "N tests in the suite".

## Output
- Human mode: "FCAR LOCAL: PASS" or "FCAR LOCAL: FAIL" + one line per finding
  (check, token, line). --json emits the same as JSON.
- Exit code 0 = PASS, 1 = FAIL, 2 = usage/input error.

## Tech
Python 3.12, standard library only. Runtime is milliseconds on a resume-sized input.

## Non-goals
- No fit scoring, no JD matching, no rewriting suggestions, no LLM calls, no network.
- Whitelist updates are data edits to whitelist.json (with the source of truth noted
  in its _meta), never code changes.

## Verification
.builder-os/init.sh exit 0: pytest suite green — fixture resumes pin every check:
a clean resume passes; React/Golang/C++/PyTorch each fail by name; Flask passes;
an unknown repo slug fails; "23/23 passing" fails; skills-section variants parse.

## Amendment 2026-10-23 (FCAR round 1, matcher notes)
- Check 4 bans ONLY "N/N passing|passed|tests"; bare ratios pass (the shipped
  code briefly banned all ratios; reconciled to this section's text).
- Forbidden-token matchers cover spelling variants (ReactJS, React.js, C++17,
  C++20, HuggingFace); "Excel" fails as a capitalised skill noun, the lowercase
  verb passes. Skills headings may carry suffix words ("Skills & Tools:",
  "Technologies Used:"); multi-space runs are skill delimiters.
- whitelist.json entries must be stated verbatim by a declared source; the
  FCAR data audit owns that standard (17 invented entries pruned in round 1).
