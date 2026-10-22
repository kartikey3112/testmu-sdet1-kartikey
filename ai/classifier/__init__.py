"""Task 3: Flaky Test Classifier (Option B).

Why Option B (Flaky Test Classifier) and not Option A (Failure Explainer):

- The ticket's pain is "fixing regression tests". Most of that time goes on triaging a red
  run: deciding which failures need a human at all. A classifier answers that question for
  the whole run; an explainer only describes failures someone has already decided to look at.
- B looks across the whole run and uses cross-attempt evidence: whether a test passed on
  rerun, whether the error repeated or varied, and whether the app was healthy at the time.
  A per-failure explainer only ever sees one failure.
- B's output is a discrete label (real_bug / environment_issue / flaky), so it can be
  measured against injected ground truth (app/faults.py). A's free-text explanations are hard
  to score objectively.
- Part of A's value is kept: every classification carries evidence and a suggested next
  action. A full Failure Explainer reusing this collector is listed as "next" in the README.

Drafted with Claude Code; reviewed and approved by Kartikey without changes (2026-10-23).

Modules:
  collector.py  pytest plugin: one JSON line per test attempt -> execution-log.jsonl
  signals.py    deterministic pre-signals (hints for the LLM, not verdicts)
  payload.py    compact, redacted, chunked payload of failing tests
  classify.py   real LLM call, validation, one retry, outputs; CLI
  report.py     classification.md and the section injected into the pytest-html report
"""
