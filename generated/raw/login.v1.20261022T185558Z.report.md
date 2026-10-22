# Validation report: login.v1.20261022T185558Z

**Result: FAIL**

- **Truncated:** output hit the token limit (finish_reason=length)

- Cases: 6 (expected 15–25) ← out of range
- Automation candidates: 5
- Open questions: 0

## Coverage matrix

| Required area | Cases | Positive | Negative / boundary / security |
|---|---|---|---|
| valid login | LOGIN-001, LOGIN-002 | 2 | 0 |
| invalid credentials | LOGIN-003, LOGIN-004, LOGIN-005 | 0 | 3 |
| forgot password | LOGIN-006 | 1 | 0 |
| session expiry | — | 0 | 0 |
| brute-force lockout | — | 0 | 0 |

## Schema errors

- <root>: 'coverage_map' is a required property
- <root>: 'open_questions' is a required property
- cases/5: 'steps' is a required property
- cases/5: 'expected_results' is a required property
- cases/5: 'automation_candidate' is a required property
- cases/5: 'notes' is a required property

## Coverage gaps

- 'valid login' has no negative/boundary/security case
- 'invalid credentials' has no positive case
- 'forgot password' has no negative/boundary/security case
- 'session expiry' has no positive case
- 'session expiry' has no negative/boundary/security case
- 'brute-force lockout' has no positive case
- 'brute-force lockout' has no negative/boundary/security case

## coverage_map mismatches

None.

## ID issues

None.

## Duplicate or near-duplicate titles

- LOGIN-001 / LOGIN-002: near-duplicate (0.91)

## Non-checkable expected results

None.

## Hard-coded credentials

None.

## Typographic characters in exact strings

None.

## Open questions from the model

None.
