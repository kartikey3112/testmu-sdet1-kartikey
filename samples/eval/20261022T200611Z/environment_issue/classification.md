# Failure classification: run eval-20261022T200611Z-environment_issue

- Model: `openai/gpt-oss-120b` (groq), temperature 0.0, prompt `classifier.v1` (SHA-256 `2406cab727e3…`)
- Generated: 2026-10-22T20:18:09Z
- Tests: 37; with a failed attempt: 37; environment_issue: 37
- LLM calls: 12 (16 requests including retries)

## Environment issues (37)

| Test | Case | Confidence | Final outcome | Reasoning | Next action |
|---|---|---|---|---|---|
| `tests/ui/dashboard/test_dashboard.py::test_total_test_cases_widget_loads[chromium]` | DASH-001 | 0.78 | error (3/3 attempts failed) | Rule 2 does not directly apply, but tie‑break rule leans to environment_issue because the majority of failing tests are 5xx and health checks are failing. | Check the backend/database service and /health endpoint, resolve the 503 responses, then re‑run the dashboard tests. |
| `tests/ui/dashboard/test_dashboard.py::test_date_from_after_date_to_puts_recent_runs_in_error[chromium]` | DASH-002 | 0.78 | error (3/3 attempts failed) | Rule 2 not triggered, but majority 5xx failures and unhealthy health check push classification to environment_issue per tie‑break. | Investigate the API/database health (503), fix the underlying service, and re‑run the test. |
| `tests/ui/dashboard/test_dashboard.py::test_total_test_cases_shows_seed_count[chromium]` | DASH-004 | 0.78 | error (3/3 attempts failed) | Same pattern as other dashboard tests; tie‑break towards environment_issue given the run‑wide 5xx pattern. | Verify the login service/database health, address the 503 errors, then re‑execute the test suite. |
| `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]` | DASH-005 | 0.78 | error (3/3 attempts failed) | Consistent 5xx login failures with unhealthy health checks; tie‑break rule selects environment_issue. | Check backend health (especially database), resolve the 503 response, and re‑run the dashboard tests. |
| `tests/ui/dashboard/test_dashboard.py::test_recent_runs_default_is_latest_ten_newest_first[chromium]` | DASH-007 | 0.78 | error (3/3 attempts failed) | Rule 2 does not match directly, but tie‑break rule leans to environment_issue because many overview tests are 5xx and health checks fail. | Check the backend/database service health (503 response) and resolve the HTTP 500 login error, then re‑run the suite. |
| `tests/ui/dashboard/test_dashboard.py::test_same_day_date_range_returns_that_run[chromium]` | DASH-009 | 0.78 | error (3/3 attempts failed) | Rule 2 does not match directly, but tie‑break rule leans to environment_issue because many overview tests are 5xx and health checks fail. | Investigate the failing health endpoint (503) and the underlying 500 error during login, fix the service, then re‑run. |
| `tests/ui/dashboard/test_dashboard.py::test_wide_viewport_shows_sidebar_and_two_columns[chromium]` | DASH-011 | 0.78 | failed (3/3 attempts failed) | Rule 2 does not match directly, but tie‑break rule leans to environment_issue because many overview tests are 5xx and health checks fail. | Check the application’s login service and database health (503), resolve the 500 error, then re‑run the test. |
| `tests/ui/dashboard/test_dashboard.py::test_narrow_viewport_hides_sidebar_behind_menu[chromium]` | DASH-013 | 0.78 | failed (3/3 attempts failed) | Rule 2 does not match directly, but tie‑break rule leans to environment_issue because many overview tests are 5xx and health checks fail. | Inspect and fix the backend/database causing the 503 health check and 500 login failure, then re‑run the suite. |
| `tests/ui/dashboard/test_dashboard.py::test_admin_sees_all_five_widgets[chromium]` | DASH-014 | 0.78 | error (3/3 attempts failed) | No rule matched directly; many tests in the overview have 5xx category, so tie‑break leans to environment_issue (rule 2 tie‑break). | Check the database health endpoint and underlying DB service, then re‑run the suite. |
| `tests/ui/dashboard/test_dashboard.py::test_viewer_sees_only_three_widgets[chromium]` | DASH-015 | 0.78 | error (3/3 attempts failed) | No rule matched directly; many tests in the overview have 5xx category, so tie‑break leans to environment_issue (rule 2 tie‑break). | Check the database health endpoint and underlying DB service, then re‑run the suite. |
| `tests/ui/dashboard/test_dashboard.py::test_viewer_gets_403_from_flaky_tests_endpoint[chromium]` | DASH-016 | 0.78 | error (3/3 attempts failed) | No rule matched directly; many tests in the overview have 5xx category, so tie‑break leans to environment_issue (rule 2 tie‑break). | Check the database health endpoint and underlying DB service, then re‑run the suite. |
| `tests/ui/dashboard/test_smoke_dashboard.py::test_total_test_cases_widget_matches_api_and_seed[chromium]` | — | 0.78 | error (3/3 attempts failed) | No rule matched directly; many tests in the overview have 5xx category, so tie‑break leans to environment_issue (rule 2 tie‑break). | Check the database health endpoint and underlying DB service, then re‑run the suite. |
| `tests/ui/login/test_login.py::test_admin_signs_in_with_correct_credentials[chromium]` | LOGIN-001 | 0.92 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx response was seen in the attempts. | Check the login backend/database service for the 500 errors and resolve the 5xx condition before re‑running. |
| `tests/ui/login/test_login.py::test_correct_password_still_works_after_a_failed_attempt[chromium]` | LOGIN-004 | 0.91 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx response was observed despite the error category being assertion. | Investigate the server error causing the 500 responses during login and fix the underlying service issue. |
| `tests/ui/login/test_login.py::test_unknown_email_gets_generic_error[chromium]` | LOGIN-005 | 0.93 | failed (3/3 attempts failed) | Rule 2 applied as the test consistently saw a 5xx response, indicating an environment problem. | Examine the authentication endpoint and database health (503 health check) to address the 500 errors causing the failure. |
| `tests/ui/login/test_login.py::test_reset_link_sets_a_new_password[chromium]` | LOGIN-006 | 0.92 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx error was seen in all attempts. | Check the backend service/database that returned 500/503 errors, then re‑run the test. |
| `tests/ui/login/test_login.py::test_reset_link_is_expired_at_exactly_30_minutes[chromium]` | LOGIN-007 | 0.92 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx error was seen in all attempts. | Investigate the server returning 500/503 for the outbox endpoint and fix the underlying issue before re‑running. |
| `tests/ui/login/test_login.py::test_forgot_password_does_not_reveal_unknown_email[chromium]` | LOGIN-008 | 0.90 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx error was observed despite the assertion failure. | Resolve the 5xx backend error causing the missing UI element, then re‑run the test. |
| `tests/ui/login/test_login.py::test_active_session_gives_access_to_dashboard[chromium]` | LOGIN-009 | 0.92 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx response was seen in the failed attempts. | Check backend services (e.g., database) for the 500 errors and re‑run the test. |
| `tests/ui/login/test_login.py::test_session_is_expired_at_exactly_1800_seconds[chromium]` | LOGIN-010 | 0.92 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx response was seen in the failed attempts. | Investigate the server/database causing the 500 error and then re‑run the test. |
| `tests/ui/login/test_login.py::test_fifth_consecutive_failure_locks_the_account[chromium]` | LOGIN-012 | 0.92 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx response was seen in the failed attempts. | Check the authentication service/database for the 500 errors and re‑run the test. |
| `tests/ui/login/test_login.py::test_correct_password_is_refused_while_locked[chromium]` | LOGIN-013 | 0.92 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx response was seen in the failed attempts. | Investigate backend services (e.g., database, auth API) and health endpoint, then re‑run the test. |
| `tests/ui/login/test_login.py::test_lock_has_run_out_at_exactly_15_minutes[chromium]` | LOGIN-014 | 0.92 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx response was seen in the failed attempts. | Check the login service and its dependencies for 5xx errors and health status, then re‑run the test. |
| `tests/ui/login/test_smoke_login.py::test_admin_can_sign_in_and_reach_dashboard[chromium]` | — | 0.92 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx response was seen in the failed attempts. | Resolve the internal server error causing the 5xx response and ensure health checks pass, then re‑run the test. |
| `tests/api/test_api.py::test_valid_admin_token_lists_test_cases` | API-001 | 0.92 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx response was seen in every attempt. | Check the authentication service and database health, then re‑run the test. |
| `tests/api/test_api.py::test_tampered_token_is_rejected` | API-004 | 0.92 | error (3/3 attempts failed) | Rule 2 applied because a 5xx response was seen in every attempt. | Investigate the 5xx errors from the token endpoint and underlying services, then re‑run. |
| `tests/api/test_api.py::test_admin_creates_a_test_case` | API-005 | 0.92 | error (3/3 attempts failed) | Rule 2 applied because a 5xx response was seen in every attempt. | Fix the server-side error (likely database or auth service) and re‑execute the test. |
| `tests/api/test_api.py::test_admin_deletes_a_test_case` | API-009 | 0.93 | error (3/3 attempts failed) | Rule 2 matched because a 5xx response was seen in every attempt, indicating an environment problem. No passed rerun and health checks failed, reinforcing the environment issue. | Check the API backend and database health, resolve the 5xx errors, then re‑run the test. |
| `tests/api/test_api.py::test_viewer_cannot_create_a_test_case` | API-010 | 0.93 | error (3/3 attempts failed) | Rule 2 matched because a 5xx response was seen in every attempt, indicating an environment problem. No passed rerun and health checks failed, reinforcing the environment issue. | Investigate the authentication service and database health, fix the 5xx errors, then re‑run the test. |
| `tests/api/test_api.py::test_unknown_id_returns_404` | API-014 | 0.93 | error (3/3 attempts failed) | Rule 2 matched because a 5xx response was seen in every attempt, indicating an environment problem. No passed rerun and health checks failed, reinforcing the environment issue. | Verify the auth token endpoint and underlying services for failures, resolve the 5xx responses, then re‑run the test. |
| `tests/api/test_api.py::test_database_fault_returns_500` | API-017 | 0.93 | error (3/3 attempts failed) | Rule 2 matched because a 5xx response was seen in every attempt. The same 5xx error persisted across attempts, indicating an external service problem. | Check the database/API backend for internal errors (503 health check, 500 token request) and retry after fixing the service. |
| `tests/api/test_api.py::test_list_works_again_after_fault_is_cleared` | API-018 | 0.93 | error (3/3 attempts failed) | Rule 2 matched because a 5xx response was observed in all attempts. Consistent 5xx errors point to an environment problem rather than code defects. | Investigate the API token endpoint and database health (503) and resolve the internal server error before re‑running the test. |
| `tests/api/test_api.py::test_sixty_requests_in_a_minute_succeed` | API-019 | 0.93 | error (3/3 attempts failed) | Rule 2 applied as each attempt returned a 5xx error. The uniform failure across attempts indicates an external service issue. | Fix the underlying API/database fault causing 500 responses and then re‑execute the test suite. |
| `tests/api/test_api.py::test_sixty_first_request_is_rate_limited` | API-020 | 0.92 | error (3/3 attempts failed) | Rule 2 applies because a 5xx response was seen in every attempt. The same 5xx error repeats across attempts, indicating an external service problem. | Investigate the token endpoint and backend services (e.g., database) that returned 500, fix the underlying issue, then re‑run the test. |
| `tests/api/test_api.py::test_token_response_matches_schema` | API-021 | 0.91 | failed (3/3 attempts failed) | Rule 2 applies because a 5xx response was observed in all attempts. Consistent 5xx errors point to an environment problem rather than a code bug. | Check the authentication service for the 500 Internal Server Error (e.g., database health), resolve it, and re‑execute the test. |
| `tests/api/test_api.py::test_created_test_case_matches_schema` | API-022 | 0.92 | error (3/3 attempts failed) | Rule 2 applies since every attempt resulted in a 5xx error. The repeated 5xx indicates an external dependency failure, classifying it as an environment issue. | Diagnose the token acquisition path and underlying services that returned 500, fix the root cause, then re‑run the suite. |
| `tests/api/test_smoke_api.py::test_token_then_list_test_cases` | — | 0.92 | failed (3/3 attempts failed) | Rule 2 applied because a 5xx response was seen in every attempt. | Investigate backend/API services (e.g., database health) and resolve the 5xx errors, then re‑run the test. |

