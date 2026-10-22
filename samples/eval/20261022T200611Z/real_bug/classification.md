# Failure classification: run eval-20261022T200611Z-real_bug

- Model: `openai/gpt-oss-120b` (groq), temperature 0.0, prompt `classifier.v1` (SHA-256 `2406cab727e3…`)
- Generated: 2026-10-22T20:07:06Z
- Tests: 37; with a failed attempt: 4; real_bug: 4
- LLM calls: 2 (2 requests including retries)

## Real bugs (4)

| Test | Case | Confidence | Final outcome | Reasoning | Next action |
|---|---|---|---|---|---|
| `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]` | DASH-005 | 0.92 | failed (3/3 attempts failed) | Rule 4 applied: same error on all attempts, assertion category, no 5xx. | File a bug: fix the pass rate calculation expected value. |
| `tests/ui/login/test_login.py::test_fifth_consecutive_failure_locks_the_account[chromium]` | LOGIN-012 | 0.91 | failed (3/3 attempts failed) | Rule 4 applied: identical assertion failures across attempts, no 5xx. | File a bug: correct the expected lockout status code. |
| `tests/ui/login/test_login.py::test_correct_password_is_refused_while_locked[chromium]` | LOGIN-013 | 0.91 | failed (3/3 attempts failed) | Rule 4 applied: identical assertion failures across attempts, no 5xx. | File a bug: adjust the expected response code for locked account login. |
| `tests/api/test_api.py::test_admin_deletes_a_test_case` | API-009 | 0.93 | failed (3/3 attempts failed) | Rule 4 matched: same error on all attempts, category is assertion, no 5xx seen, leading to real_bug. | File a bug: API returns 200 instead of expected 404 when deleting a test case; update the endpoint or adjust the test expectation. |

Evidence:

- `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]`
  - `signals.same_error_all_attempts:true`
  - `signals.error_category_heuristic:assertion`
  - `attempts[0].error.message:assert '100.0%' == '87.5%'`
- `tests/ui/login/test_login.py::test_fifth_consecutive_failure_locks_the_account[chromium]`
  - `signals.same_error_all_attempts:true`
  - `signals.error_category_heuristic:assertion`
  - `attempts[0].error.message:assert 401 == 423`
- `tests/ui/login/test_login.py::test_correct_password_is_refused_while_locked[chromium]`
  - `signals.same_error_all_attempts:true`
  - `signals.error_category_heuristic:assertion`
  - `attempts[0].error.message:assert 303 == 423`
- `tests/api/test_api.py::test_admin_deletes_a_test_case`
  - `signals.same_error_all_attempts: true`
  - `signals.error_category_heuristic: assertion`
  - `attempts[0].error.message: Expected 404, got 200`
  - `attempts[0].api_last_exchange.status: 200`
