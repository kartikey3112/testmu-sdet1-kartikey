# REST API — regression test case generation (prompt v2)

## ROLE
You are a senior QA engineer designing a regression suite for the REST API module of a web
application. You write test cases that another engineer can automate without asking you
anything.

## CONTEXT
The application is TestMu Lite, a small test-management web app. Everything below is the
complete, authoritative behaviour of its REST API.

General:
- Base path `/api/v1`. JSON in and out.
- Every error uses exactly this body: `{"error": {"code": "<code>", "message": "<text>"}}`.
- Response bodies are strict: they contain exactly the documented fields and nothing else.
- The OpenAPI document is served at `/openapi.json`.
- `GET /health` -> 200 `{"status": "ok", "checks": {"database": "ok"}}`.
- Unknown route -> 404 `not_found`. Wrong HTTP method -> 405 `method_not_allowed`.
- Malformed JSON, missing required fields, wrong types, unknown fields, or out-of-range values
  -> 422 `validation_error` (the message names the offending field).

Auth:
- `POST /api/v1/auth/token` with `{"email": str, "password": str}`. The email is trimmed and
  lower-cased.
  - Success: 200 `{"access_token": str, "token_type": "bearer", "expires_in": 3600,
    "expires_at": "<ISO 8601 date-time>"}`.
  - Wrong credentials: 401 `invalid_credentials`.
  - Locked account: 423 `account_locked`. The lockout is shared with the web sign-in: 5
    consecutive failures lock the account for 15 minutes.
- The token is a JWT (HS256) with claims `sub`, `email`, `role`, `iat`, `exp`. It lives for
  TOKEN_TTL_SECONDS = 3600.
- Send it as `Authorization: Bearer <token>`.
  - No header: 401 `missing_token`.
  - Any other scheme, or an empty token: 401 `invalid_token`.
  - Malformed token or bad signature: 401 `invalid_token`.
  - Expired token: 401 `token_expired`.
  - Valid token, role not allowed: 403 `forbidden`.
- Seed users: `admin@testmu.local` (role `admin`, password `{{admin_password}}`) and
  `viewer@testmu.local` (role `viewer`, password `{{viewer_password}}`).

Test cases resource:
- Fields: `id` (int), `title` (str), `module` (`login` | `dashboard` | `api`), `priority`
  (`P0` | `P1` | `P2`), `description` (str), `created_at` and `updated_at` (ISO 8601
  date-time).
- `GET /api/v1/test-cases?page=&page_size=` (admin or viewer):
  - 200 `{"items": [...], "page": int, "page_size": int, "total": int}`, ordered by `id`.
  - `page` >= 1 (default 1); `page_size` 1-100 (default 20).
  - A page past the end returns 200 with empty `items`.
- `GET /api/v1/test-cases/{id}` (admin or viewer): 200 with the object. Unknown id -> 404
  `not_found`. Non-integer id -> 422.
- `POST /api/v1/test-cases` (admin only): body `title` (required, at most 200 characters,
  trimmed, must not be blank), `module` (required), `priority` (required), `description`
  (optional, at most 2000 characters, default "").
  - Success: 201 with the full object.
  - Title already used, compared case-insensitively: 409 `duplicate_title`.
- `PATCH /api/v1/test-cases/{id}` (admin only): any subset of the same fields, same rules.
  - Fields that are missing or null are left unchanged; `updated_at` changes when something
    changes.
  - Unknown id: 404. Title clashing with a different case: 409 `duplicate_title`.
- `DELETE /api/v1/test-cases/{id}` (admin only): 204 with an empty body; afterwards GET
  returns 404. Unknown id: 404.
- A viewer calling POST, PATCH or DELETE: 403 `forbidden`.
- Seed data: 24 test cases with ids 1-24.

Rate limiting:
- RATE_LIMIT_PER_MIN = 60 requests per token per fixed calendar minute.
- Request 61 within the same minute: 429 `rate_limited` with a `Retry-After` header (whole
  seconds until the minute ends, at least 1).
- Each token has its own limit. `POST /auth/token` is not rate limited.

Server errors:
- An unexpected server error returns 500 `internal_error` with message
  "Internal server error". No stack trace or internal detail is exposed.

Test hooks (available to every test):
- `POST /_test/reset` restores seed data and clears rate-limit counters.
- `POST /_test/clock` with `{"advance_seconds": N}` moves the application clock forward. Token
  expiry and the rate-limit window follow it.
- `POST /_test/faults` with `{"faults": ["ENV_DB_UNAVAILABLE"]}` makes every database access
  fail. Requests that need the database then return 500 `internal_error`, and `/health`
  returns 503 `{"status": "fail", "checks": {"database": "fail"}}`. `POST /_test/reset` turns it
  off.

## REQUIRED COVERAGE
Cover every one of these areas. Use them, spelled exactly like this, as `coverage_area` values:
- auth token validation
- CRUD operations
- error handling (4xx/5xx)
- rate limiting
- schema validation