Evidence:

- `tests/ui/dashboard/test_dashboard.py::test_total_test_cases_widget_loads[chromium]`
  - `signals.health_ok_at_failure:false`
  - `attempts[0].error.message:"Could not log in as admin: HTTP 500"`
  - `attempts[0].health_at_failure.status:503`
- `tests/ui/dashboard/test_dashboard.py::test_date_from_after_date_to_puts_recent_runs_in_error[chromium]`
  - `signals.health_ok_at_failure:false`
  - `attempts[0].error.message:"Could not log in as admin: HTTP 500"`
  - `attempts[0].health_at_failure.status:503`
- `tests/ui/dashboard/test_dashboard.py::test_total_test_cases_shows_seed_count[chromium]`
  - `signals.health_ok_at_failure:false`
  - `attempts[0].error.message:"Could not log in as admin: HTTP 500"`
  - `attempts[0].health_at_failure.status:503`
- `tests/ui/dashboard/test_dashboard.py::test_pass_rate_shows_latest_run[chromium]`
  - `signals.health_ok_at_failure:false`
  - `attempts[0].error.message:"Could not log in as admin: HTTP 500"`
  - `attempts[0].health_at_failure.status:503`
- `tests/ui/dashboard/test_dashboard.py::test_recent_runs_default_is_latest_ten_newest_first[chromium]`
  - `signals.health_ok_at_failure:false`
  - `attempts[0].error.message:"Could not log in as admin: HTTP 500"`
  - `attempts[0].health_at_failure.status:503`
  - `signals.error_category_heuristic:"5xx"`
