Feature: SauceDemo Login
  As a user
  I want to log in to SauceDemo
  So that I can access the product catalog

  Scenario: Successful login with valid credentials
    Given I am on the SauceDemo login page at https://www.saucedemo.com
    When I enter username "standard_user" in the username field
    And I enter password "secret_sauce" in the password field
    And I click the Login button
    Then I should be redirected to the products page
    And I should see the page title "Products"

  Scenario: Failed login with invalid credentials
    Given I am on the SauceDemo login page at https://www.saucedemo.com
    When I enter username "invalid_user" in the username field
    And I enter password "wrong_password" in the password field
    And I click the Login button
    Then I should see an error message indicating invalid credentials
