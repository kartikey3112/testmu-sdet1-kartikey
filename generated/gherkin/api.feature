# Generated from generated/api.json by ai/testgen/to_gherkin.py. Do not edit by hand.
@api
Feature: REST API regression cases

  Rule: auth token validation

    @API-001 @P0 @positive @automation_candidate
    Scenario: API-001 Valid admin token allows access to test case list
      # test_data: {"email": "admin@testmu.local", "password": "{{admin_password}}"}
      Given Reset system state
      And Obtain admin token via POST /api/v1/auth/token with valid credentials
      When POST /api/v1/auth/token with email and password
      And Extract access_token from response
      And GET /api/v1/test-cases with Authorization: Bearer <token>
      Then POST returns 200 with access_token field
      And GET returns 200 and a JSON body containing items array
      And Response includes field "page" as integer
      And No error object present

    @API-002 @P1 @negative @automation_candidate
    Scenario: API-002 Missing Authorization header returns authentication required error
      Given Reset system state
      When GET /api/v1/test-cases without Authorization header
      Then Response status is 401
      And Response body is {"error":{"code":"missing_token","message":"Authentication required"}}

    @API-003 @P1 @boundary @automation_candidate
    Scenario: API-003 Expired token is rejected with token_expired error
      # test_data: {"email": "admin@testmu.local", "password": "{{admin_password}}", "advance_seconds": 3600}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And POST /_test/clock with {"advance_seconds":3600}
      And GET /api/v1/test-cases with Authorization: Bearer <token>
      Then GET returns 401
      And Response body is {"error":{"code":"token_expired","message":"Token has expired"}}

    @API-004 @P0 @security @automation_candidate
    Scenario: API-004 Tampered JWT token results in invalid token error
      # test_data: {"email": "admin@testmu.local", "password": "{{admin_password}}"}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And Modify one character of the token string
      And GET /api/v1/test-cases with Authorization: Bearer <tampered-token>
      Then GET returns 401
      And Response body is {"error":{"code":"invalid_token","message":"Token is malformed or has an invalid signature"}}

  Rule: CRUD operations

    @API-005 @P0 @positive @automation_candidate
    Scenario: API-005 Admin can create a new test case successfully
      # test_data: {"title": "New API test case", "module": "api", "priority": "P1", "description": "Created for CRUD create test"}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And POST /api/v1/test-cases with JSON body and Authorization header
      Then POST returns 201
      And Response body contains fields id, title, module, priority, description, created_at, updated_at
      And All fields have correct types and no extra fields

    @API-006 @P1 @positive @automation_candidate
    Scenario: API-006 List test cases with paging returns correct page metadata
      # test_data: {"page": 1, "page_size": 5}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And GET /api/v1/test-cases?page=1&page_size=5 with Authorization header
      Then GET returns 200
      And Response body contains items array (max 5 items)
      And Response body contains page=1, page_size=5, total as integer
      And No extra fields in response

    @API-007 @P1 @positive @automation_candidate
    Scenario: API-007 Viewer can retrieve a test case by ID
      # test_data: {"id": 1}
      Given Reset system state
      And Obtain viewer token
      When POST /api/v1/auth/token with viewer credentials
      And GET /api/v1/test-cases/1 with Authorization header
      Then GET returns 200
      And Response body contains id=1 and all documented fields
      And No error object present

    @API-008 @P1 @positive @automation_candidate
    Scenario: API-008 Admin can update test case title and see updated_at change
      # test_data: {"id": 25, "new_title": "Updated Title"}
      Given Reset system state
      And Obtain admin token
      And Create test case with title "Update Me"
      When POST /api/v1/auth/token to obtain token
      And PATCH /api/v1/test-cases/25 with JSON {"title":"Updated Title"} and Authorization header
      Then PATCH returns 200
      And Response body title is "Updated Title"
      And updated_at timestamp is later than original created_at

    @API-009 @P1 @positive @automation_candidate
    Scenario: API-009 Admin can delete a test case and subsequent GET returns 404
      # test_data: {"id": 26}
      Given Reset system state
      And Obtain admin token
      And Create test case to delete
      When POST /api/v1/auth/token to obtain token
      And DELETE /api/v1/test-cases/26 with Authorization header
      And GET /api/v1/test-cases/26 with Authorization header
      Then DELETE returns 204 with empty body
      And GET returns 404
      And Response body is {"error":{"code":"not_found","message":"Test case 26 not found"}}

    @API-010 @P0 @negative @automation_candidate
    Scenario: API-010 Viewer role is forbidden from creating a test case
      # test_data: {"title": "Viewer Attempt", "module": "api", "priority": "P2"}
      Given Reset system state
      And Obtain viewer token
      When POST /api/v1/auth/token with viewer credentials
      And POST /api/v1/test-cases with JSON body and Authorization header
      Then POST returns 403
      And Response body is {"error":{"code":"forbidden","message":"Admin role required"}}

    @API-011 @P1 @negative @automation_candidate
    Scenario: API-011 Creating a test case with duplicate title returns conflict error
      # test_data: {"title": "Duplicate Title", "module": "api", "priority": "P1"}
      Given Reset system state
      And Obtain admin token
      And Create test case with title "Duplicate Title"
      When POST /api/v1/auth/token to obtain token
      And POST /api/v1/test-cases with JSON body using title "Duplicate Title"
      Then POST returns 409
      And Response body is {"error":{"code":"duplicate_title","message":"A test case titled 'Duplicate Title' already exists"}}

    @API-012 @P2 @boundary @automation_candidate
    Scenario: API-012 Title at maximum length (200 chars) is accepted on creation
      # test_data: {"title": "T\".repeat(200)", "module": "api", "priority": "P2"}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And POST /api/v1/test-cases with JSON body containing 200‑character title
      Then POST returns 201
      And Response body title length is 200 characters
      And All other fields are present and valid

    @API-013 @P2 @boundary @automation_candidate
    Scenario: API-013 Page size maximum of 100 returns up to 100 items
      # test_data: {"page": 1, "page_size": 100}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And GET /api/v1/test-cases?page=1&page_size=100 with Authorization header
      Then GET returns 200
      And Response body items array length is <=100
      And Response includes page=1 and page_size=100

  Rule: error handling (4xx/5xx)

    @API-014 @P1 @negative @automation_candidate
    Scenario: API-014 Requesting unknown test case ID returns 404 not_found error
      # test_data: {"id": 9999}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And GET /api/v1/test-cases/9999 with Authorization header
      Then GET returns 404
      And Response body is {"error":{"code":"not_found","message":"Test case 9999 not found"}}

    @API-015 @P1 @negative @automation_candidate
    Scenario: API-015 Using wrong HTTP method on test case endpoint returns 405 method_not_allowed
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And POST /api/v1/test-cases/1 with Authorization header
      Then POST returns 405
      And Response body is {"error":{"code":"method_not_allowed","message":"Method Not Allowed"}}

    @API-016 @P1 @negative @automation_candidate
    Scenario: API-016 Creating test case with missing required field returns validation error
      # test_data: {"module": "api", "priority": "P1"}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And POST /api/v1/test-cases with JSON missing "title"
      Then POST returns 422
      And Response body contains error code "validation_error"

    @API-017 @P2 @negative @automation_candidate
    Scenario: API-017 Database fault causes 500 internal error on list request
      Given Reset system state
      And Inject database fault
      When POST /_test/faults with {"faults":["ENV_DB_UNAVAILABLE"]}
      And GET /api/v1/test-cases
      Then GET returns 500
      And Response body is {"error":{"code":"internal_error","message":"Internal server error"}}

    @API-018 @P1 @positive @automation_candidate
    Scenario: API-018 After resetting faults, list request succeeds again
      Given Database fault injected previously
      And Reset system state
      When POST /_test/reset to clear faults
      And GET /api/v1/test-cases
      Then GET returns 200
      And Response body contains items array

  Rule: rate limiting

    @API-019 @P0 @positive @automation_candidate
    Scenario: API-019 Sending 60 requests within a minute succeeds without rate limiting
      # test_data: {"request_count": 60}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And Loop 60 times: GET /api/v1/test-cases with Authorization header
      Then All 60 GET requests return 200

    @API-020 @P0 @negative @automation_candidate
    Scenario: API-020 61st request in same minute returns 429 rate limited error
      Given Reset system state
      And Obtain admin token
      And Send 60 successful requests
      When POST /api/v1/auth/token to obtain token
      And Send 60 GET requests to /api/v1/test-cases
      And Send 61st GET request to same endpoint
      Then 61st request returns 429
      And Response body is {"error":{"code":"rate_limited","message":"Rate limit of 60 requests per minute exceeded"}}
      And Response includes Retry-After header with integer >=1

  Rule: schema validation

    @API-021 @P0 @positive @automation_candidate
    Scenario: API-021 Token response matches documented schema exactly
      # test_data: {"email": "admin@testmu.local", "password": "{{admin_password}}"}
      Given Reset system state
      When POST /api/v1/auth/token with valid credentials
      Then Response status 200
      And Response JSON contains exactly fields: access_token (string), token_type (string), expires_in (integer), expires_at (string)
      And No additional fields are present

    @API-022 @P0 @positive @automation_candidate
    Scenario: API-022 Created test case object conforms to response schema
      # test_data: {"title": "Schema Test Case", "module": "api", "priority": "P2", "description": "Validate response schema"}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And POST /api/v1/test-cases with JSON body
      Then POST returns 201
      And Response JSON contains exactly fields: id (integer), title (string), module (string), priority (string), description (string), created_at (string), updated_at (string)
      And No extra fields are present

    @API-023 @P1 @negative @automation_candidate
    Scenario: API-023 Error response for unknown ID has correct error body shape
      # test_data: {"id": 8888}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And GET /api/v1/test-cases/8888 with Authorization header
      Then GET returns 404
      And Response body is exactly {"error":{"code":"not_found","message":"Test case 8888 not found"}}
      And No additional fields are present

    @API-024 @P2 @boundary @automation_candidate
    Scenario: API-024 Empty items list on out‑of‑range page matches list schema
      # test_data: {"page": 999, "page_size": 20}
      Given Reset system state
      And Obtain admin token
      When POST /api/v1/auth/token to obtain token
      And GET /api/v1/test-cases?page=999&page_size=20 with Authorization header
      Then GET returns 200
      And Response JSON contains fields: items (empty array), page (integer), page_size (integer), total (integer)
      And No extra fields are present
