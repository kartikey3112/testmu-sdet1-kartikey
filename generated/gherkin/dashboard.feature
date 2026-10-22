# Generated from generated/dashboard.json by ai/testgen/to_gherkin.py. Do not edit by hand.
@dashboard
Feature: Dashboard regression cases

  Rule: widget loading

    @DASH-001 @P0 @positive @automation_candidate
    Scenario: DASH-001 Total test cases widget loads successfully for admin
      Given Reset test data via POST /_test/reset
      And Sign in as admin@testmu.local
      When Navigate to /dashboard
      And Wait for widget-total-test-cases to have data-state='loaded'
      Then widget-total-test-cases element has attribute data-state='loaded'

    @DASH-002 @P1 @negative @automation_candidate
    Scenario: DASH-002 Recent runs widget shows validation error when date_from is after date_to
      # test_data: {"date_from": "2026-09-20", "date_to": "2026-09-10"}
      Given Reset test data
      And Sign in as admin
      When Navigate to /dashboard
      And Set runs-filter-from to 2026-09-20
      And Set runs-filter-to to 2026-09-10
      Then widget-recent-runs element has attribute data-state='error'
      And widget-recent-runs .widget-error contains text 'date_from must be on or before date_to'

    @DASH-003 @P2 @boundary @automation_candidate
    Scenario: DASH-003 Recent runs widget displays loading state while request is delayed
      # notes: Use Playwright route interception to hold the request.
      Given Reset test data
      And Sign in as admin
      And Set up route interception to delay GET /api/v1/dashboard/recent-runs by 5 seconds
      When Navigate to /dashboard
      And Immediately check widget-recent-runs data-state
      Then widget-recent-runs element has attribute data-state='loading'

  Rule: data accuracy

    @DASH-004 @P0 @positive @automation_candidate
    Scenario: DASH-004 Total test cases widget displays correct count from seed data
      Given Reset test data
      And Sign in as admin
      When Navigate to /dashboard
      And Wait for widget-total-test-cases data-state='loaded'
      And Read text of widget-total-test-cases .widget-value
      Then widget-total-test-cases .widget-value text equals '24'

    @DASH-005 @P0 @positive @automation_candidate
    Scenario: DASH-005 Pass rate widget shows correct percentage and run name from latest run
      Given Reset test data
      And Sign in as admin
      When Navigate to /dashboard
      And Wait for widget-pass-rate data-state='loaded'
      And Read widget-pass-rate .widget-value
      And Read widget-pass-rate .widget-caption
      Then widget-pass-rate .widget-value text equals '87.5%'
      And widget-pass-rate .widget-caption text equals '2026-09-21 nightly'

    @DASH-006 @P1 @boundary @automation_candidate
    Scenario: DASH-006 Total test cases widget updates after adding a new test case
      # test_data: {"new_test_case": {"name": "New case"}}
      Given Reset test data
      And Sign in as admin
      When Navigate to /dashboard
      And Wait for widget-total-test-cases loaded
      And POST /api/v1/test-cases with body {"name":"New case"}
      And Refresh /dashboard
      And Wait for widget-total-test-cases loaded
      Then widget-total-test-cases .widget-value text equals '25'

  Rule: filter/sort behavior

    @DASH-007 @P0 @positive @automation_candidate
    Scenario: DASH-007 Recent runs widget default shows latest 10 runs sorted by date descending
      Given Reset test data
      And Sign in as admin
      When Navigate to /dashboard
      And Wait for widget-recent-runs loaded
      And Count run-row elements
      And Read data-run-id of first run-row
      Then widget-recent-runs contains exactly 10 run-row elements
      And First run-row .run-name text equals '2026-09-21 nightly'

    @DASH-008 @P1 @negative @automation_candidate
    Scenario: DASH-008 Invalid status filter value triggers validation error in recent runs widget
      # test_data: {"status": "unknown"}
      Given Reset test data
      And Sign in as admin
      When Navigate to /dashboard
      And Set runs-filter-status to 'unknown' (invalid)
      Then widget-recent-runs data-state='error'
      And widget-recent-runs .widget-error contains error code 'validation_error'

    @DASH-009 @P2 @boundary @automation_candidate
    Scenario: DASH-009 Date filter with same from and to returns single matching run
      # test_data: {"date": "2026-09-10"}
      Given Reset test data
      And Sign in as admin
      When Navigate to /dashboard
      And Set runs-filter-from to 2026-09-10
      And Set runs-filter-to to 2026-09-10
      Then widget-recent-runs contains exactly 1 run-row
      And run-row .run-name text equals '2026-09-10 nightly'

    @DASH-010 @P0 @security @automation_candidate
    Scenario: DASH-010 Expired session token causes redirect to login with reason=expired
      Given Reset test data
      And Sign in as admin
      And Obtain valid session cookie
      And Tamper session cookie to be invalid
      When Navigate to /dashboard with tampered session cookie
      Then Browser navigates to '/login?reason=expired'

  Rule: responsive layout

    @DASH-011 @P0 @positive @automation_candidate
    Scenario: DASH-011 Wide viewport displays sidebar and two-column widget grid
      # test_data: {"viewport_width": 1024}
      Given Reset test data
      And Sign in as admin
      When Set viewport width to 1024px
      And Navigate to /dashboard
      Then Element with data-testid='sidebar' is visible
      And Element with data-testid='menu-toggle' is not visible
      And Element with data-testid='widget-grid' has two columns layout (widget-total-test-cases and widget-pass-rate share a row)

    @DASH-012 @P2 @boundary @automation_candidate
    Scenario: DASH-012 Viewport exactly 768px uses wide layout with sidebar visible
      # test_data: {"viewport_width": 768}
      Given Reset test data
      And Sign in as admin
      When Set viewport width to 768px
      And Navigate to /dashboard
      Then Element with data-testid='sidebar' is visible
      And Element with data-testid='menu-toggle' is not visible

    @DASH-013 @P1 @negative @automation_candidate
    Scenario: DASH-013 Narrow viewport hides sidebar and toggles visibility via menu button
      # test_data: {"viewport_width": 500}
      Given Reset test data
      And Sign in as admin
      When Set viewport width to 500px
      And Navigate to /dashboard
      And Verify menu-toggle aria-expanded='false' and sidebar hidden
      And Click menu-toggle
      And Verify aria-expanded='true' and sidebar visible
      Then menu-toggle attribute aria-expanded equals 'false' initially
      And sidebar is not visible initially
      And After click, menu-toggle aria-expanded equals 'true'
      And sidebar becomes visible

  Rule: permission-based visibility

    @DASH-014 @P0 @positive @automation_candidate
    Scenario: DASH-014 Admin user sees all five dashboard widgets
      Given Reset test data
      And Sign in as admin@testmu.local
      When Navigate to /dashboard
      Then Elements with data-testid 'widget-total-test-cases', 'widget-pass-rate', 'widget-recent-runs', 'widget-flaky-tests', 'widget-team-activity' are all present

    @DASH-015 @P1 @negative @automation_candidate
    Scenario: DASH-015 Viewer user sees only three widgets and missing admin widgets
      Given Reset test data
      And Sign in as viewer@testmu.local
      When Navigate to /dashboard
      Then Elements with data-testid 'widget-total-test-cases', 'widget-pass-rate', 'widget-recent-runs' are present
      And Elements with data-testid 'widget-flaky-tests' and 'widget-team-activity' are not present

    @DASH-016 @P0 @security @automation_candidate
    Scenario: DASH-016 Viewer attempting to load flaky-tests endpoint receives forbidden error
      Given Reset test data
      And Sign in as viewer@testmu.local
      When Send GET request to /api/v1/dashboard/flaky-tests with viewer session
      Then Response status is 403
      And Response body error code equals 'forbidden'
      And Response body error message equals 'Admin role required'
