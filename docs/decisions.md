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
