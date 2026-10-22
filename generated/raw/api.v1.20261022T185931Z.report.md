# Validation report: api.v1.20261022T185931Z

**Result: FAIL**

- Cases: 18 (expected 15–25)
- Automation candidates: 18
- Open questions: 0

## Coverage matrix

| Required area | Cases | Positive | Negative / boundary / security |
|---|---|---|---|
| auth token validation | API-001, API-002, API-003, API-004 | 1 | 3 |
| CRUD operations | API-005, API-006, API-007, API-008, API-009, API-010 | 3 | 3 |
| error handling (4xx/5xx) | API-011, API-012, API-013 | 0 | 3 |
| rate limiting | API-014, API-015 | 1 | 1 |
| schema validation | API-016, API-017, API-018 | 0 | 3 |

## Schema errors

- cases/0/expected_results/3: '' should be non-empty
- cases/1/preconditions/0: {'0': 'Obtain a valid admin token (optional)'} is not of type 'string'
- cases/2/preconditions/0: {'0': 'Obtain a valid admin token'} is not of type 'string'
- cases/3/preconditions/0: {'0': 'Obtain a valid admin token'} is not of type 'string'
- cases/4/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/5/preconditions/0: {'0': 'Obtain viewer JWT token'} is not of type 'string'
- cases/6/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/6/preconditions/1: {'0': 'Existing test case with title "Login flow test"'} is not of type 'string'
- cases/7/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/7/preconditions/1: {'0': 'Test case with id 1 exists'} is not of type 'string'
- cases/8/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/8/preconditions/1: {'0': 'Test case id 2 title "Dashboard overview"'} is not of type 'string'
- cases/8/preconditions/2: {'0': 'Test case id 3 exists'} is not of type 'string'
- cases/9/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/9/preconditions/1: {'0': 'Test case with id 24 exists'} is not of type 'string'
- cases/10/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/11/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/12/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/13/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/14/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/15/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/16/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'
- cases/17/preconditions/0: {'0': 'Obtain admin JWT token'} is not of type 'string'

## Coverage gaps

- 'error handling (4xx/5xx)' has no positive case
- 'schema validation' has no positive case

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

- API-001: U+2011
- API-005: U+2011

## Open questions from the model

None.
