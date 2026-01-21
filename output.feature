Feature: Password Reset
  As a registered user
  I want to reset my password
  So that I can regain access to my account

  Scenario: Successful password reset request with valid email
    Given I am on the password reset page
    When I enter a valid registered email address
    And I submit the password reset request
    Then I should see a confirmation message
    And I should receive a password reset email

  Scenario: Successful password reset with valid token
    Given I have received a password reset email
    When I click the password reset link
    And I enter a new valid password
    And I confirm the new password
    And I submit the new password
    Then my password should be updated
    And I should see a success message

  Scenario: Password reset request with unregistered email
    Given I am on the password reset page
    When I enter an email address that is not registered
    And I submit the password reset request
    Then I should see an error message indicating the email is not found

  Scenario: Password reset request with invalid email format
    Given I am on the password reset page
    When I enter an invalid email format
    And I submit the password reset request
    Then I should see an error message indicating invalid email format

  Scenario: Password reset with expired token
    Given I have a password reset link with an expired token
    When I click the password reset link
    Then I should see an error message indicating the link has expired
    And I should be prompted to request a new password reset

  Scenario: Password reset with already used token
    Given I have already used a password reset link
    When I click the same password reset link again
    Then I should see an error message indicating the link is no longer valid

  Scenario: Password reset with mismatched passwords
    Given I am on the password reset form
    When I enter a new password
    And I enter a different password in the confirmation field
    And I submit the new password
    Then I should see an error message indicating passwords do not match

  Scenario: Password reset with password not meeting requirements
    Given I am on the password reset form
    When I enter a password that does not meet security requirements
    And I confirm the password
    And I submit the new password
    Then I should see an error message indicating password requirements

  Scenario: Password reset request with empty email field
    Given I am on the password reset page
    When I leave the email field empty
    And I submit the password reset request
    Then I should see an error message indicating email is required
