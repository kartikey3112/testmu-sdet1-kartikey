# Failure classification: run eval-20261022T200611Z-flaky

- Model: `openai/gpt-oss-120b` (groq), temperature 0.0, prompt `classifier.v1` (SHA-256 `2406cab727e3…`)
- Generated: 2026-10-23T07:17:20Z
- Tests: 37; with a failed attempt: 5; real_bug: 1, flaky: 4
- LLM calls: 2 (2 requests including retries)

## Real bugs (1)

| Test | Case | Confidence | Final outcome | Reasoning | Next action |
|---|---|---|---|---|---|
| `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]` | DASH-005 | 0.94 | failed (3/3 attempts failed) | Rule 4 applied: same error on all attempts, category assertion, no 5xx, indicating a real bug. | File a bug: pass‑rate widget remains in loading state; investigate widget rendering logic. |

Evidence:

- `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]`
  - `signals.same_error_all_attempts:true`
  - `signals.error_category_heuristic:"assertion"`
  - `attempts[0].error.message:"Locator expected to have attribute 'loaded'"`

## Flaky tests (4)

| Test | Case | Confidence | Final outcome | Reasoning | Next action |
|---|---|---|---|---|---|
| `tests/ui/dashboard/test_dashboard.py::test_total_test_cases_widget_loads[chromium]` | DASH-001 | 0.92 | passed (1/2 attempts failed) | Rule 1 applied: passed_on_rerun is true and no 5xx seen, so flaky. | Add explicit wait or retry logic for the widget load and re‑run the test. |
| `tests/ui/dashboard/test_dashboard.py::test_date_from_after_date_to_puts_recent_runs_in_error[chromium]` | DASH-002 | 0.92 | passed (1/2 attempts failed) | Rule 1 applied: passed_on_rerun is true and no 5xx seen, so flaky. | Stabilize the date filter UI (e.g., wait for options to load) and re‑run. |
| `tests/ui/dashboard/test_dashboard.py::test_recent_runs_default_is_latest_ten_newest_first[chromium]` | DASH-007 | 0.91 | passed (2/3 attempts failed) | Rule 1 applied: passed_on_rerun is true and no 5xx seen, so flaky. | Add a retry or explicit wait for recent‑runs list to settle before asserting its content. |
| `tests/ui/login/test_login.py::test_session_is_expired_at_exactly_1800_seconds[chromium]` | LOGIN-010 | 0.90 | failed (3/3 attempts failed) | Rule 5 matched: attempts failed with differing error details and no 5xx, leading to a flaky classification. | Add an explicit wait or retry for the widget to reach the 'loaded' state before asserting, then re‑run the test. |

Evidence:

- `tests/ui/dashboard/test_dashboard.py::test_total_test_cases_widget_loads[chromium]`
  - `signals.passed_on_rerun:true`
  - `signals.http_5xx_seen:false`
  - `attempts[0].error.message:"Locator expected to have attribute 'loaded'"`
- `tests/ui/dashboard/test_dashboard.py::test_date_from_after_date_to_puts_recent_runs_in_error[chromium]`
  - `signals.passed_on_rerun:true`
  - `signals.http_5xx_seen:false`
  - `attempts[0].error.message:"Locator expected to have attribute 'error'"`
- `tests/ui/dashboard/test_dashboard.py::test_recent_runs_default_is_latest_ten_newest_first[chromium]`
  - `signals.passed_on_rerun:true`
  - `signals.http_5xx_seen:false`
  - `attempts[0].error.message:"Locator expected to have text '2026-09-21 nightly'"`
- `tests/ui/login/test_login.py::test_session_is_expired_at_exactly_1800_seconds[chromium]`
  - `signals.passed_on_rerun: false`
  - `signals.same_error_all_attempts: false`
  - `signals.error_category_heuristic: assertion`
  - `attempts[0].error.message: Locator expected to have attribute 'loaded'\nActual value: loading `
