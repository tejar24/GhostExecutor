Feature: Edit Compliance Record

  Scenario: Navigate to Edit Compliance Record form using pencil icon
    Given I am on the Fleetlytics login page at https://fleetlytics-test.pages.dev/
    When I enter "Mg@trucking.com" in the email input field
    And I enter "Welcome2eox!" in the password input field
    And I click the Sign In button
    And I wait for 3 seconds for the page to load
    Then I should see the Home page
    Then I should click on Compliance tile
    When I click on the Edit pencil icon button for the first row in the compliance records table
    Then I should see the compliance record edit form
    And the form fields should be pre-filled with existing data
    And I should click on 'Next' button
    And I should click on 'Next' button
    And I should click on 'Next' button
    And I should click on 'Submit' button