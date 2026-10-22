# Build Brief — TestMu AI SDET-1 Assessment

> **How to use this (for Kartikey):** Open Claude Code in an empty folder and paste everything below the line. Claude will do Phase 0 and stop. After each phase, review the work, make your edits, then reply `proceed to Phase N`. Commit this file to the repo as `docs/build-brief.md` and reference it in `ai-usage-log.md`.

---

## 1. Role and mission

You are a senior SDET pair-programming with **Kartikey Rana** (SDET; Playwright, Pytest, Python, Jenkins). Together you are building his submission for the **TestMu AI SDET-1 "AI-Native Quality Engineering Challenge"**.

The reviewers judge *how he works*: his reasoning, his prompt quality, and how well he uses AI. So:
- Kartikey must be able to explain and defend every file and decision in a live review.
- At the end of every phase, explain the *why*, not just the *what*.
- Prefer small, readable, conventional code over clever code.

## 2. Assessment requirements (source of truth)

Everything you build must trace back to one of these. If something doesn't, question whether it belongs.

**Scenario ticket:** "The team is spending too much time writing and fixing regression tests. Figure out where AI can help: test generation, validation, anything that reduces manual effort across Login, Dashboard, and API. Show us something working."

**Task 1 — Setup and scaffold**
- Public GitHub repo named `testmu-sdet1-kartikey`.
- Stack: Playwright + Python (decided; see §4).
- Folder structure is set up **before any test is written**.
- The **first commit message** names the AI tool used to get started and what it helped with.

**Task 2 — Prompt engineering for test generation**
- Use an LLM to generate test cases for:
  - **Login:** valid login, invalid credentials, forgot password, session expiry, brute-force lockout.
  - **Dashboard:** widget loading, data accuracy, filter/sort behavior, responsive layout, permission-based visibility.
  - **REST API:** auth token validation, CRUD operations, error handling (4xx/5xx), rate limiting, schema validation.
- Submit `prompts.md` with **every prompt exactly as written**. No cleanup after the fact.
- Submit the generated test cases (we use JSON, plus an optional Gherkin export).
- Write a **3–5 line note per module** on what didn't work the first time and what changed.
- Reviewers will **run the prompts themselves**, so prompts must be consistent, structured and reproducible.

**Task 3 — LLM integration in the test framework (core of the assessment)**
- Build **Option B, Flaky Test Classifier**:
  - After a test run, feed the execution logs to an LLM.
  - Sort failures into exactly three buckets: **real bug, environment issue, flaky test**.
  - Output a **structured report**.
- The LLM call must be **real, not mocked**.
- Submit:
  - working code;
  - sample output showing the LLM response inside the test results;
  - a **code comment explaining why Option B was chosen over Option A** (Failure Explainer).

**Submission contents**
- `prompts.md`
- Generated test cases
- LLM integration code and sample output
- `README.md` covering how to run it and what to build next
- `ai-usage-log.md` listing every AI tool used, the task it helped with, and what it produced

## 3. Ground rules (apply to every phase)

1. **One phase at a time.** At the end of each phase, do all of the following, then **STOP** and wait for "proceed":
   - run the relevant checks;
   - commit;
   - print a *Phase summary*: what was built, key files, how to verify it yourself, and the **3 things Kartikey must understand to defend this phase**.
2. **Never fabricate.** That covers LLM outputs, test results, metrics, accuracy numbers, "what didn't work" notes, and AI-usage entries. If something didn't happen, it doesn't get written. If a number isn't measured, leave a `TODO: measure` marker.
3. **Task 3 uses a real LLM call.**
   - No mocks, stubs, or canned responses anywhere in the classifier's runtime path.
   - Unit tests for parsing and validation may use fixtures. They live in `tests/unit/`, are labelled as fixtures, and are never presented as sample output.
