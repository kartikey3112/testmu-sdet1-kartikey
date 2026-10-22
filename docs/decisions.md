# Decisions

Each entry: the decision, the alternatives considered, and why.

## D1. Stack: Playwright + Python + pytest

- **Decision:** `pytest-playwright` for UI, `httpx` + `jsonschema`/`pydantic` for API, pytest as the runner with `pytest-html`, JUnit XML and `pytest-rerunfailures`.
- **Alternatives:** Playwright + TypeScript; Selenium + Python; `requests` for API tests.
- **Why:** Python and Playwright are my strongest stack. Playwright gives auto-waiting and traces. `httpx` is explicit and simple. Rerun results are evidence the Task 3 classifier uses.

## D2. Build our own app under test ("TestMu Lite")

- **Decision:** a small FastAPI + Jinja2 + SQLite test-management app, started with one command and reset to deterministic seed data.
- **Alternatives:** public demo sites (e.g. saucedemo, reqres, the-internet).
- **Why:**
  - The required scenarios need behaviour public sites don't let us control: brute-force lockout, session expiry, forgot-password tokens, permission-based visibility, rate limiting, schema validation.
  - Task 3 needs failures whose true cause is known. Fault injection with a fixed fault → bucket map makes classifier accuracy measurable.
  - Tests against third-party sites break for reasons outside our control.

## D3. LLM provider: Groq free tier, model `openai/gpt-oss-120b`

- **Decision:** call Groq through its OpenAI-compatible HTTP API. Configured only via `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`. Temperature 0.
- **Alternatives:** OpenAI or Anthropic paid APIs; local Ollama only.
- **Why:** free, fast, and OpenAI-compatible, so Ollama works by changing env vars only. Model name verified in the Groq console on 2026-10-22.

## D4. Python version

- **Decision:** code targets Python 3.11+ (`ruff` `target-version = "py311"`). Local development uses 3.14.6; CI will pin a version in Phase 6.
- **Why:** the brief requires 3.11+. Dependency pins were resolved on 3.14.6.

## D5. `make` is a convenience, not a requirement

- **Decision:** keep a `Makefile` for reviewers and CI. The README lists the raw `python -m ...` command for every target.
- **Alternatives:** require `make` on Windows; add a separate PowerShell task runner.
- **Why:** each target is a one-line wrapper. Showing the raw command avoids extra tooling on Windows and keeps one source of truth.

## D6. Test packages have `__init__.py`

- **Decision:** every folder under `tests/` is a package.
- **Why:** pytest's default import mode fails when two test files share a basename (e.g. `test_permissions.py` in both `ui/dashboard` and `api`). Packages avoid that.

## D7. CI workflow added in Phase 6

- **Decision:** `.github/workflows/` exists in the scaffold with a `.gitkeep`; `ci.yml` is written in Phase 6.
- **Why:** a workflow with nothing to test would only run an install step. The real one is written when there are tests to run.

## D8. LF line endings everywhere (`.gitattributes`)

- **Decision:** `* text=auto eol=lf`.
- **Why:** prompts are stored byte-for-byte and hashed (SHA-256) in generation metadata. Without this, Git on Windows would check them out with CRLF and the hashes would differ between machines. It also keeps the `Makefile` valid on Linux CI.

## D9. Test clock instead of waiting in real time

- **Decision:** the app reads time from one `clock` (`app/settings.py`). In TEST_MODE, `POST /_test/clock {"advance_seconds": N}` moves it forward. Session expiry, lockout expiry, reset-token expiry, JWT expiry and the rate-limit window all use it.
- **Alternatives:** tiny TTLs set by env var and waiting them out; editing rows in the DB from tests.
- **Why:** expiry tests stay fast and deterministic, with no sleeps (a ground rule). Tests use the real rules rather than reaching into the database. JWT expiry is checked against this clock, not PyJWT's built-in check.

## D10. Dashboard widget endpoints live under `/api/v1/dashboard` and accept session or token

- **Decision:** the browser calls them with its session cookie; API tests call them with a bearer token. Same endpoint, same 403 for viewers.
- **Why:** one source of each number, so a test can assert UI value == API value == expected-from-seed. Permission checks are tested once at the API level and once in the UI.

## D11. How some edge behaviours are defined

These are choices the brief left open. They are written here so the test-generation prompts can quote them instead of guessing.

