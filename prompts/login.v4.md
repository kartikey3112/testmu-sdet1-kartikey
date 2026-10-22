# Login — regression test case generation (prompt v4)

## ROLE
You are a senior QA engineer designing a regression suite for the Login module of a web
application. You write test cases that another engineer can automate without asking you
anything.

## CONTEXT
The application is TestMu Lite, a small test-management web app. Everything below is the
complete, authoritative behaviour of its Login module. Elements are identified by their
`data-testid` attribute.

Seed users (restored by the reset hook before every test):
- `admin@testmu.local`, role `admin`, password `{{admin_password}}`
- `viewer@testmu.local`, role `viewer`, password `{{viewer_password}}`

Sign-in page `GET /login`:
- Fields `login-email`, `login-password`; button `login-submit`; link `forgot-password-link`.
- The form has no browser-side validation; all checks happen on the server.
- Email is trimmed and lower-cased before lookup.
- Success: HTTP 303 redirect to `/dashboard`, sets an HttpOnly, SameSite=Lax cookie named
  `session`. The dashboard shows the signed-in role in `user-role` (`admin` or `viewer`).
- Wrong password, unknown email, or empty fields: HTTP 401, the page shows exactly
  "Invalid email or password." in `login-error`. The message is identical in every case.
- Failed attempts with an unknown email do not count towards any lockout.

Brute-force lockout:
- LOCKOUT_THRESHOLD = 5 consecutive failed attempts on an existing account locks it for
  LOCKOUT_MINUTES = 15. At exactly 15 minutes after the lock started, it has run out.
- The attempt that reaches the threshold already gets HTTP 423 and exactly
  "Your account is locked after too many failed sign-in attempts. Try again later." in
  `login-error`.
- While locked, every attempt, including one with the correct password, gets the same 423
  lockout message.
- A successful sign-in resets the failure count to 0.
- When the lock runs out, counting starts again from 0.
- The API endpoint `POST /api/v1/auth/token` shares the same counter and lock; while locked it
  answers HTTP 423 with error code `account_locked`.

Forgot password:
- `GET /forgot-password`: field `forgot-email`, button `forgot-submit`.
- After submitting, the page always shows exactly "If an account exists for that email, we've
  sent a password reset link." in `forgot-confirmation`, whether or not the email exists.
- If the account exists, one email is delivered to the test outbox. It contains a link
  `/reset-password?token=<token>`. Unknown emails produce no email.
- A token is valid for RESET_TOKEN_MINUTES = 30 and can be used once. At exactly 30 minutes
  after it was issued it has already expired.
- Reset page: fields `reset-password`, `reset-confirm-password`; button `reset-submit`.
- New password shorter than 8 characters: HTTP 422, `reset-error` shows exactly
  "Password must be at least 8 characters."
- Confirmation differs: HTTP 422, `reset-error` shows exactly "Passwords do not match."
- Unknown, expired or already-used token: HTTP 400, `reset-error` shows exactly
  "This reset link is invalid or has expired." and no form is shown.
- Success: the password changes, any lockout on the account is cleared, every existing session
  of that user is ended, and the browser is redirected (HTTP 303) to `/login?reason=reset`, which shows
  exactly "Your password has been updated. Please sign in." in `login-notice`.

Sessions:
- A session lasts SESSION_TTL_SECONDS = 1800 from sign-in. Activity does not extend it. At
  exactly 1800 seconds after sign-in it has already expired.
- Opening `/dashboard` with an expired session redirects (303) to `/login?reason=expired`, which
  shows exactly "Your session has expired. Please sign in again." in `login-notice`.
- Opening `/dashboard` with no session redirects to `/login` with no notice.
- Sign out: button `logout` on the dashboard ends the session and redirects to
  `/login?reason=logged_out`, which shows exactly "You have been signed out." in `login-notice`.

Test hooks (available to every test; tests must never wait in real time):
- `POST /_test/reset` restores seed data (including lockout counters) and clears sessions and the outbox.
- `POST /_test/clock` with `{"advance_seconds": N}` moves the application clock forward by N
  seconds. Session, lockout and reset-token expiry all follow this clock.
- `GET /_test/outbox?to=<email>` returns the emails sent to that address, including the reset
  link.

## REQUIRED COVERAGE
Cover every one of these areas. Use them, spelled exactly like this, as `coverage_area` values:
- valid login
- invalid credentials
- forgot password
- session expiry
- brute-force lockout

Each area needs at least one `positive` case and at least one `negative`, `boundary` or
`security` case. What counts as `positive` in each area:
- valid login: correct credentials sign the user in.
- invalid credentials: after a rejected attempt, the same user can still sign in with the
  correct password (while below the lockout threshold).
- forgot password: an existing user receives a working reset link and can set a new password.
- session expiry: a session that has not expired still gives access to the dashboard.
- brute-force lockout: once the lock has run out, the user can sign in again.

Case types:
- `positive`: the main expected path with ordinary valid input.
- `boundary`: input or timing at an edge of what the app accepts: exact limits, the exact
  moment something expires, letter-case and whitespace variants of valid input.
- `negative`: invalid input or a disallowed action, and how the app rejects it.
- `security`: account enumeration, injection-like input, token tampering, wrong role.

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
            "pattern": "^LOGIN-\\d{3}$"
          },
          "module": {
            "const": "login"
          },
          "title": {
            "type": "string",
            "minLength": 10,
            "maxLength": 120
          },
          "coverage_area": {
            "enum": [
              "valid login",
              "invalid credentials",
              "forgot password",
              "session expiry",
              "brute-force lockout"
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
        "valid login",
        "invalid credentials",
        "forgot password",
        "session expiry",
        "brute-force lockout"
      ],
      "properties": {
        "valid login": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^LOGIN-\\d{3}$"
          }
        },
        "invalid credentials": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^LOGIN-\\d{3}$"
          }
        },
        "forgot password": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^LOGIN-\\d{3}$"
          }
        },
        "session expiry": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^LOGIN-\\d{3}$"
          }
        },
        "brute-force lockout": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^LOGIN-\\d{3}$"
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
1. IDs are `LOGIN-001`, `LOGIN-002`, ... in order, with no gaps or duplicates.
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
13. Assert an exact message text only when CONTEXT gives that text word for word. Otherwise
    assert only the HTTP status and error code.

## SELF-CHECK
Before you answer, check that:
- every required coverage area has at least one positive case and at least one negative,
  boundary or security case. Count them: for each area, count the cases whose `type` is
  exactly `positive`, and the cases whose `type` is `negative`, `boundary` or `security`.
  If either count is 0, add a case for that area before answering;
- `coverage_map` lists, for each area, the IDs of every case with that `coverage_area`, and
  every ID in it exists in `cases`;
- IDs run from 001 upwards with no gaps;
- no two cases test the same thing;
- no expected result uses a vague phrase;
- the output is a single JSON object matching the schema.
