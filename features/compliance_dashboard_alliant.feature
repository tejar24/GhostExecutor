Feature: Access Compliance Dashboard - Alliant Admin
  As an Alliant Admin
  I want to click on the Compliance Dashboard module
  So that I can navigate to the Compliance Dashboard to manage company requirements

  Background:
    Given I navigate to the application at https://fleetlytics-test.pages.dev/
    When I enter email "alliant@admin.com" in the email input field
    And I enter password "Welcome2eox!" in the password input field
    And I click the Login button
    Then I should be logged in and see the home page

  Scenario: Compliance Dashboard module is visible on home page for Alliant Admin
    Given I am on the home page as Alliant Admin
    Then I should see the Compliance Dashboard module on the home page
    And the module should display the title "Compliance Dashboard"

  Scenario: Navigate to Compliance Dashboard Companies list view
    Given I am on the home page as Alliant Admin
    When I click on the Compliance Dashboard module
    Then I should be navigated to the Compliance Dashboard Companies list view
    And I should see the companies list

  Scenario: Companies list view displays all company records
    Given I am on the home page as Alliant Admin
    When I click on the Compliance Dashboard module
    Then I should see the Companies list view
    And the list should contain records of companies
    And each company record should be visible in the list

  Scenario: Compliance Dashboard module not visible for unauthorized users
    Given I navigate to the application at https://fleetlytics-test.pages.dev/
    When I login with a non-admin user account
    Then I should not see the Compliance Dashboard module on the home page

  Scenario: Direct URL access denied for unauthorized users
    Given I am logged in as a non-admin user
    When I attempt to access the Compliance Dashboard URL directly
    Then I should be denied access or redirected to an error page