- **Lockout:** the failure that reaches the threshold returns the lockout message (HTTP 423), not the generic one. A correct password during the lock is still refused. Unknown emails never count towards a lockout. When a lock runs out, counting starts again from zero. The API token endpoint shares the same counter, so the API can't be used to get around the lockout.
- **Sessions:** fixed lifetime from login (not sliding). Expired session → 303 to `/login?reason=expired`.
- **Password reset:** minimum 8 characters, confirmation must match. A successful reset clears the lockout and signs the user out everywhere.
- **Update is `PATCH`** (partial). Titles are unique case-insensitively and trimmed; blank titles get a 422.
- **500 path:** `ENV_DB_UNAVAILABLE` makes every DB connection fail; the unhandled error becomes a 500 in the standard error body. `/health` reports `database: fail` with a 503 at the same time.
- **Rate limit:** a fixed one-minute window per bearer token. Request number `RATE_LIMIT_PER_MIN + 1` gets a 429 with `Retry-After` (seconds until the window resets). Session-cookie calls from the UI are not rate limited.
- **Recent runs:** newest first by default. Sorting by pass rate breaks ties newest first. `date_from` after `date_to` returns 422.
- **Not implemented:** CSRF protection on forms. The app is only ever run locally for testing.

## D12. Cached role logins with `storage_state`, kept across per-test resets

- **Decision:** every UI/API test starts with `POST /_test/reset?keep_sessions=true`. Admin and viewer each log in once over HTTP; the session cookie becomes Playwright `storage_state`. Before each use the session is checked, and if it has gone (e.g. a test moved the clock past the TTL) the role logs in again.
- **Alternatives:** log in through the UI in every test; reset only some tables.
- **Why:** a full reset keeps tests independent. Keeping sessions avoids a UI login per test. The login page still gets its own tests.

## D13. Response schemas are written on the test side

- **Decision:** `framework/schemas.py` holds hand-written JSON Schemas with `additionalProperties: false`, checked with `jsonschema`. It does not use the app's `/openapi.json`. `rfc3339-validator` is installed so `date-time` formats are really checked; without it jsonschema silently skips them.
- **Why:** validating the app against its own generated schema would pass even when the app changes by mistake.

## D14. Markers come from folders

- **Decision:** `tests/conftest.py` adds `ui`/`api`/`unit` and `login`/`dashboard` markers from the test's path. `smoke` and `case(id)` are set by hand.
- **Why:** less repetition, and no test can be filed under one folder but marked as another.

## D15. One `time.sleep`, in server start-up only

- **Decision:** `framework/app_server.py` polls `/health` every 0.1 s while the uvicorn subprocess starts. No test waits with `sleep`; tests use Playwright web-first assertions and the test clock.
- **Why:** waiting for a separate process to accept connections has no event to wait on. It runs once per session, during fixture setup, and stops at a deadline.

## D16. Task 3 hook point: `pytest_testmu_attempt_finished`

- **Decision:** the framework collects evidence per test attempt: console errors, failed requests, page URL, screenshot and trace paths, and the last API exchange with tokens redacted. After each attempt it calls a custom hook (`framework/hookspecs.py`). The Phase 5 collector will implement that hook to write `execution-log.jsonl`.
- **Why:** the classifier needs per-attempt data including reruns. A hook keeps the classifier out of the framework code, so it can be turned off or replaced.

## D17. JSON mode, not strict `json_schema`, for test generation

- **Decision:** requests use `response_format: {"type": "json_object"}`. The schema is in the prompt and enforced afterwards by `ai/testgen/validators.py`.
- **Alternatives:** Groq's strict `json_schema` mode.
- **Why:** strict mode requires every object to list all its properties. `test_data` is free-form on purpose. JSON mode guarantees parseable output, and our validator reports every schema violation (API v1 had 24) instead of the provider hiding them.

## D18. Output budget and rate-limit handling found on the first real runs

- **What happened:**
  - Login v1's first run stopped at 3,072 completion tokens (`finish_reason: length`). 2,283 of them were gpt-oss's hidden reasoning, so the JSON was cut short.
  - Dashboard and API v1 were then refused with HTTP 413: "tokens per minute (TPM): Limit 8000". The free tier's per-minute window was full from the previous call. Groq reports this as 413 + `rate_limit_exceeded`, not 429.