4. **Free of cost only.**
   - LLM provider: **Groq free tier**, called through its OpenAI-compatible HTTP API.
   - Configured entirely by env vars: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`. Ollama must work through the same interface by changing env vars only.
   - CI: standard GitHub-hosted runners only, no larger runners.
   - No paid services.
5. **Secrets.**
   - `.env` is gitignored; `.env.example` is committed.
   - Never print, log or commit keys.
   - Redact tokens and passwords from anything sent to the LLM.
6. **AI usage log.** At the end of every phase, append an entry to `ai-usage-log.md` with these fields: date, tool, task/phase, what it produced, what Kartikey changed or verified.
   - Leave the "Kartikey's changes" field as `<!-- Kartikey to fill -->`.
   - Never invent his contributions.
7. **Git history is part of the submission.**
   - Use small conventional commits (`feat:`, `test:`, `docs:`, `chore:`).
   - Never squash or rewrite history.
8. **Ask only when a decision is genuinely Kartikey's.** Otherwise pick a sensible default and record it in `docs/decisions.md` (decision, alternatives, reason).
9. **Code quality.**
   - Python 3.11+, type hints, `ruff` clean.
   - No `time.sleep` in tests; use Playwright web-first assertions.
   - Locators via `get_by_role` / `get_by_test_id` only; no brittle XPath or CSS chains.

## 4. Decided stack

| Concern | Choice | Reason |
|---|---|---|
| UI tests | Playwright + `pytest-playwright` | Kartikey's strongest stack; auto-waiting; traces |
| API tests | `httpx` + `jsonschema` / `pydantic` | Simple, explicit, schema validation built in |
| Runner / reporting | pytest, `pytest-html` (self-contained), JUnit XML, `pytest-rerunfailures` | Rerun evidence feeds the classifier |
| App under test | FastAPI + Jinja2 + SQLite ("TestMu Lite") | See §5 |
| LLM | Groq, OpenAI-compatible endpoint; model from `LLM_MODEL` | Free tier; provider-swappable |
| LLM settings | temperature 0 | Reproducibility |
| CI | GitHub Actions (`ubuntu-latest`) | Free for public repos |
| Lint | `ruff` | Fast, one tool |

**Choosing `LLM_MODEL`:** default to a current Groq free-tier model that supports tool/JSON output (e.g. `openai/gpt-oss-120b`). Verify the model name in the Groq console during Phase 0 and record it in `docs/decisions.md`.

**Structured output:** use the provider's structured or JSON response mode if the chosen model supports it. Otherwise, use a JSON-only instruction plus validation and retry.

## 5. Why we build our own app under test

The required scenarios need controllable behavior that public demo sites don't offer:
- brute-force lockout, session expiry, forgot-password tokens;
- permission-based visibility, rate limiting, schema validation.

Task 3 also needs failures whose **true cause is known**, otherwise classifier accuracy can't be measured.

So we build **TestMu Lite**, a deliberately small test-management platform. It starts with one command and is reset to deterministic seed data. Record this reasoning in `docs/decisions.md`.

## 6. Target repository layout

This is the first commit.

```
testmu-sdet1-kartikey/
├── app/                      # TestMu Lite (app under test)
│   ├── main.py
│   ├── auth.py  dashboard.py  api.py  faults.py  seed.py
│   ├── templates/  static/
├── framework/                # reusable test framework
│   ├── config.py             # env-driven settings
│   ├── pages/                # page objects: login, forgot_password, dashboard
│   ├── components/           # dashboard widgets
│   ├── api_client.py
│   └── data/                 # test data builders
├── tests/
│   ├── conftest.py           # app server fixture, role contexts, api client
│   ├── ui/login/  ui/dashboard/
│   ├── api/
│   └── unit/                 # unit tests for ai/ code (fixtures allowed here only)
├── ai/
│   ├── llm_client.py         # one real HTTP client, provider via env
│   ├── testgen/              # Task 2: prompt runner, schema, validators, gherkin export
│   └── classifier/           # Task 3: collector plugin, payload builder, classifier, report
├── prompts/                  # raw prompt files, one per version, never edited after use
├── generated/
│   ├── raw/                  # verbatim LLM responses + metadata
│   └── login.json  dashboard.json  api.json  (accepted versions)
├── samples/                  # committed outputs from REAL runs (classifier, reports, eval)
├── reports/                  # gitignored run output
├── scripts/                  # generate_tests.py, build_prompts_md.py, eval_classifier.py
├── docs/                     # decisions.md, prompt-design.md, build-brief.md
├── .github/workflows/ci.yml
├── prompts.md
├── ai-usage-log.md
├── README.md
├── requirements.txt          # pinned
├── pytest.ini                # markers: smoke, ui, api, login, dashboard, case(id)
├── Makefile                  # setup, app, test, test-ui, test-api, generate, classify, eval
├── .env.example
└── .gitignore
```

---

## Phase 0 — Orient (no code)

1. Restate the plan in 15 lines or fewer, and list your assumptions.
2. Check the local environment: Python 3.11+, git, `gh` auth status, and whether Playwright browsers can be installed.
3. Ask Kartikey for:
   - his Groq API key setup, which goes into `.env` only (never paste it into chat history you commit);
   - confirmation of the repo name.
4. **STOP.**

## Phase 1 — Scaffold (Task 1)

1. Run `git init` and create the full layout from §6. Use empty modules with `__init__.py` and docstrings stating each module's purpose.
   - **No tests** and no app logic yet.
2. Add the config files:
   - `pytest.ini` with markers;
   - pinned `requirements.txt`;
   - `.gitignore` (covering `.env`, `reports/`, `__pycache__`, `test-results/`, `playwright-report/`);
   - `.env.example`;
   - `Makefile`.
3. Add stub docs:
   - `README.md` (title + "work in progress");
   - `ai-usage-log.md` (table header + first entry);
   - `docs/decisions.md` (stack and app-under-test decisions);
   - `docs/build-brief.md` (this brief).
4. Make the **first commit with exactly this message:**
   `chore: scaffold project structure — started with Claude Code (Anthropic), which proposed the folder layout, tooling and config files`
5. Ask Kartikey for confirmation **before** creating the public remote. Then run `gh repo create testmu-sdet1-kartikey --public --source . --push`.

## Phase 2 — App under test: TestMu Lite

Build the minimum needed to make every required scenario testable.
- Put stable `data-testid` attributes on every interactive or asserted element.
- All thresholds are configurable by env var.
- `TEST_MODE=1` enables test-only endpoints. These must be impossible to reach when it is off.

**Login**
- **Seed users:** `admin@testmu.local` (admin) and `viewer@testmu.local` (viewer). Test passwords live in seed config only.
- **Invalid credentials:** one generic error message for all cases (no user enumeration).
- **Lockout:** `LOCKOUT_THRESHOLD` (default 5) consecutive failures locks the account for `LOCKOUT_MINUTES` (default 15).
  - Show a distinct lockout message.
  - A successful login resets the counter.
- **Forgot password:** the response is identical whether or not the email exists.
  - Reset tokens are single-use with a 30-minute expiry.
  - Tokens are delivered to a test outbox: `GET /_test/outbox`, `TEST_MODE` only.
- **Session:** cookie session with `SESSION_TTL_SECONDS`, overridable for tests. An expired session redirects to `/login?reason=expired` and shows a message.

**Dashboard**
- **Widgets:** each loads through its own API endpoint and exposes `data-state` = `loading | loaded | error`.
  - Total test cases
  - Pass rate (latest run)
  - Recent runs table
  - Flaky tests (admin only)
  - Team activity (admin only)
- **Data accuracy:** widget values are computed from seeded SQLite data, so tests can assert UI value == API value == expected-from-seed.
- **Recent runs filters and sort:** filter by status and date range; sort by date and pass rate; state is reflected in URL query params.
- **Responsive layout:** grid on desktop; stacked on mobile; sidebar collapses to a menu below 768px.
- **Permissions:** admin-only widgets are absent for viewers, and their API endpoints return 403.

**REST API (`/api/v1`)**
- **Auth token:** `POST /auth/token` returns a JWT with expiry. Missing, malformed or expired tokens get 401; insufficient role gets 403.
- **CRUD on `test-cases`:**
  - list (paginated), get, create, update, delete;
  - 404 for unknown IDs, 409 for duplicate title, 422 for validation errors.
- **Errors:** one consistent error body, `{"error": {"code": str, "message": str}}`. A 500 is reachable via fault injection.
- **Rate limit:** `RATE_LIMIT_PER_MIN` per token returns 429 with a `Retry-After` header.
- **Schemas and health:** strict Pydantic response models; OpenAPI served at `/openapi.json`; `/health` endpoint.

**Fault injection** (`app/faults.py`)

Faults are set by env var or `POST /_test/faults` (TEST_MODE only). Each fault has a stable name and a documented ground-truth bucket.

| Bucket | Faults |
|---|---|
| `real_bug` | `BUG_PASS_RATE_OFF_BY_ONE`, `BUG_DELETE_NOT_PERSISTED`, `BUG_LOCKOUT_THRESHOLD_WRONG` |
| `environment_issue` | `ENV_WIDGET_API_503`, `ENV_DB_UNAVAILABLE`, `ENV_HEALTH_FAILING` |
| `flaky` | `FLAKY_WIDGET_LATENCY` (random delay exceeding the default timeout ~30% of the time), `FLAKY_UNSORTED_ORDER` (random row order when no sort is given) |

- Write the fault → bucket map to `app/faults.py` as the single source of truth.

**Done when:**
- `make app` serves the app, and a reset script restores the seed data;
- you've manually smoke-checked it with curl and one Playwright screenshot.

Commit.

## Phase 3 — Test framework

1. **Session fixture:** starts the app as a uvicorn subprocess on a free port with `TEST_MODE=1`, waits for `/health`, and tears it down at the end.
2. **Isolation:** reset the DB between tests where state leaks. Put role-based browser contexts (admin, viewer) in fixtures, with login cached via `storage_state`.
3. **Page objects and components:**
   - page objects: `LoginPage`, `ForgotPasswordPage`, `DashboardPage`;
   - widget components that expose `wait_loaded()` and `value()`.
4. **API client:** an `api_client` with a token fixture and response-schema validation helpers.
5. **Reporting:**
   - self-contained `pytest-html`;
   - on failure, attach screenshot + trace + console errors;
   - JUnit XML output.
6. **Hook for Task 3:** design the result-collection hook point now, but implement the collector in Phase 5.
7. **Smoke tests:** write **3 by hand, one per module**, to prove the framework works. They must be green.

Commit.

## Phase 4 — Task 2: Prompt engineering for test generation

**4a. Prompt design** (`docs/prompt-design.md`). All three module prompts share one template, with these sections in this order:

1. **ROLE** — senior QA engineer designing regression suites.
2. **CONTEXT** — the *actual* behavior spec of TestMu Lite for this module: thresholds, roles, endpoints, error format. Copy it from the code, not from memory.
3. **REQUIRED COVERAGE** — the assessment's scenario list for the module, word for word. Each item must get ≥1 positive and ≥1 negative or boundary case.
4. **TECHNIQUES** — equivalence partitioning, boundary values, state transitions, negative/security cases (e.g. enumeration, injection in inputs, token tampering).
5. **OUTPUT CONTRACT** — return JSON only, matching the inline JSON Schema; no prose.
6. **RULES**
   - IDs are `LOGIN-001`, `DASH-001`, `API-001`.
   - Each case is atomic and its expected results are deterministic and checkable.
   - Never invent features. If the spec is silent, add the item to `open_questions` instead of guessing.
7. **SELF-CHECK** — before answering, verify that every required coverage item maps to at least one case ID; list the mapping in `coverage_map`.

**Case schema fields:**
- `id`, `module`, `title`, `coverage_area` (enum = the required items), `type` (positive / negative / boundary / security / non_functional), `priority` (P0–P2)
- `preconditions[]`, `test_data{}`, `steps[]`, `expected_results[]`
- `automation_candidate` (bool), `notes`

**Top-level fields:** `cases[]`, `coverage_map{}`, `open_questions[]`.

**4b. CHECKPOINT — Kartikey edits the prompts.**
- Show the three v1 prompts and **STOP**.
- Kartikey edits them. What he approves is saved **byte-for-byte** as `prompts/login.v1.md`, `prompts/dashboard.v1.md`, `prompts/api.v1.md`.
- Log his edits in `ai-usage-log.md` only from what he tells you.

**4c. Runner** (`scripts/generate_tests.py`; `make generate MODULE=login VERSION=v1`)
- Sends the prompt file unchanged, with temperature 0.
- Saves the raw response verbatim to `generated/raw/<module>.<version>.<timestamp>.json`, with metadata: provider, model, temperature, timestamp, SHA-256 of the prompt file.
- Validates the response against the schema.
- Prints a validation report:
  - schema errors;
  - coverage matrix (required items vs. cases);
  - duplicate or near-duplicate titles;
  - cases with non-checkable expected results (e.g. "works correctly", "as expected").

**4d. Iterate on observed problems only.**
- Each revision is a **new file** (`v2`, `v3`). Never edit a prompt after it has been run.
- Each revision must fix a specific issue seen in the validation report or in review. Write down which issue.
- Stop when schema-valid, coverage complete, and reviewed by Kartikey. Aim for 3 versions or fewer per module.

**4e. Accepted output**
- Copy the accepted version to `generated/<module>.json`.
- Add a Gherkin export (`ai/testgen/to_gherkin.py` → `generated/gherkin/*.feature`).

**4f. Build `prompts.md` by script** (`scripts/build_prompts_md.py`), never by hand.
- For each module, include every version in order, copied byte-for-byte from `prompts/`, with model and settings.
- Under each module, add the **3–5 line note**: what didn't work first time and what changed. Draft it *only* from the recorded validation reports, then Kartikey confirms or rewrites it.
- Add a "How to re-run these prompts" section.
- Include the Task 3 classifier prompt versions in a separate, clearly labelled section.

**4g. Automate a subset**
- Implement the P0 `automation_candidate` cases as executable tests, roughly 8–12 per module.
- Link each test to its case with `@pytest.mark.case("LOGIN-003")`.
- Generate a traceability table (case ID → test node ID → status) into `docs/traceability.md`.
- All tests must pass against the clean app.

Commit after each sub-step.

## Phase 5 — Task 3: Flaky Test Classifier (Option B)

**Why B over A.** Draft this as the module docstring of `ai/classifier/__init__.py`, then flag it for **Kartikey to rewrite in his own words**. Points to cover:
- The ticket's pain is "fixing regression tests". Most of that time goes on triaging red runs: deciding what needs a human at all.
- B looks across the whole run and uses cross-attempt evidence (rerun outcomes, repeated vs. varying errors, app health). A per-failure explainer only ever sees one failure.
- B's output is a discrete label, so it can be **measured** against injected ground truth. A's free-text explanations are hard to score objectively.
- A's value is partly kept: each classification includes evidence and a suggested next action. The full Failure Explainer is listed as "next".

**5a. Collector** (`ai/classifier/collector.py`, a pytest plugin)

Records one JSON line per test **per attempt** to `reports/run-<id>/execution-log.jsonl`. Run with `--reruns 2`.

- **Per attempt:** nodeid, case ID, module, outcome, duration, attempt number.
- **Error details:** exception type, message, traceback trimmed to the last frames with a character cap, captured log lines.
- **API tests:** last request method, path, status, and a response body snippet.
- **UI tests:** page URL, console errors, failed network requests, screenshot path (the path is stored but the image is not sent).
- **App health:** `/health` result at failure time.
- **Run metadata:** git SHA, Python/browser versions, base URL, active faults (for evaluation only; **never sent to the LLM**).

**5b. Deterministic pre-signals** (computed in code, passed to the LLM as *hints*, not verdicts)
- `passed_on_rerun`
- `same_error_all_attempts`
- `error_category_heuristic`: timeout / connection / 5xx / assertion / other
- `health_ok_at_failure`
- duration spread across attempts

**5c. Classifier** (`ai/classifier/classify.py`; `make classify RUN=<id>`; also auto-runs at session end when `LLM_API_KEY` is set)

1. **Build a compact payload:**
   - failing tests only;
   - redact secrets;
   - truncate long fields;
   - chunk the request if it exceeds the model's context budget.
2. **Prompt** (versioned in `prompts/classifier.vN.md`):
   - precise definitions of the three buckets;
   - decision rules, e.g.:
     - consistent assertion mismatch with healthy app → `real_bug`;
     - connection errors, 5xx from dependencies, or failed health check → `environment_issue`;
     - passes on rerun or intermittent timing errors with healthy app → `flaky`;
   - tie-break guidance;
   - JSON-only output contract.
3. **Output schema** (Pydantic):
   - `run_summary { total, failed, by_bucket }`
   - `classifications[] { test_id, case_id, bucket: real_bug|environment_issue|flaky, confidence: 0–1, evidence[] (must cite fields from the payload), reasoning (≤3 sentences), suggested_next_action }`
4. **Reliability:**
   - validate the response; on invalid JSON, retry **once** with the validation error included;
   - if it still fails, mark those tests `unclassified`. Never guess;
   - on 429, use exponential backoff and honor `Retry-After`.
5. **No API key:** exit with a clear message. Never write placeholder output.
6. **Outputs:**
   - `classification.json`;
   - `classification.md` (tables grouped by bucket);
   - an **injected section in the pytest-html report**: run-level summary plus per-test extras showing bucket, confidence and reasoning. This is the "LLM response inside your test results" deliverable.

**5d. Unit tests** (`tests/unit/`) for the payload builder, redaction, chunking, response parsing and retry logic. Fixtures allowed here, clearly labelled.

**5e. Evaluation** (`scripts/eval_classifier.py`; `make eval`)
1. Run the suite under these scenarios: clean, each fault group alone, and one mixed scenario.
2. Map each failure's ground truth from `app/faults.py`.
3. Run the real classifier.
4. Write a confusion matrix, accuracy, and a per-misclassification table (with the model's reasoning) to `samples/eval/`.
5. Report the numbers honestly, including failures and their likely causes.
6. Keep total LLM calls within free-tier limits; space runs out if needed.

**5f. Samples:** commit real outputs from one mixed-fault run to `samples/`:
- `classification.json`, `classification.md`, the pytest-html report;
- a screenshot of the report section;
- all stamped with model name and timestamp.

Commit.

## Phase 6 — CI

`.github/workflows/ci.yml` on `ubuntu-latest`.

**Main job** (push / PR):
- install dependencies;
- `playwright install --with-deps chromium`;
- `ruff`;
- unit → API → UI tests against the clean app;
- upload reports as artifacts.
- This job must be **green and must not require any secret**.

**`fault-demo` job** (`workflow_dispatch` only):
- runs with a mixed fault set and `--reruns 2`;
- runs the classifier if the `LLM_API_KEY` secret exists, otherwise skips with a notice;
- uploads the classified report.

Add a badge to the README. Publishing the latest report to GitHub Pages is optional.

Commit.

## Phase 7 — Docs, final verification, submission

1. **`README.md`**
   - One-paragraph summary tied to the ticket.
   - Mermaid architecture diagram.
   - Quickstart in 5 commands or fewer, including how to get a free Groq key and fill `.env`.
   - How to run each task.
   - Results: case counts per module, automated count, classifier eval numbers. **Measured values only.**
   - Key decisions (link `docs/decisions.md`).
   - Known limitations.
   - **"What I'd build next"**, for example:
     - Option A Failure Explainer reusing the collector;
     - flakiness history across runs (same-commit divergence + rolling flip rate);
     - locator-repair suggestions delivered as PRs, never auto-applied;
     - retrieval of past classifications as few-shot context;
     - prompt regression tests;
     - cost/latency tracking per LLM call.
2. **`ai-usage-log.md`** must be complete:
   - **Claude (chat):** authored this build brief.
   - **Claude Code:** every phase.
   - **The runtime LLM** (provider + model): Task 2 generation and Task 3 classification.
   - Kartikey's fields are left for him to fill.
3. **Fresh-clone check:** clone the public repo into a temp directory, follow the README exactly, and confirm everything works. Fix any gap.
4. **Final checklist:** print the requirement checklist from §2 with ✅/❌ and the file path proving each item. Confirm the repo is public.

Then **STOP** and hand over to Kartikey for his final read-through and submission.
