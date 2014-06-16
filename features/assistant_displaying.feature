Feature: Assistant displaying

  Scenario: Foo creator assistant is loaded with icon
    Given da-gui is running
      and "Create Project" is the current tab
     Then "Foo" assistant should be displayed
     # and "Foo" assistant should have label "Foo is foo!" - TODO: how to test this?
