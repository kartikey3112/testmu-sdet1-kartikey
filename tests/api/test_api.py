"""REST API: automated from generated/api.json (accepted prompt v4).

Adaptations, noted per test: API-009 hard-codes id 26; its own precondition says to create
the case first, so the test deletes the id the create call returned.
"""

import pytest

from framework.api_client import ApiClient, assert_error
from framework.config import credentials
from framework.data.builders import build_case
from framework.schemas import TEST_CASE, TOKEN, assert_matches_schema
from framework.test_control import TestControl

RATE_LIMIT_PER_MIN = 60


def tamper(token: str) -> str:
    """Change one character in the middle of the signature.

    The last base64url character can carry unused bits, so changing it may leave the decoded
    signature unchanged; a middle character always changes it.
    """
    header, payload, signature = token.split(".")
    i = len(signature) // 2
    replacement = "A" if signature[i] != "A" else "B"
    return ".".join([header, payload, signature[:i] + replacement + signature[i + 1:]])


# --- auth token validation ---------------------------------------------------------------------

@pytest.mark.case("API-001")
def test_valid_admin_token_lists_test_cases(api_client: ApiClient) -> None:
    admin = credentials("admin")

    token = api_client.request_token(admin.email, admin.password)
    api_client.token = token.json()["access_token"]
    response = api_client.list_cases()

    assert token.status_code == 200
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["items"], list)
    assert isinstance(body["page"], int)
    assert "error" not in body


@pytest.mark.case("API-004")
def test_tampered_token_is_rejected(admin_api: ApiClient) -> None:
    admin_api.token = tamper(admin_api.token)

    response = admin_api.list_cases()

    assert_error(response, 401, "invalid_token")
    assert response.json()["error"]["message"] == "Token is malformed or has an invalid signature"


# --- CRUD operations ---------------------------------------------------------------------------

@pytest.mark.case("API-005")
def test_admin_creates_a_test_case(admin_api: ApiClient) -> None:
    body = build_case(title="New API test case", module="api", priority="P1",
                      description="Created for CRUD create test")

    response = admin_api.create_case(body)

    assert response.status_code == 201
    created = response.json()
    assert_matches_schema(created, TEST_CASE)
    assert {k: created[k] for k in body} == body


@pytest.mark.case("API-009")
def test_admin_deletes_a_test_case(admin_api: ApiClient) -> None:
    case_id = admin_api.create_case(build_case()).json()["id"]

    deleted = admin_api.delete_case(case_id)
    after = admin_api.get_case(case_id)

    assert deleted.status_code == 204
    assert deleted.content == b""
    assert_error(after, 404, "not_found")
    assert after.json()["error"]["message"] == f"Test case {case_id} not found"


@pytest.mark.case("API-010")
def test_viewer_cannot_create_a_test_case(viewer_api: ApiClient) -> None:
    response = viewer_api.create_case(build_case(title="Viewer Attempt", priority="P2"))

    assert_error(response, 403, "forbidden")
    assert response.json()["error"]["message"] == "Admin role required"


# --- error handling (4xx/5xx) ------------------------------------------------------------------

@pytest.mark.case("API-014")
def test_unknown_id_returns_404(admin_api: ApiClient) -> None:
    response = admin_api.get_case(9999)

    assert_error(response, 404, "not_found")
    assert response.json()["error"]["message"] == "Test case 9999 not found"


@pytest.mark.case("API-017")
def test_database_fault_returns_500(admin_api: ApiClient, test_control: TestControl) -> None:
    test_control.set_faults("ENV_DB_UNAVAILABLE")

    response = admin_api.list_cases()

    assert_error(response, 500, "internal_error")
    assert response.json()["error"]["message"] == "Internal server error"


@pytest.mark.case("API-018")
def test_list_works_again_after_fault_is_cleared(
    admin_api: ApiClient, test_control: TestControl
) -> None:
    test_control.set_faults("ENV_DB_UNAVAILABLE")
    assert admin_api.list_cases().status_code == 500

    test_control.reset(keep_sessions=True)
    response = admin_api.list_cases()

    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


# --- rate limiting -----------------------------------------------------------------------------

@pytest.mark.case("API-019")
def test_sixty_requests_in_a_minute_succeed(
    admin_api: ApiClient, test_control: TestControl
) -> None:
    test_control.advance_to_next_minute()

    statuses = [admin_api.list_cases().status_code for _ in range(RATE_LIMIT_PER_MIN)]

    assert statuses == [200] * RATE_LIMIT_PER_MIN


@pytest.mark.case("API-020")
def test_sixty_first_request_is_rate_limited(
    admin_api: ApiClient, test_control: TestControl
) -> None:
    test_control.advance_to_next_minute()
    for _ in range(RATE_LIMIT_PER_MIN):
        admin_api.list_cases()

    response = admin_api.list_cases()

    assert_error(response, 429, "rate_limited")
    assert response.json()["error"]["message"] == "Rate limit of 60 requests per minute exceeded"
    assert int(response.headers["Retry-After"]) >= 1


# --- schema validation -------------------------------------------------------------------------

@pytest.mark.case("API-021")
def test_token_response_matches_schema(api_client: ApiClient) -> None:
    admin = credentials("admin")

    response = api_client.request_token(admin.email, admin.password)

    assert response.status_code == 200
    assert_matches_schema(response.json(), TOKEN)


@pytest.mark.case("API-022")
def test_created_test_case_matches_schema(admin_api: ApiClient) -> None:
    response = admin_api.create_case(build_case(title="Schema Test Case", priority="P2",
                                                description="Validate response schema"))

    assert response.status_code == 201
    assert_matches_schema(response.json(), TEST_CASE)
