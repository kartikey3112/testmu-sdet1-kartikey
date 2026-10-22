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
