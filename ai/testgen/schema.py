"""JSON Schema for generated test cases.

The same schema is pasted into each prompt's OUTPUT CONTRACT and used by the validator,
so what the model is asked for and what it is checked against can't drift apart.
"""

import json
from typing import Any

# The assessment's required scenarios, word for word. Each is a coverage_area enum value.
COVERAGE_AREAS: dict[str, list[str]] = {
    "login": [
        "valid login",
        "invalid credentials",
        "forgot password",
        "session expiry",
        "brute-force lockout",
    ],
    "dashboard": [
        "widget loading",
        "data accuracy",
        "filter/sort behavior",
        "responsive layout",
        "permission-based visibility",
    ],
    "api": [
        "auth token validation",
        "CRUD operations",
        "error handling (4xx/5xx)",
        "rate limiting",
        "schema validation",
    ],
}

ID_PREFIX = {"login": "LOGIN", "dashboard": "DASH", "api": "API"}

CASE_TYPES = ["positive", "negative", "boundary", "security", "non_functional"]
PRIORITIES = ["P0", "P1", "P2"]


def case_schema(module: str) -> dict[str, Any]:
    areas = COVERAGE_AREAS[module]
    string_list = {"type": "array", "items": {"type": "string", "minLength": 1}}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["cases", "coverage_map", "open_questions"],
        "properties": {
            "cases": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "id", "module", "title", "coverage_area", "type", "priority",
                        "preconditions", "test_data", "steps", "expected_results",
                        "automation_candidate", "notes",
                    ],
                    "properties": {
                        "id": {"type": "string", "pattern": f"^{ID_PREFIX[module]}-\\d{{3}}$"},
                        "module": {"const": module},
                        "title": {"type": "string", "minLength": 10, "maxLength": 120},
                        "coverage_area": {"enum": areas},
                        "type": {"enum": CASE_TYPES},
                        "priority": {"enum": PRIORITIES},
                        "preconditions": string_list,
                        "test_data": {"type": "object"},
                        "steps": {**string_list, "minItems": 1},
                        "expected_results": {**string_list, "minItems": 1},
                        "automation_candidate": {"type": "boolean"},
                        "notes": {"type": "string"},
                    },
                },
            },
            "coverage_map": {
                "type": "object",
                "additionalProperties": False,
                "required": areas,
                "properties": {
                    area: {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string", "pattern": f"^{ID_PREFIX[module]}-\\d{{3}}$"},
                    }
                    for area in areas
                },
            },
            "open_questions": string_list,
        },
    }


def schema_text(module: str) -> str:
    """The schema exactly as it appears in the prompt."""
    return json.dumps(case_schema(module), indent=2)
