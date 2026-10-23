# Submission checklist

Every requirement from the assessment (build brief §2), with the file that proves it.
✅ done and verified

## Task 1: setup and scaffold

| Requirement | Status | Proof |
|---|---|---|
| Public GitHub repo named `testmu-sdet1-kartikey` | ✅ | https://github.com/kartikey3112/testmu-sdet1-kartikey (GitHub API: `private: false`, checked 2026-10-23) |
| Playwright + Python | ✅ | `requirements.txt`, `framework/`, `tests/ui/` |
| Folder structure set up before any test | ✅ | first commit `54b14a9` contains docstring-only modules and no test files |
| First commit names the AI tool and what it helped with | ✅ | `54b14a9`: "chore: scaffold project structure — started with Claude Code (Anthropic), which proposed the folder layout, tooling and config files" |

## Task 2: prompt engineering for test generation

| Requirement | Status | Proof |
|---|---|---|
| LLM-generated cases for Login (valid login, invalid credentials, forgot password, session expiry, brute-force lockout) | ✅ | `generated/login.json` (15 cases, coverage map complete) |
| … for Dashboard (widget loading, data accuracy, filter/sort, responsive layout, permission-based visibility) | ✅ | `generated/dashboard.json` (16 cases) |
| … for REST API (auth token validation, CRUD, 4xx/5xx, rate limiting, schema validation) | ✅ | `generated/api.json` (24 cases) |
| `prompts.md` with every prompt exactly as written | ✅ | `prompts.md`, built from `prompts/` byte-for-byte; `--check` runs in CI |
| Generated test cases submitted (JSON + Gherkin) | ✅ | `generated/*.json`, `generated/gherkin/*.feature`, raw responses in `generated/raw/` |
| 3–5 line note per module on what didn't work first time | ✅ | `prompts.md` → each module's "What didn't work the first time" (source: `prompts/notes.md`) |
| Prompts consistent, structured, reproducible | ✅ | one template (`docs/prompt-design.md`), settings and re-run steps in `prompts.md` |

## Task 3: LLM integration (Option B, Flaky Test Classifier)

| Requirement | Status | Proof |
|---|---|---|
| Feed execution logs to an LLM after a run | ✅ | `ai/classifier/collector.py` → `execution-log.jsonl` → `ai/classifier/classify.py` |
| Exactly three buckets: real bug, environment issue, flaky | ✅ | `ai/classifier/classify.py` (`Bucket`), `prompts/classifier.v1.md` |
| Structured report | ✅ | `classification.json` / `classification.md` per run |
| Real LLM call, not mocked | ✅ | `ai/llm_client.py`; real classifications in `samples/eval/` (53/55 correct on known-cause faults) |
| Working code | ✅ | CI green; 52 unit tests for payload, redaction, chunking, validation, retry, quota, provider errors |
| Sample output with the LLM response inside the test results | ✅ | `samples/eval-20261022T200611Z-mixed/report.html` (LLM summary, "LLM bucket" column, per-test block) + `report-llm-summary.png`, `report-test-classification.png` |
| Code comment: why Option B over Option A | ✅ | `ai/classifier/__init__.py` (module docstring) |

## Submission contents

| Item | Status | Proof |
|---|---|---|
| `prompts.md` | ✅ | `prompts.md` |
| Generated test cases | ✅ | `generated/` |
| LLM integration code and sample output | ✅ | code: `ai/`; sample: `samples/eval-20261022T200611Z-mixed/`; evaluation: `samples/eval/` |
| `README.md`: how to run it and what to build next | ✅ | `README.md` ("How to run each part", "Results (measured)", "What I'd build next") |
| `ai-usage-log.md`: every AI tool, task, output | ✅ | `ai-usage-log.md` (Kartikey's own fields marked `<!-- Kartikey to fill -->` where not yet filled) |

## Verification done in Phase 7

- Fresh clone of the public repo into an empty folder, README quickstart followed exactly, no
  API key: 83/83 tests passed, ruff clean, `prompts.md` check passed (2026-10-23). Chromium
  was already in the local Playwright cache; CI on `ubuntu-latest` covers a clean machine.
- All relative links in `README.md` resolve.
