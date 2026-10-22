# Validation report: login.v1.20261022T185659Z

**Result: FAIL**

- Cases: 18 (expected 15–25)
- Automation candidates: 18
- Open questions: 1

## Coverage matrix

| Required area | Cases | Positive | Negative / boundary / security |
|---|---|---|---|
| valid login | LOGIN-001, LOGIN-002 | 1 | 1 |
| invalid credentials | LOGIN-003, LOGIN-004, LOGIN-005 | 0 | 3 |
| forgot password | LOGIN-006, LOGIN-007, LOGIN-008, LOGIN-009, LOGIN-010, LOGIN-011 | 2 | 4 |
| session expiry | LOGIN-012, LOGIN-013, LOGIN-014 | 1 | 2 |
| brute-force lockout | LOGIN-015, LOGIN-016, LOGIN-017, LOGIN-018 | 1 | 3 |

## Schema errors

None.

## Coverage gaps

- 'invalid credentials' has no positive case

## coverage_map mismatches

None.

## ID issues

None.

## Duplicate or near-duplicate titles

None.

## Non-checkable expected results

None.

## Hard-coded credentials

None.

## Typographic characters in exact strings

- LOGIN-002: U+2011
- LOGIN-015: U+2011
- LOGIN-016: U+2011
- LOGIN-018: U+2011

## Open questions from the model

- What HTTP status code is used for the successful password‑reset redirect to /login?reason=reset?
