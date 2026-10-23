# Failure classification: run eval-20261022T200611Z-mixed

- Model: `openai/gpt-oss-120b` (groq), temperature 0.0, prompt `classifier.v1` (SHA-256 `2406cab727e3…`)
- Generated: 2026-10-23T07:16:23Z
- Tests: 37; with a failed attempt: 9; real_bug: 3, flaky: 6
- LLM calls: 3 (3 requests including retries)

## Real bugs (3)

| Test | Case | Confidence | Final outcome | Reasoning | Next action |
|---|---|---|---|---|---|
| `tests/ui/login/test_login.py::test_fifth_consecutive_failure_locks_the_account[chromium]` | LOGIN-012 | 0.78 | failed (3/3 attempts failed) | Rule 4 matched (same assertion error across attempts, category assertion, no 5xx). | File a bug: lockout endpoint returns 401 instead of expected 423 after consecutive failures. |
| `tests/ui/login/test_login.py::test_correct_password_is_refused_while_locked[chromium]` | LOGIN-013 | 0.78 | failed (3/3 attempts failed) | Rule 4 matched (consistent assertion error, category assertion, no 5xx). | File a bug: locked account returns 303 instead of expected 423 for incorrect password. |
| `tests/api/test_api.py::test_admin_deletes_a_test_case` | API-009 | 0.94 | failed (3/3 attempts failed) | Rule 4 matched: all attempts had the same assertion error, category is assertion, and no 5xx seen, leading to a real bug classification. | File a bug: the API returns 200 instead of the expected 404 for a deleted test case, causing the assertion to fail. |

Evidence:

- `tests/ui/login/test_login.py::test_fifth_consecutive_failure_locks_the_account[chromium]`
  - `signals.same_error_all_attempts:true`
  - `signals.error_category_heuristic:assertion`
  - `attempts[0].error.message:"assert 401 == 423"`
- `tests/ui/login/test_login.py::test_correct_password_is_refused_while_locked[chromium]`
  - `signals.same_error_all_attempts:true`
  - `signals.error_category_heuristic:assertion`
  - `attempts[0].error.message:"assert 303 == 423"`
- `tests/api/test_api.py::test_admin_deletes_a_test_case`
  - `signals.same_error_all_attempts: true`
  - `signals.error_category_heuristic: assertion`
  - `attempts[0].error.message: Expected 404, got 200: {"id":25,..."`
  - `attempts[0].api_last_exchange.status: 200`

## Flaky tests (6)

| Test | Case | Confidence | Final outcome | Reasoning | Next action |
|---|---|---|---|---|---|
| `tests/ui/dashboard/test_dashboard.py::test_total_test_cases_widget_loads[chromium]` | DASH-001 | 0.92 | passed (1/2 attempts failed) | Rule 1 applied: passed_on_rerun is true and no 5xx seen, so the failure is flaky. | Add a retry or explicit wait to stabilize the widget loading and re‑run the test. |
| `tests/ui/dashboard/test_dashboard.py::test_date_from_after_date_to_puts_recent_runs_in_error[chromium]` | DASH-002 | 0.92 | passed (1/2 attempts failed) | Rule 1 applied: passed_on_rerun is true and no 5xx seen, indicating flakiness. | Introduce a wait for the date filter to settle or retry the step to reduce nondeterminism. |
| `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]` | DASH-005 | 0.78 | failed (3/3 attempts failed) | Rule 5 applied: attempts failed with different messages and no 5xx, pointing to a flaky test. | Investigate timing/race conditions on the pass‑rate widget and add appropriate waits or retries. |
| `tests/ui/dashboard/test_dashboard.py::test_recent_runs_default_is_latest_ten_newest_first[chromium]` | DASH-007 | 0.78 | failed (3/3 attempts failed) | Rule 5 applied: multiple distinct assertion failures without 5xx indicate flakiness. | Add stabilization (e.g., wait for recent‑runs list to load) and consider retry logic for this UI test. |
| `tests/ui/dashboard/test_dashboard.py::test_same_day_date_range_returns_that_run[chromium]` | DASH-009 | 0.92 | passed (1/2 attempts failed) | Rule 1 matched (passed_on_rerun true and no 5xx seen). | Add a more robust wait or retry for the widget to reach the loaded state. |
| `tests/ui/login/test_login.py::test_session_is_expired_at_exactly_1800_seconds[chromium]` | LOGIN-010 | 0.92 | passed (1/2 attempts failed) | Rule 1 matched (passed_on_rerun true and no 5xx seen). | Introduce explicit wait for session expiration indicator before asserting. |

Evidence:

- `tests/ui/dashboard/test_dashboard.py::test_total_test_cases_widget_loads[chromium]`
  - `signals.passed_on_rerun:true`
  - `signals.http_5xx_seen:false`
- `tests/ui/dashboard/test_dashboard.py::test_date_from_after_date_to_puts_recent_runs_in_error[chromium]`
  - `signals.passed_on_rerun:true`
  - `signals.http_5xx_seen:false`
- `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]`
  - `attempts[0].error.message:"Locator expected to have attribute 'loaded'..."`
  - `attempts[2].error.message:"assert '100.0%' == '87.5%'"`
  - `signals.same_error_all_attempts:false`
- `tests/ui/dashboard/test_dashboard.py::test_recent_runs_default_is_latest_ten_newest_first[chromium]`
  - `attempts[0].error.message:"Locator expected to have attribute 'loaded'..."`
  - `attempts[1].error.message:"Locator expected to have have text '2026-09-21 nightly'"`
  - `attempts[2].error.message:"Locator expected to have attribute 'loaded'..."`
- `tests/ui/dashboard/test_dashboard.py::test_same_day_date_range_returns_that_run[chromium]`
  - `signals.passed_on_rerun:true`
  - `signals.http_5xx_seen:false`
  - `attempts[0].error.message:"Locator expected to have attribute 'loaded'"`
- `tests/ui/login/test_login.py::test_session_is_expired_at_exactly_1800_seconds[chromium]`
  - `signals.passed_on_rerun:true`
  - `signals.http_5xx_seen:false`
  - `attempts[0].error.message:"Locator expected to have attribute 'loaded'"`
