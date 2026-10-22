# Generated from generated/login.json by ai/testgen/to_gherkin.py. Do not edit by hand.
@login
Feature: Login regression cases

  Rule: valid login

    @LOGIN-001 @P0 @positive @automation_candidate
    Scenario: LOGIN-001 Admin user can sign in with correct credentials
      # test_data: {"email": "admin@testmu.local", "password": "{{admin_password}}"}
      Given POST /_test/reset
      When Navigate to GET /login
      And Enter email admin@testmu.local into field login-email
      And Enter password {{admin_password}} into field login-password
      And Click button login-submit
      Then Response HTTP 303 redirect to /dashboard
      And Set HttpOnly SameSite=Lax cookie named session
      And Dashboard element user-role contains text admin

    @LOGIN-002 @P1 @boundary @automation_candidate
    Scenario: LOGIN-002 Login trims whitespace and lower‑cases email address
      # test_data: {"email": "  ADMIN@TESTMU.LOCAL  ", "password": "{{admin_password}}"}
      Given POST /_test/reset
      When Navigate to GET /login
      And Enter email with leading/trailing spaces and uppercase into login-email
      And Enter password {{admin_password}} into login-password
      And Click button login-submit
      Then Response HTTP 303 redirect to /dashboard
      And Dashboard element user-role contains text admin

    @LOGIN-003 @P1 @negative @automation_candidate
    Scenario: LOGIN-003 Sign‑in fails with incorrect password
      # test_data: {"email": "viewer@testmu.local", "password": "wrongpass"}
      Given POST /_test/reset
      When Navigate to GET /login
      And Enter email viewer@testmu.local into login-email
      And Enter password wrongpass into login-password
      And Click button login-submit
      Then Response HTTP 401
      And Element login-error contains text "Invalid email or password."

  Rule: invalid credentials

    @LOGIN-004 @P0 @positive @automation_candidate
    Scenario: LOGIN-004 After a failed attempt, correct credentials still allow sign‑in
      # test_data: {"email": "viewer@testmu.local", "wrong_password": "bad", "correct_password": "{{viewer_password}}"}
      Given POST /_test/reset
      When Navigate to GET /login
      And Enter email viewer@testmu.local into login-email
      And Enter password bad into login-password
      And Click button login-submit
      And Observe login-error with text "Invalid email or password."
      And Enter password {{viewer_password}} into login-password (same page)
      And Click button login-submit again
      Then Second response HTTP 303 redirect to /dashboard
      And Dashboard element user-role contains text viewer

    @LOGIN-005 @P1 @negative @automation_candidate
    Scenario: LOGIN-005 Sign‑in with unknown email returns generic error
      # test_data: {"email": "unknown@example.com", "password": "any"}
      Given POST /_test/reset
      When Navigate to GET /login
      And Enter email unknown@example.com into login-email
      And Enter password any into login-password
      And Click button login-submit
      Then Response HTTP 401
      And Element login-error contains text "Invalid email or password."

  Rule: forgot password

    @LOGIN-006 @P0 @positive @automation_candidate
    Scenario: LOGIN-006 User receives reset link and can set a new password
      # test_data: {"email": "viewer@testmu.local", "new_password": "newStrongPass1"}
      Given POST /_test/reset
      When Navigate to GET /forgot-password
      And Enter email viewer@testmu.local into forgot-email
      And Click button forgot-submit
      And GET /_test/outbox?to=viewer@testmu.local and extract reset link token
      And Navigate to GET /reset-password?token=<extracted token>
      And Enter new password newStrongPass1 into reset-password
      And Enter same password into reset-confirm-password
      And Click button reset-submit
      Then Response HTTP 303 redirect to /login?reason=reset
      And Element login-notice contains text "Your password has been updated. Please sign in."
      And Subsequent sign‑in with new password succeeds (HTTP 303 to /dashboard)

    @LOGIN-007 @P2 @boundary @automation_candidate
    Scenario: LOGIN-007 Reset link expires exactly after 30 minutes
      # test_data: {"email": "admin@testmu.local"}
      Given POST /_test/reset
      When Navigate to GET /forgot-password
      And Enter email admin@testmu.local into forgot-email
      And Click button forgot-submit
      And GET /_test/outbox?to=admin@testmu.local and extract token
      And POST /_test/clock with {"advance_seconds":1800}
      And Navigate to GET /reset-password?token=<extracted token>
      Then Response HTTP 400
      And Element reset-error contains text "This reset link is invalid or has expired."
      And No password reset form is displayed

    @LOGIN-008 @P0 @security @automation_candidate
    Scenario: LOGIN-008 Forgot‑password does not reveal whether email exists
      # test_data: {"email": "nonexistent@testmu.local"}
      Given POST /_test/reset
      When Navigate to GET /forgot-password
      And Enter email nonexistent@testmu.local into forgot-email
      And Click button forgot-submit
      Then Element forgot-confirmation contains text "If an account exists for that email, we've sent a password reset link."
      And GET /_test/outbox?to=nonexistent@testmu.local returns empty list

  Rule: session expiry

    @LOGIN-009 @P0 @positive @automation_candidate
    Scenario: LOGIN-009 Active session allows access to dashboard
      # test_data: {"email": "admin@testmu.local", "password": "{{admin_password}}"}
      Given POST /_test/reset
      When Navigate to GET /login
      And Enter email admin@testmu.local and password {{admin_password}} and submit
      And Obtain session cookie from response
      And Within less than 1800 seconds, navigate to GET /dashboard with session cookie
      Then Response HTTP 200 (dashboard page)
      And Element user-role contains text admin

    @LOGIN-010 @P2 @boundary @automation_candidate
    Scenario: LOGIN-010 Session expires exactly after 1800 seconds
      # test_data: {"email": "viewer@testmu.local", "password": "{{viewer_password}}"}
      Given POST /_test/reset
      When Sign in as viewer@testmu.local to obtain session cookie
      And POST /_test/clock with {"advance_seconds":1800}
      And Navigate to GET /dashboard with session cookie
      Then Response HTTP 303 redirect to /login?reason=expired
      And Element login-notice contains text "Your session has expired. Please sign in again."

    @LOGIN-011 @P1 @negative @automation_candidate
    Scenario: LOGIN-011 Accessing dashboard without a session redirects to login
      Given POST /_test/reset
      When Navigate to GET /dashboard without any session cookie
      Then Response HTTP 303 redirect to /login
      And Login page shows no login-notice element

  Rule: brute-force lockout

    @LOGIN-012 @P0 @negative @automation_candidate
    Scenario: LOGIN-012 Fifth consecutive failed login locks the account
      # test_data: {"email": "admin@testmu.local", "wrong_password": "badpass"}
      Given POST /_test/reset
      When Repeat 5 times: navigate to GET /login, enter email admin@testmu.local, enter password badpass, click login-submit
      Then On the fifth attempt response HTTP 423
      And Element login-error contains text "Your account is locked after too many failed sign-in attempts. Try again later."

    @LOGIN-013 @P0 @security @automation_candidate
    Scenario: LOGIN-013 Correct password is rejected while account is locked
      # test_data: {"email": "viewer@testmu.local", "wrong_password": "bad", "correct_password": "{{viewer_password}}"}
      Given POST /_test/reset
      When Perform 5 consecutive failed attempts with wrong password for viewer@testmu.local to trigger lock
      And Immediately attempt login with correct password {{viewer_password}}
      And Click button login-submit
      Then Response HTTP 423
      And Element login-error contains text "Your account is locked after too many failed sign-in attempts. Try again later."

    @LOGIN-014 @P2 @boundary @automation_candidate
    Scenario: LOGIN-014 Account unlocks exactly after 15 minutes lockout period
      # test_data: {"email": "admin@testmu.local", "wrong_password": "bad", "correct_password": "{{admin_password}}"}
      Given POST /_test/reset
      When Perform 5 failed attempts to lock admin account
      And POST /_test/clock with {"advance_seconds":900}
      And Attempt login with correct password {{admin_password}}
      Then Response HTTP 303 redirect to /dashboard
      And Dashboard element user-role contains text admin

    @LOGIN-015 @P1 @positive @automation_candidate
    Scenario: LOGIN-015 Successful login after lockout period clears failure count
      # test_data: {"email": "viewer@testmu.local", "wrong_password": "bad", "correct_password": "{{viewer_password}}"}
      Given POST /_test/reset
      When Perform 5 failed attempts to lock viewer account
      And POST /_test/clock with {"advance_seconds":901}
      And Attempt login with correct password {{viewer_password}}
      And Observe successful sign‑in
      And Immediately attempt another login with wrong password bad
      Then First post‑lock attempt response HTTP 303 redirect to /dashboard
      And Second immediate wrong password attempt response HTTP 401
