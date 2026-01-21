Feature: Access Compliance Dashboard - Alliant Admin
  As an Alliant Admin
  I want to click on the Compliance Dashboard module
  So that I can navigate to the Compliance Dashboard to manage company requirements

  Scenario: Login as Alliant Admin and access Compliance Dashboard
    Given I navigate to https://fleetlytics-test.pages.dev/
    When I enter "alliant@admin.com" in the email input field
    And I enter "Welcome2eox!" in the password input field
    And I click the Sign In button
    And I wait for 3 seconds for the page to load
    Then I should see the Compliance Dashboard module on the home page
  