- `tests/ui/dashboard/test_dashboard.py::test_same_day_date_range_returns_that_run[chromium]`
  - `signals.health_ok_at_failure:false`
  - `attempts[0].error.message:"Could not log in as admin: HTTP 500"`
  - `attempts[0].health_at_failure.status:503`
  - `signals.error_category_heuristic:"5xx"`
- `tests/ui/dashboard/test_dashboard.py::test_wide_viewport_shows_sidebar_and_two_columns[chromium]`
  - `signals.health_ok_at_failure:false`
  - `attempts[0].error.message:"Could not log in as admin: HTTP 500"`
  - `attempts[0].health_at_failure.status:503`
  - `signals.error_category_heuristic:"5xx"`
- `tests/ui/dashboard/test_dashboard.py::test_narrow_viewport_hides_sidebar_behind_menu[chromium]`
  - `signals.health_ok_at_failure:false`
  - `attempts[0].error.message:"Could not log in as admin: HTTP 500"`
  - `attempts[0].health_at_failure.status:503`
  - `signals.error_category_heuristic:"5xx"`
- `tests/ui/dashboard/test_dashboard.py::test_admin_sees_all_five_widgets[chromium]`
  - `signals.passed_on_rerun: false`
  - `signals.http_5xx_seen: false`
  - `attempts[0].error.message: Could not log in as admin: HTTP 500`
  - `attempts[0].health_at_failure.status: 503`
