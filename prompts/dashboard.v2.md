# Dashboard — regression test case generation (prompt v2)

## ROLE
You are a senior QA engineer designing a regression suite for the Dashboard module of a web
application. You write test cases that another engineer can automate without asking you
anything.

## CONTEXT
The application is TestMu Lite, a small test-management web app. Everything below is the
complete, authoritative behaviour of its Dashboard module. Elements are identified by their
`data-testid` attribute.

Access:
- `GET /dashboard` requires a signed-in session; without one it redirects to `/login`.
- Seed users: `admin@testmu.local` (role `admin`) and `viewer@testmu.local` (role `viewer`).
  The signed-in role is shown in `user-role`.

Widgets:
- Each widget's root element has a `data-state` attribute that is `loading` while its request
  is in flight, then `loaded` or `error`.
- On error, `widget-error` inside the widget shows the `message` field of the API's error
  body (not the `code`).
- If a widget request returns 401 (for example the session expired while the page was open),
  the page navigates to `/login?reason=expired`.
- `loading` lasts only while the request is in flight. A test can observe it reliably only by
  holding the request back (for example with Playwright route interception).
- Each widget loads from its own endpoint under `/api/v1/dashboard/`. These endpoints accept the
  browser session cookie or an `Authorization: Bearer <token>` header. With neither they return
  401 with error code `missing_token`.

| Widget (`data-testid`) | Endpoint | Who sees it | What it shows |
|---|---|---|---|
| `widget-total-test-cases` | `GET /api/v1/dashboard/total-test-cases` -> `{"value": int}` | everyone | number of test cases, as an integer in `widget-value` |
| `widget-pass-rate` | `GET /api/v1/dashboard/pass-rate` -> `{"value": float, "run_id": int, "run_name": str}` | everyone | pass rate of the latest run (by date) = round(passed * 100 / total, 1), shown like `87.5%` in `widget-value`; the run name in `widget-caption` |
| `widget-recent-runs` | `GET /api/v1/dashboard/recent-runs` -> `{"items": [run, ...]}` | everyone | table `runs-table`, one `run-row` per run (attribute `data-run-id`), cells `run-name`, `run-date`, `run-passed`, `run-failed`, `run-pass-rate` (like `95.8%`), `run-status` |
| `widget-flaky-tests` | `GET /api/v1/dashboard/flaky-tests` | admin only | one `flaky-row` per test (cells `flaky-name`, `flaky-flips`, `flaky-last-seen`), most flips first |
| `widget-team-activity` | `GET /api/v1/dashboard/team-activity` | admin only | one `activity-item` per entry, text `<email>: <action>`, newest first |

A run's `status` is `passed` when `failed` is 0, otherwise `failed`.

Seed data (restored by the reset hook before every test):
- 24 test cases.
- 12 runs, named `<date> nightly`, each with total 24:

| date | passed | failed | pass rate | status |
|---|---|---|---|---|
| 2026-09-10 | 24 | 0 | 100.0 | passed |
| 2026-09-11 | 22 | 2 | 91.7 | failed |
| 2026-09-12 | 23 | 1 | 95.8 | failed |
| 2026-09-13 | 24 | 0 | 100.0 | passed |
| 2026-09-14 | 20 | 4 | 83.3 | failed |
| 2026-09-15 | 24 | 0 | 100.0 | passed |
| 2026-09-16 | 23 | 1 | 95.8 | failed |
| 2026-09-17 | 21 | 3 | 87.5 | failed |
| 2026-09-18 | 24 | 0 | 100.0 | passed |
| 2026-09-19 | 22 | 2 | 91.7 | failed |
| 2026-09-20 | 24 | 0 | 100.0 | passed |
| 2026-09-21 | 21 | 3 | 87.5 | failed |

- 4 flaky tests and 5 team-activity entries.

