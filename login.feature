```gherkin
Feature: User Login
  As a user
  I want to log in to my account
  So that I can access my personalized content and features

  Scenario: Successful login with valid credentials
    Given the user is on the login page
    When the user enters a valid email address
    And the user enters a valid password
    And the user clicks the login button
    Then the user should be redirected to the dashboard
    And the user should see their personalized content

  Scenario: Unsuccessful login with invalid email
    Given the user is on the login page
    When the user enters an invalid email address
    And the user enters a valid password
    And the user clicks the login button
    Then the user should see an error message "Invalid email or password"
    And the user should remain on the login page

  Scenario: Unsuccessful login with invalid password
    Given the user is on the login page
    When the user enters a valid email address
    And the user enters an invalid password
    And the user clicks the login button
    Then the user should see an error message "Invalid email or password"
    And the user should remain on the login page

  Scenario: Unsuccessful login with empty email field
    Given the user is on the login page
    When the user leaves the email field empty
    And the user enters a valid password
    And the user clicks the login button
    Then the user should see an error message "Email is required"
    And the user should remain on the login page

  Scenario: Unsuccessful login with empty password field
    Given the user is on the login page
    When the user enters a valid email address
    And the user leaves the password field empty
    And the user clicks the login button
    Then the user should see an error message "Password is required"
    And the user should remain on the login page

  Scenario: Unsuccessful login with both fields empty
    Given the user is on the login page
    When the user leaves the email field empty
    And the user leaves the password field empty
    And the user clicks the login button
    Then the user should see an error message "Email is required"
    And the user should see an error message "Password is required"
    And the user should remain on the login page

  Scenario: Account locked after multiple failed login attempts
    Given the user is on the login page
    And the user has failed to log in 4 times
    When the user enters a valid email address
    And the user enters an invalid password
    And the user clicks the login button
    Then the user should see an error message "Account locked. Please try again in 30 minutes"
    And the user should remain on the login page

  Scenario: Login with email in different case
    Given the user is on the login page
    When the user enters a valid email address in uppercase
    And the user enters a valid password
    And the user clicks the login button
    Then the user should be redirected to the dashboard
    And the user should see their personalized content

  Scenario: Login with leading and trailing spaces in email
    Given the user is on the login page
    When the user enters a valid email address with leading and trailing spaces
    And the user enters a valid password
    And the user clicks the login button
    Then the user should be redirected to the dashboard
    And the user should see their personalized content

  Scenario: Login with inactive account
    Given the user is on the login page
    And the user account is inactive
    When the user enters a valid email address
    And the user enters a valid password
    And the user clicks the login button
    Then the user should see an error message "Your account is inactive. Please contact support"
    And the user should remain on the login page

  Scenario: Login session persists after page refresh
    Given the user is logged in
    When the user refreshes the page
    Then the user should remain logged in
    And the user should see their personalized content

  Scenario: Password field masks input
    Given the user is on the login page
    When the user enters a password
    Then the password field should mask the input

  Scenario: Login with SQL injection attempt in email field
    Given the user is on the login page
    When the user enters "admin'--" in the email field
    And the user enters any password
    And the user clicks the login button
    Then the user should see an error message "Invalid email or password"
    And the user should remain on the login page

  Scenario: Login with XSS attempt in email field
    Given the user is on the login page
    When the user enters "<script>alert('xss')</script>" in the email field
    And the user enters any password
    And the user clicks the login button
    Then the user should see an error message "Invalid email or password"
    And the user should remain on the login page

  Scenario: Login redirects to originally requested page
    Given the user attempted to access the profile page without being logged in
    And the user was redirected to the login page
    When the user enters a valid email address
    And the user enters a valid password
    And the user clicks the login button
    Then the user should be redirected to the profile page

  Scenario: Login with remember me option selected
    Given the user is on the login page
    When the user enters a valid email address
    And the user enters a valid password
    And the user selects the remember me checkbox
    And the user clicks the login button
    Then the user should be redirected to the dashboard
    And the user session should persist for 30 days

  Scenario: Login with expired password
    Given the user is on the login page
    And the user password has expired
    When the user enters a valid email address
    And the user enters a valid password
    And the user clicks the login button
    Then the user should be redirected to the password reset page
    And the user should see a message "Your password has expired. Please create a new password"

  Scenario: Login with unverified email address
    Given the user is on the login page
    And the user email address is not verified
    When the user enters a valid email address
    And the user enters a valid password
    And the user clicks the login button
    Then the user should see an error message "Please verify your email address before logging in"
    And the user should see an option to resend verification email

  Scenario: Login using keyboard navigation
    Given the user is on the login page
    When the user navigates to the email field using tab
    And the user enters a valid email address
    And the user navigates to the password field using tab
    And the user enters a valid password
    And the user presses enter
    Then the user should be redirected to the dashboard

  Scenario: Login with maximum length email and password
    Given the user is on the login page
    When the user enters an email address with 254 characters
    And the user enters a password with 128 characters
    And the user clicks the login button
    Then the system should process the login attempt
```