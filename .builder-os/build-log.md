# Build log — fcar-local (Build 2, 2026-10-23)

Engine: agy headless (OmniRush benched). Method: BUILDER-OS — specs-first,
.gates before code, TDD per feature, verify exit 0 before "done".

## Build (agy)
- Scaffold implemented to specs.md: whitelist loader/validator, four checks,
  human + JSON report, CLI (exit 0/1/2, stdin, --json, --allow-no-skills).
- agy run: 56 tests passed; CLI on the clean fixture PASS in 0.170s.

## FCAR round 1 — FAIL (fresh-context reviewer, adversarial)
- DATA: whitelist.json carried entries tracing to none of the declared sources
  (NumPy, Linux, OOP/SOLID, Dashboards, Data quality/validation, Containerized
  deployment, AI coding agents, CD, Git, Express, Supertest, Vitest) plus
  misattributed stack items (ProjectFlow->JWT, wildlife->Pandas/Streamlit,
  aiprise->Pydantic, invented stacks for ts-express-api and
  stripe-webhook-idempotency). One shipped test even blessed the inventions
  via a self-written "general canon".
- CODE: check 4 banned ALL N/N ratios (spec bans only N/N passing|tests|passed);
  ReactJS / C++20 / HuggingFace evaded the forbidden scan; the verb "excel"
  false-fired; headings with suffix words ("Skills & Tools:") misparsed;
  multi-space-separated skills glued into one token; Jarvis rule was
  same-line only; one dead import.
- CLEARED by FCAR: known_repos exact (31), forbidden list complete, canonical
  AGENTS.md stacks fully present, CLI contract and exit codes exact.

## Fixes (all pinned by tests/test_fcar_round1_regressions.py + updated suites)
- Data: 17 entries pruned; JWT re-attributed to flask-ledger-api (its README
  names JWT), Model serving to flask-ml-serving, API/E2E testing to
  qa-e2e-lab; two unsourced stack entries dropped. Global-only skills now
  exactly six, each traced to a named source in the traceability test.
- Code: per-token special matchers; check 4 requires the test suffix; heading
  regex anchored with suffix words; multi-space delimiter + token whitespace
  normalization; Jarvis window extended to a bare-link next line; dead import
  removed; whitelist.py documents the union contract.
- Fixtures/tests that pinned the old data were corrected (skills lines without
  Git/Linux, prose Java removed, canon test rewritten with named sources).

## Gate (final, fresh)
- .venv/bin/python -m pytest: 75 passed. .builder-os/init.sh exit 0.
- BUILDER-OS secret-scan on project source: PASSED.
- Independent probes: bad resume fails all four checks with exact tokens and
  line numbers (exit 1); clean resume PASS (exit 0); CLI ~0.1s per run.
- No FCAR round 2 was run; the fixes are verified by the regression suite and
  probes. Stated plainly in the completion report to main.
