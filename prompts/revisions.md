# Prompt revisions

Every prompt version after v1 fixes specific problems seen in the previous version's
validation report (`generated/raw/<module>.<version>.<timestamp>.report.md`) or in review of
its cases. Prompt files are never edited after they have been run.

## v2 (all modules), from the v1 runs on 2026-10-22

Reports: `login.v1.20261022T185659Z`, `dashboard.v1.20261022T185814Z`,
`api.v1.20261022T185931Z`.

Common to all three prompts:

| Change | Problem it fixes |
|---|---|
| Rule 3: expected results must be observable through the page, HTTP response or a test hook; no internal state, no "X or Y" | Review: LOGIN-017 expected "failure counter is reset to 0"; DASH-008 expected "attribute or style indicating full-width" |
| New rule 11: copy strings character for character, ASCII hyphens and quotes | Report: U+2011 (non-breaking hyphen) inside exact strings in LOGIN-002/015/016/018, DASH-008, API-001/005 |
| New rule 12: list items are non-empty plain strings, never objects | Report: API v1 had 24 schema errors: preconditions returned as `{"0": "..."}` and one empty expected result |
| REQUIRED COVERAGE now says what counts as `positive` in each area | Report: no positive case for "invalid credentials" (Login), "error handling (4xx/5xx)" and "schema validation" (API) |

Login only:

| Change | Problem it fixes |
|---|---|
| The reset redirect is stated as HTTP 303 | Model's open question ("What HTTP status code is used for the successful password-reset redirect?") and LOGIN-008 expecting 302 |

Dashboard only:

| Change | Problem it fixes |
|---|---|
| `widget-error` shows the error body's `message`, not its `code` | Review: DASH-002 and DASH-014 expected the code text in `widget-error` |
| A 401 on a widget request navigates to `/login?reason=expired` | Review: DASH-002 invented an error-state behaviour for a missing session |
| `loading` is only observable by holding the request back | Review: DASH-012 asserted the transient `loading` state right after navigation (a race) |
| Layout described in checkable terms (same row, full width, `aria-expanded` values) | Review: DASH-008's layout expectations could not be checked |

API only:

| Change | Problem it fixes |
|---|---|
| CRUD must include list (paging) and get by id | Review: v1 had no read cases |
| Error handling needs at least one 5xx case via the database fault hook | Review: v1 had no 5xx case, although the hook is documented in CONTEXT |
| "Schema validation" means response shapes; request validation (422) belongs to error handling | Review: v1's schema-validation cases were all request-body 422s |

## v3 (all modules), from the v2 runs on 2026-10-22

Reports: `login.v2.20261022T190838Z`, `dashboard.v2.20261022T190923Z`,
`api.v2.20261022T191239Z`.

Common to all three prompts:

| Change | Problem it fixes |
|---|---|
| Case types (`positive`, `boundary`, `negative`, `security`) defined; case/whitespace variants are `boundary` | Report: 'valid login' had no negative/boundary case because LOGIN-002 (case and whitespace variant) was labelled positive |
| New rule 13: assert exact message text only when CONTEXT gives it word for word | Review: invented messages in API-002 ("Missing token"), API-015 ("email"), DASH-002 ("Internal error") |
| SELF-CHECK: IDs run from 001 with no gaps | Report: Dashboard IDs skipped DASH-010 |

Dashboard only:

| Change | Problem it fixes |
|---|---|
| The pass-rate widget always shows the latest run; no control to choose another | Review: DASH-005 expected the widget to show run 2026-09-11 |
| No hook makes a widget fail server-side; error state comes from an invalid filter or browser-side interception | Review: DASH-002 assumed a server failure the prompt gives no way to trigger |

API only:

| Change | Problem it fixes |
|---|---|
| Table of exact error messages per code, copied from `app/api.py` | Review: API-002 and API-015 invented message texts |
| Error handling must include 404, 405, 422 and 500 cases | Review: v2 error handling had only the 500 case; v1's 4xx cases disappeared |
