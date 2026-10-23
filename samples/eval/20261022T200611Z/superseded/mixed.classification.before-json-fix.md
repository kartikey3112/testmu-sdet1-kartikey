# Failure classification: run eval-20261022T200611Z-mixed

- Model: `openai/gpt-oss-120b` (groq), temperature 0.0, prompt `classifier.v1` (SHA-256 `2406cab727e3…`)
- Generated: 2026-10-23T07:13:26Z
- Tests: 37; with a failed attempt: 10; real_bug: 3, environment_issue: 1, flaky: 2, unclassified: 4
- LLM calls: 3 (2 requests including retries)

## Real bugs (3)

| Test | Case | Confidence | Final outcome | Reasoning | Next action |
|---|---|---|---|---|---|
| `tests/ui/login/test_login.py::test_fifth_consecutive_failure_locks_the_account[chromium]` | LOGIN-012 | 0.94 | failed (3/3 attempts failed) | Rule 4 applied: all attempts failed with the same assertion error, no 5xx seen, indicating a real bug in the lock‑out logic. | File a bug (LOGIN-012) to fix the lock‑out response code mismatch (expected 423, got 401). |
| `tests/ui/login/test_login.py::test_correct_password_is_refused_while_locked[chromium]` | LOGIN-013 | 0.92 | failed (3/3 attempts failed) | Rule 4 matched: same error on all attempts, category assertion, no 5xx seen, so this is a real bug. | File a bug: login lockout returns status 303 instead of expected 423, causing incorrect password handling while account is locked. |
| `tests/api/test_api.py::test_admin_deletes_a_test_case` | API-009 | 0.91 | failed (3/3 attempts failed) | Rule 4 matched: same error on all attempts, category assertion, no 5xx seen, indicating a real bug in the API behavior. | File a bug: admin delete test case endpoint returns 200 instead of 404 after deletion, breaking expected contract. |

Evidence:

- `tests/ui/login/test_login.py::test_fifth_consecutive_failure_locks_the_account[chromium]`
  - `signals.same_error_all_attempts: true`
  - `signals.error_category_heuristic: assertion`
  - `signals.http_5xx_seen: false`
  - `attempts[0].error.message: "assert 401 == 423"`
- `tests/ui/login/test_login.py::test_correct_password_is_refused_while_locked[chromium]`
  - `signals.same_error_all_attempts: true`
  - `signals.error_category_heuristic: assertion`
  - `attempts[0].error.message: assert 303 == 423`
- `tests/api/test_api.py::test_admin_deletes_a_test_case`
  - `signals.same_error_all_attempts: true`
  - `signals.error_category_heuristic: assertion`
  - `attempts[0].error.message: Expected 404, got 200`

## Environment issues (1)

| Test | Case | Confidence | Final outcome | Reasoning | Next action |
|---|---|---|---|---|---|
| `tests/ui/login/test_login.py::test_session_is_expired_at_exactly_1800_seconds[chromium]` | LOGIN-010 | 0.73 | failed (3/3 attempts failed) | No rule matched directly; the health endpoint returned 503 on every attempt, indicating the application was unhealthy, so rule 2 is inferred as an environment issue. | Investigate the health service/database that returned 503 and ensure the app is healthy before re‑running the test. |

Evidence:

- `tests/ui/login/test_login.py::test_session_is_expired_at_exactly_1800_seconds[chromium]`
  - `attempts[0].health_at_failure.status: 503`
  - `signals.health_ok_at_failure: false`
  - `attempts[0].error.message: "Locator expected to have attribute 'loaded'\nActual value: loading "`

## Flaky tests (2)

| Test | Case | Confidence | Final outcome | Reasoning | Next action |
|---|---|---|---|---|---|
| `tests/ui/dashboard/test_dashboard.py::test_wide_viewport_shows_sidebar_and_two_columns[chromium]` | DASH-011 | 0.92 | passed (1/2 attempts failed) | Rule 1 applied: the test passed on a rerun and no 5xx was seen, indicating a flaky failure. | Add an explicit wait for the widget to reach the 'loaded' state before asserting. |
| `tests/ui/dashboard/test_smoke_dashboard.py::test_total_test_cases_widget_matches_api_and_seed[chromium]` | — | 0.91 | passed (1/2 attempts failed) | Rule 1 applied: the test passed on a rerun with no 5xx observed, marking it as flaky. | Introduce a retry or wait for the total‑test‑cases widget to finish loading before checking its value. |

Evidence:

- `tests/ui/dashboard/test_dashboard.py::test_wide_viewport_shows_sidebar_and_two_columns[chromium]`
  - `signals.passed_on_rerun: true`
  - `signals.http_5xx_seen: false`
  - `attempts[0].error.message: "Locator expected to have attribute 'loaded'\nActual value: loading "`
  - `attempts[0].duration_s: 5.137`
- `tests/ui/dashboard/test_smoke_dashboard.py::test_total_test_cases_widget_matches_api_and_seed[chromium]`
  - `signals.passed_on_rerun: true`
  - `signals.http_5xx_seen: false`
  - `attempts[0].error.message: "Locator expected to have attribute 'loaded'\nActual value: loading "`
  - `attempts[0].duration_s: 5.07`

## Unclassified (no valid LLM answer) (4)

| Test | Case | Confidence | Final outcome | Reasoning | Next action |
|---|---|---|---|---|---|
| `tests/ui/dashboard/test_dashboard.py::test_date_from_after_date_to_puts_recent_runs_in_error[chromium]` | DASH-002 | — | failed (3/3 attempts failed) | No valid classification after one retry. | Triage manually. |
| `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]` | DASH-005 | — | failed (3/3 attempts failed) | No valid classification after one retry. | Triage manually. |
| `tests/ui/dashboard/test_dashboard.py::test_recent_runs_default_is_latest_ten_newest_first[chromium]` | DASH-007 | — | failed (3/3 attempts failed) | No valid classification after one retry. | Triage manually. |
| `tests/ui/dashboard/test_dashboard.py::test_same_day_date_range_returns_that_run[chromium]` | DASH-009 | — | passed (1/2 attempts failed) | No valid classification after one retry. | Triage manually. |

Evidence:

- `tests/ui/dashboard/test_dashboard.py::test_date_from_after_date_to_puts_recent_runs_in_error[chromium]`
- `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]`
- `tests/ui/dashboard/test_dashboard.py::test_recent_runs_default_is_latest_ten_newest_first[chromium]`
- `tests/ui/dashboard/test_dashboard.py::test_same_day_date_range_returns_that_run[chromium]`

## LLM call problems

- chunk 1: LLM request failed: HTTP 400: {"error":{"message":"Failed to generate JSON. Please adjust your prompt. See 'failed_generation' for more details.","type":"invalid_request_error","code":"json_validate_failed","failed_generation":"{\"classifications\":[{\"test_id\":\"tests/ui/dashboard/test_dashboard.p
