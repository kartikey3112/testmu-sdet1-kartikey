# Validation report: login.v2.20261022T190838Z

**Result: FAIL**

- Cases: 17 (expected 15–25)
- Automation candidates: 17
- Open questions: 0

## Coverage matrix

| Required area | Cases | Positive | Negative / boundary / security |
|---|---|---|---|
| valid login | LOGIN-001, LOGIN-002 | 2 | 0 |
| invalid credentials | LOGIN-003, LOGIN-004, LOGIN-016, LOGIN-017 | 1 | 3 |
| forgot password | LOGIN-005, LOGIN-006, LOGIN-007, LOGIN-008 | 1 | 3 |
| session expiry | LOGIN-009, LOGIN-010, LOGIN-011 | 1 | 2 |
| brute-force lockout | LOGIN-012, LOGIN-013, LOGIN-014, LOGIN-015 | 2 | 2 |

## Schema errors

None.

## Coverage gaps

- 'valid login' has no negative/boundary/security case

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

None.

## Open questions from the model

None.
