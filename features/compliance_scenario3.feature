Feature: Access Compliance Dashboard - Verify Companies List
  As an Alliant Admin
  I want to verify the Companies list contains records

  Scenario: Verify Companies list contains company records
    Given I navigate to https://fleetlytics-test.pages.dev/
    When I enter "alliant@admin.com" in the email input
    And I enter "Welcome2eox!" in the password input
    And I click the Sign In button
    And I wait for 3 seconds for the page to load
    When I click on the element containing "Compliance" text
    And I wait for 2 seconds
    Then I should see a list or table with company data