Each area needs at least one `positive` case and at least one `negative`, `boundary` or
`security` case. What each area means here, and what counts as `positive`:
- auth token validation: tokens are issued and checked. Positive: a valid token is accepted.
- CRUD operations: create, read (list with paging, and get by id), update and delete must
  all be covered. Positive: an allowed operation succeeds and its effect is visible through
  the API.
- error handling (4xx/5xx): include 4xx cases for bad input and at least one 5xx case using
  the database fault hook. Positive: after the cause is removed (input corrected, or the
  fault turned off with the reset hook), the same request succeeds.
- rate limiting: positive: requests within the limit succeed.
- schema validation: this means the API's *responses* match the documented shapes exactly:
  every documented field present with the documented type, and no other fields. Validation
  of request bodies (422) belongs to error handling. Positive: a success response (token,
  test case, list page) matches its documented shape.

## TECHNIQUES
Apply these where they fit the behaviour above:
- Equivalence partitioning: one case per class of input that the app treats differently.
- Boundary values: test just below, at and just above every number in CONTEXT (thresholds,
  lengths, limits, expiry times).
- State transitions: check what changes after a sequence of actions (lock, unlock, expire,
  reuse, delete).
- Negative and security cases: account enumeration, injection-like input (SQL or script
  strings) treated as plain data, token tampering, and access with the wrong role.

## OUTPUT CONTRACT
Respond with one JSON object and nothing else: no Markdown fences, no prose before or after.
It must validate against this JSON Schema:

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "cases",
    "coverage_map",
    "open_questions"
  ],
  "properties": {
    "cases": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "id",
          "module",
          "title",
          "coverage_area",
          "type",
          "priority",
          "preconditions",
          "test_data",
          "steps",
          "expected_results",
          "automation_candidate",
          "notes"
        ],
        "properties": {
          "id": {
            "type": "string",
            "pattern": "^API-\\d{3}$"
          },
          "module": {
            "const": "api"
          },
          "title": {
            "type": "string",
            "minLength": 10,
            "maxLength": 120
          },
          "coverage_area": {
            "enum": [
              "auth token validation",
              "CRUD operations",
              "error handling (4xx/5xx)",
              "rate limiting",
              "schema validation"
            ]
          },
          "type": {
            "enum": [
              "positive",
              "negative",
              "boundary",
              "security",
              "non_functional"
            ]
          },
          "priority": {
            "enum": [
              "P0",
              "P1",
              "P2"
            ]
          },
          "preconditions": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "test_data": {
            "type": "object"
          },
          "steps": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "minItems": 1
          },
          "expected_results": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            },
            "minItems": 1
          },
          "automation_candidate": {
            "type": "boolean"
          },
          "notes": {
            "type": "string"
          }
        }
      }
    },
    "coverage_map": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "auth token validation",
        "CRUD operations",
        "error handling (4xx/5xx)",
        "rate limiting",
        "schema validation"
      ],
      "properties": {
        "auth token validation": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^API-\\d{3}$"
          }
        },
        "CRUD operations": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^API-\\d{3}$"
          }
        },
        "error handling (4xx/5xx)": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^API-\\d{3}$"
          }
        },
        "rate limiting": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^API-\\d{3}$"
          }
        },
        "schema validation": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^API-\\d{3}$"
          }
        }
      }
    },
    "open_questions": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  }
}

## RULES
1. IDs are `API-001`, `API-002`, ... in order, with no gaps or duplicates.
2. One behaviour per case. Do not combine several checks that could fail independently.
3. Every expected result must be deterministic and checkable: an exact message, HTTP status,
   error code, URL, element state, attribute or number taken from CONTEXT. Never write vague
   results such as "works correctly", "as expected", "appropriate error" or "properly".
   Each expected result must be observable through the interfaces in CONTEXT (the page, the
   HTTP response, or a test hook). Never expect internal state such as counters or database
   rows, and never offer alternatives ("X or Y").
4. Use only the behaviour described in CONTEXT. Never invent features, fields, messages or
   endpoints. If you think something should be tested but CONTEXT does not say how the app
   behaves, add it to `open_questions` as a question and do not write a case for it.
5. Put concrete values in `test_data`. Refer to passwords only as `{{admin_password}}` and
   `{{viewer_password}}`.
6. Use the test hooks in CONTEXT instead of waiting in real time.
7. `priority`: P0 for the main path and for security, P1 for important variations, P2 for
   rare edge cases.
8. Set `automation_candidate` to true when the case can run deterministically through the
   interfaces in CONTEXT.
9. Use `notes` for anything an automation engineer must know; use "" if there is nothing.
10. Write between 15 and 25 cases.
11. Copy messages, error codes, URLs and `data-testid`s from CONTEXT character for character.
    Use plain ASCII: "-" for hyphens and straight quotes, never typographic variants.
12. Every item in `preconditions`, `steps` and `expected_results` is a non-empty plain string,
    never an object.

## SELF-CHECK
Before you answer, check that:
- every required coverage area has at least one positive case and at least one negative,
  boundary or security case;
- `coverage_map` lists, for each area, the IDs of every case with that `coverage_area`, and
  every ID in it exists in `cases`;
- no two cases test the same thing;
- no expected result uses a vague phrase;
- the output is a single JSON object matching the schema.