- `tests/ui/dashboard/test_dashboard.py::test_viewer_sees_only_three_widgets[chromium]`
  - `signals.passed_on_rerun: false`
  - `signals.http_5xx_seen: false`
  - `attempts[0].error.message: Could not log in as viewer: HTTP 500`
  - `attempts[0].health_at_failure.status: 503`
- `tests/ui/dashboard/test_dashboard.py::test_viewer_gets_403_from_flaky_tests_endpoint[chromium]`
  - `signals.passed_on_rerun: false`
  - `signals.http_5xx_seen: false`
  - `attempts[0].error.message: Could not log in as viewer: HTTP 500`
  - `attempts[0].health_at_failure.status: 503`
- `tests/ui/dashboard/test_smoke_dashboard.py::test_total_test_cases_widget_matches_api_and_seed[chromium]`
  - `signals.passed_on_rerun: false`
  - `signals.http_5xx_seen: false`
  - `attempts[0].error.message: Could not log in as admin: HTTP 500`
  - `attempts[0].health_at_failure.status: 503`
- `tests/ui/login/test_login.py::test_admin_signs_in_with_correct_credentials[chromium]`
  - `signals.http_5xx_seen:true`
  - `attempts[0].ui.failed_requests:"POST /login -> 500"`
  - `attempts[0].health_at_failure.status:503`
