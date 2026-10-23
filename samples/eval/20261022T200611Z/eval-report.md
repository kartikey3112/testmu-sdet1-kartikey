# Flaky Test Classifier: evaluation

- Generated: 20261022T200611Z
- Model: `openai/gpt-oss-120b`, prompt `classifier.v1`, temperature 0
- Each scenario: UI + API suites with `--reruns 2` and the faults listed; ground truth from `app/faults.py` as described in `scripts/eval_classifier.py`.

**Overall accuracy: 53/55 = 0.964**

## Confusion matrix (rows: ground truth, columns: prediction)

| | real_bug | environment_issue | flaky | unclassified |
|---|---|---|---|---|
| **real_bug** | 7 | 0 | 1 | 0 |
| **environment_issue** | 0 | 37 | 0 | 0 |
| **flaky** | 1 | 0 | 9 | 0 |

## Per scenario

| Scenario | Faults | Failing tests | Scored | Correct | Accuracy | LLM requests |
|---|---|---|---|---|---|---|
| clean | none | 0 | — | — | — | 0 |
| real_bug | BUG_PASS_RATE_OFF_BY_ONE, BUG_DELETE_NOT_PERSISTED, BUG_LOCKOUT_THRESHOLD_WRONG | 4 | 4 | 4 | 1.0 | 2 |
| environment_issue | ENV_WIDGET_API_503, ENV_DB_UNAVAILABLE, ENV_HEALTH_FAILING | 37 | 37 | 37 | 1.0 | 16 |
| flaky | FLAKY_WIDGET_LATENCY, FLAKY_UNSORTED_ORDER | 5 | 5 | 4 | 0.8 | 2 |
| health_only | ENV_HEALTH_FAILING | 0 | — | — | — | 0 |
| mixed | BUG_PASS_RATE_OFF_BY_ONE, BUG_DELETE_NOT_PERSISTED, BUG_LOCKOUT_THRESHOLD_WRONG, FLAKY_WIDGET_LATENCY, FLAKY_UNSORTED_ORDER, ENV_HEALTH_FAILING | 9 | 9 | 8 | 0.889 | 3 |

## Misclassifications (2)

| Scenario | Test | Truth | Predicted | Confidence | Model's reasoning |
|---|---|---|---|---|---|
| flaky | `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]` | flaky | real_bug | 0.94 | Rule 4 applied: same error on all attempts, category assertion, no 5xx, indicating a real bug. |
| mixed | `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]` | real_bug | flaky | 0.78 | Rule 5 applied: attempts failed with different messages and no 5xx, pointing to a flaky test. |