- **Decision:**
  - The runner sets `max_completion_tokens = 16384` and records `finish_reason`. A truncated response always fails validation.
  - The LLM client treats 413 `rate_limit_exceeded` like 429 and backs off for up to about 62 s, honouring `Retry-After`.
- **Why:** these are request settings, not prompt problems, so v1 was re-run unchanged (same SHA-256). The truncated first run is kept in `generated/raw/` as evidence.

## D19. Which generated cases were automated, and how

- **Decision:** every P0 `automation_candidate` case was automated, plus a few P1/P2 cases so that each required coverage area has at least one automated test: 11 Login, 11 Dashboard, 12 API. Each test is linked with `@pytest.mark.case("<ID>")`, and `docs/traceability.md` is generated from the run.
- **Expected results come from the case.** Where a case could not be run as written, the test docstring says what was adapted. For example, API-009 hard-codes id 26, so the test deletes the id its own create call returned.
- **Cases with a wrong expectation are not "fixed" to pass.** They are left out with the reason recorded:
  - DASH-010: tampered cookie, expects `?reason=expired`. Confirmed wrong by running it as generated.
  - DASH-008: expects the error code where the UI shows the message.
- **Flakiness found and fixed:** LOGIN-010 (session expiry) failed about 2 runs in 3. Widget requests from the post-login page load could reach the server after the clock jump, expire and delete the session first. The test now waits for the dashboard to finish loading. After the fix: 10 of 10 passes alone, and 3 full-suite runs of 37 of 37.
- **Rate-limit tests** move the app clock to the start of a fresh minute first, so a burst can't straddle two windows.
- **Tests can fail:** with each injected `real_bug` fault, exactly the targeted tests fail: `BUG_PASS_RATE_OFF_BY_ONE` → DASH-005; `BUG_DELETE_NOT_PERSISTED` → API-009; `BUG_LOCKOUT_THRESHOLD_WRONG` → LOGIN-012 and LOGIN-013.

## D20. Classifier payload: compact, redacted, chunked, with code-computed signals

- **Decision:** only tests with a failed attempt are sent. The first failed attempt carries full detail; later attempts carry a short form (type, message, location, status, health). Repeated browser errors are collapsed with a count, local origins are stripped from URLs, and Playwright's call log is dropped from messages.
- **Why:** the first dry run (3 faults, `--reruns 2`, 10 failing tests) produced 10 chunks of about 9.8k characters each, one test per chunk, because every rerun repeated the same 2.4k characters. After compaction it is 4 chunks. The free Groq tier allows 8,000 tokens per minute for prompt, payload and answer together.
- **Signals are computed in code and passed as hints:** `passed_on_rerun`, `same_error_all_attempts` (on normalised messages), `error_category_heuristic`, `http_5xx_seen`, `health_ok_at_failure`, duration spread.
  - Two problems found in the dry run shaped them. Every Playwright `expect()` failure contains "with timeout 5000ms" in its call log, so categories use the first line of the message only.
  - With `ENV_WIDGET_API_503`, UI tests fail as assertions while the 503s appear only in the browser's network log, hence `http_5xx_seen`.
- **Ground truth isolation:** active faults are written to `run-meta.json` for evaluation only. The payload builder never reads it, and a unit test checks this.

## D21. Classifier output is validated and never guessed

- **Decision:** the response must parse as the Pydantic schema, include every test in the chunk exactly once with its exact `case_id`, keep reasoning to at most 3 sentences, and cite only evidence fields that exist in that test's payload (paths are resolved).
  - Any problem triggers one retry with the problems listed.
  - Anything still invalid is `unclassified`.
  - `run_summary` is computed in code, not by the model.
- **Why:** a plausible but unsupported label is worse than "unclassified" for triage. Checking the evidence paths stops the model from citing facts that are not in its input.

## D22. Showing results inside the pytest-html report

- **Decision:** classification runs in our `pytest_sessionfinish`, before pytest-html's own (which is `trylast`) writes the file. The run summary goes into pytest-html's summary list. The "LLM bucket" column and per-test blocks are added to the row data pytest-html holds until then.
- **Trade-off:** that row data is internal to pytest-html, so `pytest-html==4.2.0` is pinned and the code says why. `make classify RUN=<id>` also writes standalone `classification.json` and `classification.md`.
