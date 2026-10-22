<!--
Per-module notes for prompts.md: what didn't work the first time and what changed.
Drafted from the saved validation reports (generated/raw/*.report.md) and prompts/revisions.md.
status: DRAFT - Kartikey to confirm or rewrite
-->

## login

- v1: the first run was cut off at 3,072 tokens (gpt-oss spends part of its output on hidden reasoning), so the runner now sets `max_completion_tokens`. The re-run had no positive "invalid credentials" case, a non-breaking hyphen inside the exact lockout message, a 302 instead of 303 after reset, and an expected result nothing exposes (a failure counter).
- v2: defined "positive" per area, required plain-ASCII exact strings and stated the 303. The coverage gap moved to "valid login".
- v3: defined the case types. The gap moved to "session expiry", and LOGIN-009 got the reset-link expiry boundary wrong.
- v4: stated which side of each expiry boundary wins and made the self-check count cases per area. Coverage complete; non-breaking hyphens remain only in descriptive text, not in quoted messages.

## dashboard

- v1: all areas covered, but review found `widget-error` expected to show the error code instead of the message, invented behaviour for a missing session, an uncheckable layout result ("attribute or style indicating full-width") and a race on the `loading` state.
- v2: described those behaviours exactly, but new mistakes appeared: the pass-rate widget expected to show an older run, a server-side widget failure assumed with no way to trigger it, and DASH-010 skipped.
- v3: stated that the widget always shows the latest run and how a widget can be put into the error state. Passed validation; DASH-008 still expects the error code, and DASH-010 is filed under filter/sort.

## api

- v1: 24 schema errors (preconditions as `{"0": ...}` objects), no positive case for error handling or schema validation, no 5xx or read cases, and "schema validation" treated as request validation.
- v2: structure and scope fixed, but error message texts were invented (e.g. "Missing token") and the 404/405/422 cases disappeared.
- v3: added a table of exact error messages and required 404, 405, 422 and 500 cases. Messages became exact, but the recovery after the 500 was labelled negative and schema validation had one case.
- v4: made recovery its own positive case and defined negative schema checks. Passed validation with 24 cases.
