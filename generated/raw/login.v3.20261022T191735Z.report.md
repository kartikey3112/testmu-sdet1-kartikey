# Validation report: login.v3.20261022T191735Z

**Result: FAIL**

- Cases: 18 (expected 15–25)
- Automation candidates: 18
- Open questions: 0

## Coverage matrix

| Required area | Cases | Positive | Negative / boundary / security |
|---|---|---|---|
| valid login | LOGIN-001, LOGIN-002, LOGIN-003 | 2 | 1 |
| invalid credentials | LOGIN-004, LOGIN-005, LOGIN-006, LOGIN-007 | 1 | 3 |
| forgot password | LOGIN-008, LOGIN-009, LOGIN-010, LOGIN-011, LOGIN-012 | 1 | 4 |
| session expiry | LOGIN-013, LOGIN-014 | 0 | 2 |
| brute-force lockout | LOGIN-015, LOGIN-016, LOGIN-017, LOGIN-018 | 1 | 3 |

## Schema errors

None.

## Coverage gaps

- 'session expiry' has no positive case

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
