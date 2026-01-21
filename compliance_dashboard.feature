```gherkin
Feature: Access Compliance Dashboard - Alliant Admin
  As an Alliant Admin
  I want to click on the Compliance Dashboard module
  So that I can navigate to the Compliance Dashboard to manage company requirements

  Scenario: Compliance Dashboard module is visible on home page for Alliant Admin
    Given I am logged in as an Alliant Admin
    When I navigate to the home page
    Then I should see the Compliance Dashboard module

  Scenario: Compliance Dashboard module displays correct title
    Given I am logged in as an Alliant Admin
    And I am on the home page
    When I view the Compliance Dashboard module
    Then the module should display the title "Compliance Dashboard"

  Scenario: Alliant Admin navigates to Companies list view by clicking Compliance Dashboard
    Given I am logged in as an Alliant Admin
    And I am on the home page
    When I click on the Compliance Dashboard module
    Then I should be navigated to the Compliance Dashboard Companies list view

  Scenario: Companies list view displays all company records
    Given I am logged in as an Alliant Admin
    And I have clicked on the Compliance Dashboard module
    When the Companies list view is displayed
    Then I should see records of all companies

  Scenario: Claims Advocate can set compliance requirements for companies
    Given I am logged in as a Claims Advocate
    And I am on the Compliance Dashboard Companies list view
    When I select a company
    Then I should be able to set compliance requirements for that company

  Scenario: Compliance Dashboard module is not visible for unauthorized roles
    Given I am logged in as a user without Alliant Admin role
    When I navigate to the home page
    Then I should not see the Compliance Dashboard module

  Scenario: User without access cannot navigate to Compliance Dashboard directly
    Given I am logged in as a user without dashboard access permissions
    When I attempt to access the Compliance Dashboard URL directly
    Then I should be denied access to the Compliance Dashboard

  Scenario: Companies list view displays empty state when no companies exist
    Given I am logged in as an Alliant Admin
    And no companies exist in the system
    When I click on the Compliance Dashboard module
    Then I should see an empty Companies list view with appropriate messaging

  Scenario: Alliant Admin can view Companies list with large number of records
    Given I am logged in as an Alliant Admin
    And there are more than 1000 companies in the system
    When I click on the Compliance Dashboard module
    Then the Companies list view should load successfully
    And I should be able to navigate through all company records
```