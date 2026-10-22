"""Expected API response schemas (JSON Schema), written from the test side.

These are the contract the tests hold the API to. They are deliberately not generated
from the app's own OpenAPI, so an unintended change in the app shows up as a failure.
"""

from typing import Any

from jsonschema import Draft202012Validator

ISO_DATETIME = {"type": "string", "format": "date-time"}
ISO_DATE = {"type": "string", "format": "date"}


def _object(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required if required is not None else list(properties),
        "additionalProperties": False,
    }


ERROR = _object({
    "error": _object({"code": {"type": "string"}, "message": {"type": "string"}}),
})

TOKEN = _object({
    "access_token": {"type": "string", "minLength": 1},
    "token_type": {"const": "bearer"},
    "expires_in": {"type": "integer", "minimum": 1},
    "expires_at": ISO_DATETIME,
})

TEST_CASE = _object({
    "id": {"type": "integer"},
    "title": {"type": "string", "minLength": 1, "maxLength": 200},
    "module": {"enum": ["login", "dashboard", "api"]},
    "priority": {"enum": ["P0", "P1", "P2"]},
    "description": {"type": "string"},
    "created_at": ISO_DATETIME,
    "updated_at": ISO_DATETIME,
})

TEST_CASE_PAGE = _object({
    "items": {"type": "array", "items": TEST_CASE},
    "page": {"type": "integer", "minimum": 1},
    "page_size": {"type": "integer", "minimum": 1, "maximum": 100},
    "total": {"type": "integer", "minimum": 0},
})

COUNT_WIDGET = _object({"value": {"type": "integer", "minimum": 0}})

PASS_RATE_WIDGET = _object({
    "value": {"type": "number", "minimum": 0, "maximum": 100},
    "run_id": {"type": "integer"},
    "run_name": {"type": "string"},
})

RUN = _object({
    "id": {"type": "integer"},
    "name": {"type": "string"},
    "run_date": ISO_DATE,
    "total": {"type": "integer"},
    "passed": {"type": "integer"},
    "failed": {"type": "integer"},
    "pass_rate": {"type": "number"},
    "status": {"enum": ["passed", "failed"]},
})

RUN_LIST = _object({"items": {"type": "array", "items": RUN}})

FLAKY_TEST_LIST = _object({
    "items": {"type": "array", "items": _object({
        "test_name": {"type": "string"}, "flips": {"type": "integer"}, "last_seen": ISO_DATE,
    })},
})

ACTIVITY_LIST = _object({
    "items": {"type": "array", "items": _object({
        "user_email": {"type": "string"}, "action": {"type": "string"}, "at": {"type": "string"},
    })},
})


def schema_errors(instance: Any, schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    return [
        f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    ]


def assert_matches_schema(instance: Any, schema: dict[str, Any]) -> None:
    errors = schema_errors(instance, schema)
    assert not errors, "Response does not match schema:\n" + "\n".join(errors)
