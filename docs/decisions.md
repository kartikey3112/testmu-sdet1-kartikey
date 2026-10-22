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
