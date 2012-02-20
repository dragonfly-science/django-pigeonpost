Feature: Getting messages
    In order to know what is going on
    As a subscriber
    I get an email when a post is published

    Scenario: Simple email
        Given I am subscribed
        When a post is published
        Then I get an email

