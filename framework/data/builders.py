"""Builders for users, test cases and runs used in tests."""

import uuid
from typing import Any


def unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


def build_case(**overrides: Any) -> dict[str, Any]:
    """A valid POST /api/v1/test-cases body with a unique title."""
    body = {
        "title": f"Generated case {unique_suffix()}",
        "module": "api",
        "priority": "P1",
        "description": "Created by the test suite",
    }
    return body | overrides