- `tests/ui/login/test_login.py::test_correct_password_still_works_after_a_failed_attempt[chromium]`
  - `signals.http_5xx_seen:true`
  - `attempts[0].ui.console_errors:"Failed to load resource: the server responded with a status of 500 (Internal Server Error)"`
  - `attempts[0].health_at_failure.status:503`
- `tests/ui/login/test_login.py::test_unknown_email_gets_generic_error[chromium]`
  - `signals.http_5xx_seen:true`
  - `attempts[0].ui.failed_requests:"POST /login -> 500"`
  - `attempts[0].health_at_failure.status:503`
- `tests/ui/login/test_login.py::test_reset_link_sets_a_new_password[chromium]`
  - `signals.http_5xx_seen:true`
  - `attempts[0].error.type:"HTTPStatusError"`
  - `attempts[0].health_at_failure.status:503`
- `tests/ui/login/test_login.py::test_reset_link_is_expired_at_exactly_30_minutes[chromium]`
  - `signals.http_5xx_seen:true`
  - `attempts[0].error.type:"HTTPStatusError"`
  - `attempts[0].health_at_failure.status:503`
- `tests/ui/login/test_login.py::test_forgot_password_does_not_reveal_unknown_email[chromium]`
  - `signals.http_5xx_seen:true`
  - `attempts[0].error.type:"AssertionError"`
  - `attempts[0].health_at_failure.status:503`
- `tests/ui/login/test_login.py::test_active_session_gives_access_to_dashboard[chromium]`
  - `signals.http_5xx_seen: true`
  - `attempts[0].ui.failed_requests: ["POST /login -> 500","GET /dashboard -> 500"]`
  - `attempts[0].health_at_failure.status: 503`
- `tests/ui/login/test_login.py::test_session_is_expired_at_exactly_1800_seconds[chromium]`
  - `signals.http_5xx_seen: true`
  - `attempts[0].ui.failed_requests: ["POST /login -> 500"]`
  - `attempts[0].health_at_failure.status: 503`
- `tests/ui/login/test_login.py::test_fifth_consecutive_failure_locks_the_account[chromium]`
  - `signals.http_5xx_seen: true`
  - `attempts[0].ui.failed_requests: ["POST /login -> 500 (x5)"]`
  - `attempts[0].health_at_failure.status: 503`
- `tests/ui/login/test_login.py::test_correct_password_is_refused_while_locked[chromium]`
  - `signals.http_5xx_seen: true`
  - `attempts[0].ui.failed_requests: ["POST /login -> 500 (x6)"]`
  - `attempts[0].health_at_failure.status: 503`