Recent runs: filters and sort:
- Controls: `runs-filter-status` (All / `passed` / `failed`), `runs-filter-from` and
  `runs-filter-to` (dates, both inclusive), `runs-sort` (Default / `date` / `pass_rate`),
  `runs-order` (`desc` / `asc`).
- Changing any control reloads the widget and updates the page URL query string with
  `status`, `date_from`, `date_to`, `sort`, `order`. `order` is left out of the URL when no sort
  is chosen and it is `desc`.
- Opening `/dashboard` with these query parameters applies them on load.
- Default order: newest date first. Sorting by `pass_rate` breaks ties newest first.
- At most 10 rows are shown, taken after filtering and sorting.
- If no run matches, `runs-empty` shows exactly "No runs match these filters."
- API query parameters: `status`, `date_from`, `date_to` (YYYY-MM-DD), `sort`, `order`,
  `limit` (1-50, default 10). Invalid values return 422 `validation_error`. `date_from` later
  than `date_to` returns 422 with message "date_from must be on or before date_to"; the
  widget then shows the `error` state with that message.

Responsive layout:
- Viewport 768px wide or more: the sidebar (`sidebar`) is visible on the left and the widgets
  sit in a two-column grid (`widget-grid`): `widget-total-test-cases` and `widget-pass-rate`
  are side by side on the same row, and `widget-recent-runs` is as wide as the whole grid.
  `menu-toggle` is not visible.
- Narrower than 768px: widgets are stacked in one column (each one below the previous, each as
  wide as the grid), the sidebar is hidden, and a `menu-toggle` button shows and hides it; its
  `aria-expanded` attribute is `"false"` when the sidebar is hidden and `"true"` when shown.
- Wide tables scroll horizontally inside their widget instead of widening the page.

Permissions:
- Admins see all five widgets.
- Viewers see three: the Flaky tests and Team activity widgets are not in the page at all.
- For a viewer, their endpoints return HTTP 403 with
  `{"error": {"code": "forbidden", "message": "Admin role required"}}`.

Test hooks (available to every test):
- `POST /_test/reset` restores seed data.
- Admins can add test cases through `POST /api/v1/test-cases`, which changes the total count.

## REQUIRED COVERAGE
Cover every one of these areas. Use them, spelled exactly like this, as `coverage_area` values:
- widget loading
- data accuracy
- filter/sort behavior
- responsive layout
- permission-based visibility

Each area needs at least one `positive` case and at least one `negative`, `boundary` or
`security` case. What counts as `positive` in each area:
- widget loading: a widget reaches `loaded` and shows its content.
- data accuracy: a displayed value equals both the API value and the value expected from the
  seed data.
- filter/sort behavior: a filter or sort shows exactly the expected rows in the expected order.
- responsive layout: the layout matches the description for the viewport width.
- permission-based visibility: a user sees exactly the widgets their role allows.

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
            "pattern": "^DASH-\\d{3}$"
          },
          "module": {
            "const": "dashboard"
          },
          "title": {
            "type": "string",
            "minLength": 10,
            "maxLength": 120
          },
          "coverage_area": {
            "enum": [
              "widget loading",
              "data accuracy",
              "filter/sort behavior",
              "responsive layout",
              "permission-based visibility"
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
        "widget loading",
        "data accuracy",
        "filter/sort behavior",
        "responsive layout",
        "permission-based visibility"
      ],
      "properties": {
        "widget loading": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^DASH-\\d{3}$"
          }
        },
        "data accuracy": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^DASH-\\d{3}$"
          }
        },
        "filter/sort behavior": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^DASH-\\d{3}$"
          }
        },
        "responsive layout": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^DASH-\\d{3}$"
          }
        },
        "permission-based visibility": {
          "type": "array",
          "minItems": 1,
          "items": {
            "type": "string",
            "pattern": "^DASH-\\d{3}$"
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
1. IDs are `DASH-001`, `DASH-002`, ... in order, with no gaps or duplicates.
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
