Feature: Edit Compliance Record - Client Admin
  As a Client Admin
  I want to click on the Edit button (pencil icon) in the list view
  So that I can update compliance record details for my company's drivers/contractors

  Scenario: Navigate to Edit Compliance Record form using pencil icon
    Given I am on the Fleetlytics login page at https://fleetlytics-test.pages.dev/
    When I enter "alliant@admin.com" in the email input field
    And I enter "Welcome2eox!" in the password input field
    And I click the Sign In button
    And I wait for 3 seconds for the page to load
    Then I should see the Compliance Dashboard page
    When I click on the Edit pencil icon button for the first row in the compliance records table
    Then I should see the compliance record edit form
    And the form fields should be pre-filled with existing data

  Scenario: Verify auto-populated fields from Focus are displayed
    Given I am on the Fleetlytics login page at https://fleetlytics-test.pages.dev/
    When I enter "alliant@admin.com" in the email input field
    And I enter "Welcome2eox!" in the password input field
    And I click the Sign In button
    And I wait for 3 seconds for the page to load
    When I click on the Edit pencil icon button for the first row in the compliance records table
    Then I should see the First Name field with a value
    And I should see the Last Name field with a value
    And I should see the Company Name field with a value
    And I should see the Contractor ID field with a value
    And I should see the Email field with a value

  Scenario: Verify Requirements tab is non-editable for Client Admin
    Given I am on the Fleetlytics login page at https://fleetlytics-test.pages.dev/
    When I enter "alliant@admin.com" in the email input field
    And I enter "Welcome2eox!" in the password input field
    And I click the Sign In button
    And I wait for 3 seconds for the page to load
    When I click on the Edit pencil icon button for the first row in the compliance records table
    And I click on the Requirements tab
    Then the input fields in Requirements tab should be disabled

  Scenario: Verify Attachments tab is visible and editable
    Given I am on the Fleetlytics login page at https://fleetlytics-test.pages.dev/
    When I enter "alliant@admin.com" in the email input field
    And I enter "Welcome2eox!" in the password input field
    And I click the Sign In button
    And I wait for 3 seconds for the page to load
    When I click on the Edit pencil icon button for the first row in the compliance records table
    And I click on the Attachments tab
    Then the Attachments tab content should be visible

  Scenario: Verify Save and Cancel buttons are available on edit form
    Given I am on the Fleetlytics login page at https://fleetlytics-test.pages.dev/
    When I enter "alliant@admin.com" in the email input field
    And I enter "Welcome2eox!" in the password input field
    And I click the Sign In button
    And I wait for 3 seconds for the page to load
    When I click on the Edit pencil icon button for the first row in the compliance records table
    Then I should see a Save button
    And I should see a Cancel button

  Scenario: Cancel editing returns to Compliance Dashboard
    Given I am on the Fleetlytics login page at https://fleetlytics-test.pages.dev/
    When I enter "alliant@admin.com" in the email input field
    And I enter "Welcome2eox!" in the password input field
    And I click the Sign In button
    And I wait for 3 seconds for the page to load
    When I click on the Edit pencil icon button for the first row in the compliance records table
    And I click the Cancel button
    Then I should be back on the Compliance Dashboard list view