- `tests/ui/login/test_login.py::test_lock_has_run_out_at_exactly_15_minutes[chromium]`
  - `signals.http_5xx_seen: true`
  - `attempts[0].ui.failed_requests: ["POST /login -> 500 (x6)"]`
  - `attempts[0].health_at_failure.status: 503`
- `tests/ui/login/test_smoke_login.py::test_admin_can_sign_in_and_reach_dashboard[chromium]`
  - `signals.http_5xx_seen: true`
  - `attempts[0].ui.failed_requests: ["POST /login -> 500"]`
  - `attempts[0].health_at_failure.status: 503`
- `tests/api/test_api.py::test_valid_admin_token_lists_test_cases`
  - `signals.http_5xx_seen:true`
  - `attempts[0].api_last_exchange.status:500`
  - `attempts[0].error.type:KeyError`
- `tests/api/test_api.py::test_tampered_token_is_rejected`
  - `signals.http_5xx_seen:true`
  - `attempts[0].api_last_exchange.status:500`
  - `attempts[0].error.type:AssertionError`
- `tests/api/test_api.py::test_admin_creates_a_test_case`
  - `signals.http_5xx_seen:true`
  - `attempts[0].api_last_exchange.status:500`
  - `attempts[0].error.type:AssertionError`
- `tests/api/test_api.py::test_admin_deletes_a_test_case`
  - `signals.http_5xx_seen:true`
  - `attempts[0].api_last_exchange.status:500`
  - `attempts[0].error.message:"Token request failed: 500"`
  - `attempts[0].health_at_failure.status:503`
- `tests/api/test_api.py::test_viewer_cannot_create_a_test_case`
  - `signals.http_5xx_seen:true`
  - `attempts[0].api_last_exchange.status:500`
  - `attempts[0].error.message:"Token request failed: 500"`
  - `attempts[0].health_at_failure.status:503`
- `tests/api/test_api.py::test_unknown_id_returns_404`
  - `signals.http_5xx_seen:true`
  - `attempts[0].api_last_exchange.status:500`
  - `attempts[0].error.message:"Token request failed: 500"`
  - `attempts[0].health_at_failure.status:503`
- `tests/api/test_api.py::test_database_fault_returns_500`
  - `signals.http_5xx_seen: true`
  - `attempts[0].api_last_exchange.status: 500`
  - `attempts[0].error.message: Token request failed: 500`
- `tests/api/test_api.py::test_list_works_again_after_fault_is_cleared`
  - `signals.http_5xx_seen: true`
  - `attempts[0].api_last_exchange.status: 500`
  - `attempts[0].error.message: Token request failed: 500`
- `tests/api/test_api.py::test_sixty_requests_in_a_minute_succeed`
  - `signals.http_5xx_seen: true`
  - `attempts[0].api_last_exchange.status: 500`
  - `attempts[0].error.message: Token request failed: 500`
- `tests/api/test_api.py::test_sixty_first_request_is_rate_limited`
  - `signals.http_5xx_seen: true`
  - `attempts[0].api_last_exchange.status: 500`
  - `attempts[0].error.message: Token request failed: 500`
- `tests/api/test_api.py::test_token_response_matches_schema`
  - `signals.http_5xx_seen: true`
  - `attempts[0].api_last_exchange.status: 500`
  - `attempts[0].error.message: assert 500 == 200`
- `tests/api/test_api.py::test_created_test_case_matches_schema`
  - `signals.http_5xx_seen: true`
  - `attempts[0].api_last_exchange.status: 500`
  - `attempts[0].error.message: Token request failed: 500`
- `tests/api/test_smoke_api.py::test_token_then_list_test_cases`
  - `signals.http_5xx_seen: true`
  - `attempts[0].api_last_exchange.status: 500`
  - `attempts[1].api_last_exchange.status: 500`
  - `attempts[0].health_at_failure.status: 503`
