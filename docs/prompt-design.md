# Prompt design: test case generation (Task 2)

## Goal

Prompts that reviewers can re-run and get comparable output: the same structure, the same
schema, and expected results that can be checked automatically. All three module prompts
share one template. Only CONTEXT, REQUIRED COVERAGE and the ID prefix change.

## Template (sections in this order)

| Section | What it does | Why |
|---|---|---|
| ROLE | Senior QA engineer designing a regression suite | Sets the level of detail and the audience (an automation engineer) |
| CONTEXT | The app's actual behaviour for the module: thresholds, exact messages, status and error codes, `data-testid`s, endpoints, seed data, test hooks | Written from the code (`app/`), so the model doesn't guess. Exact strings make expected results checkable |
| REQUIRED COVERAGE | The assessment's scenario list, word for word; each must get one positive and one negative/boundary/security case | These strings are the `coverage_area` enum, so coverage can be checked by machine |
| TECHNIQUES | Equivalence partitioning, boundary values, state transitions, negative/security | Asks for the case design methods a reviewer expects, tied to numbers in CONTEXT |
| OUTPUT CONTRACT | JSON only, with the JSON Schema inline | One parseable shape; the same schema object is used by the validator |
| RULES | ID format, atomic cases, checkable results, no invented features (`open_questions` instead), placeholders for passwords, test hooks instead of waiting, priority meaning, case count | Each rule targets a known failure mode of generated test cases |
| SELF-CHECK | Coverage mapping, no duplicates, no vague phrases, valid JSON | Makes the model review its own answer against the same checks the validator runs |

## Case schema

Defined once in `ai/testgen/schema.py` and pasted into each prompt.

- **Per case:** `id`, `module`, `title`, `coverage_area` (enum = required items), `type`
  (positive / negative / boundary / security / non_functional), `priority` (P0–P2),
  `preconditions[]`, `test_data{}`, `steps[]`, `expected_results[]`,
  `automation_candidate`, `notes`.
- **Top level:** `cases[]`, `coverage_map{}` (every required area → case IDs),
  `open_questions[]`.
- `additionalProperties: false` everywhere, so extra or misspelled fields are caught.

## Decisions

- **CONTEXT is copied from the code, not summarised from the brief.** I probed edge cases
  against the running app before writing it: empty login fields, non-integer IDs, malformed
  JSON, wrong auth scheme, paging past the end, title length 200 vs 201, PATCH with nulls.
- **Fault-injection names are left out**, except `ENV_DB_UNAVAILABLE` in the API prompt.
  That one is the documented way to reach a 500, which "error handling (4xx/5xx)" needs.
  The other faults exist for the Task 3 classifier evaluation and are not app behaviour.
- **Passwords are placeholders** (`{{admin_password}}`), so generated cases don't hard-code
  credentials. The automation layer fills them from `app/seed.py`.
- **Test hooks are described** (reset, clock, outbox), so expiry and reset-link cases come
  out deterministic instead of "wait 30 minutes".
- **15–25 cases per module.** Enough for two or more cases per coverage area, small enough
  to stay well within free-tier output limits and to review by hand.

## Versioning

- What Kartikey approves is saved byte-for-byte as `prompts/<module>.v1.md`.
- A prompt file is never edited after it has been run.
- Each revision is a new file (`v2`, `v3`) that fixes a specific problem seen in the
  validation report or in review. The problem is written down with the revision.
