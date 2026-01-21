Feature: Access Compliance Dashboard - Alliant Admin
  As an Alliant Admin
  I want to click on the Compliance Dashboard module
  So that I can navigate to the Compliance Dashboard to manage company requirements

  Scenario: Login as Alliant Admin and verify Compliance Dashboard module visibility
    Given I am on the login page at https://fleetlytics-test.pages.dev/
    When I enter "alliant@admin.com" in the email field
    And I enter "Welcome2eox!" in the password field
    And I click the login button
    Then I should be redirected to the home page
    And I should see the Compliance Dashboard module
    And the Compliance Dashboard module should display the title "Compliance Dashboard"

  Scenario: Navigate to Compliance Dashboard and view Companies list
    Given I am on the login page at https://fleetlytics-test.pages.dev/
    When I enter "alliant@admin.com" in the email field
    And I enter "Welcome2eox!" in the password field
    And I click the login button
    Then I should be on the home page
    When I click on the Compliance Dashboard module
    Then I should be navigated to the Companies list view
    And I should see a list of companies

  Scenario: Verify Companies list contains company records
    Given I am on the login page at https://fleetlytics-test.pages.dev/
    When I enter "alliant@admin.com" in the email field
    And I enter "Welcome2eox!" in the password field
    And I click the login button
    And I click on the Compliance Dashboard module
    Then I should see the Companies list view
    And the companies list should contain at least one company record
