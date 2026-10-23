# Sample: classified run `eval-20261022T200611Z-mixed`

Real output, copied unchanged from `reports/` by `scripts/export_samples.py`.

- Model: `openai/gpt-oss-120b` (groq), temperature 0.0, prompt `classifier.v1`
- Classified at: 2026-10-23T07:16:23Z
- Tests: 37; with a failed attempt: 9; by bucket: {'flaky': 6, 'real_bug': 3}
- Faults injected (ground truth, never sent to the LLM): BUG_DELETE_NOT_PERSISTED, BUG_LOCKOUT_THRESHOLD_WRONG, BUG_PASS_RATE_OFF_BY_ONE, ENV_HEALTH_FAILING, FLAKY_UNSORTED_ORDER, FLAKY_WIDGET_LATENCY
- Reruns: 2; git SHA: `dc500a2b76c794b037189ae21bfdf90b5f983c1a`

Files:
- `report.html`: the pytest-html report with the LLM classification inside it (summary above the results, an "LLM bucket" column, and a block per failing test)
- `classification.json` / `classification.md`: the classifier's output
- `report-llm-summary.png`: screenshot of the report
- `report-test-classification.png`: screenshot of the report
