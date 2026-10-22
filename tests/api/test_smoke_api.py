"""Smoke: a token can be issued and used to list test cases in the documented shape."""

import pytest

from app.seed import SEED_TEST_CASES
from framework.api_client import ApiClient
from framework.config import credentials
from framework.schemas import TEST_CASE_PAGE, TOKEN, assert_matches_schema


@pytest.mark.smoke
def test_token_then_list_test_cases(api_client: ApiClient) -> None:
    viewer = credentials("viewer")

    token_response = api_client.request_token(viewer.email, viewer.password)
    assert token_response.status_code == 200
    assert_matches_schema(token_response.json(), TOKEN)

    api_client.token = token_response.json()["access_token"]
    response = api_client.list_cases(page=1, page_size=10)

    assert response.status_code == 200
    body = response.json()
    assert_matches_schema(body, TEST_CASE_PAGE)
    assert body["total"] == len(SEED_TEST_CASES)
    assert len(body["items"]) == 10
