# Validation report: api.v3.20261022T192144Z

**Result: FAIL**

- Cases: 17 (expected 15–25)
- Automation candidates: 17
- Open questions: 0

## Coverage matrix

| Required area | Cases | Positive | Negative / boundary / security |
|---|---|---|---|
| auth token validation | API-001, API-002, API-003, API-004, API-018 | 1 | 4 |
| CRUD operations | API-005, API-006, API-007, API-008, API-009 | 3 | 2 |
| error handling (4xx/5xx) | API-010, API-011, API-012, API-013 | 0 | 4 |
| rate limiting | API-014, API-015 | 1 | 1 |
| schema validation | API-016 | 1 | 0 |

## Schema errors

None.

## Coverage gaps

- 'error handling (4xx/5xx)' has no positive case
- 'schema validation' has no negative/boundary/security case

## coverage_map mismatches

None.

## ID issues

- ids are not sequential from 001: ['API-001', 'API-002', 'API-003', 'API-004', 'API-005', 'API-006', 'API-007', 'API-008', 'API-009', 'API-010', 'API-011', 'API-012', 'API-013', 'API-014', 'API-015', 'API-016', 'API-018']

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
