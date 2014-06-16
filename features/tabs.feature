Feature: Tabs switching

  Scenario: "Create Project" tab is default
    Given da-gui has just started
     Then "Create Project" is the current tab
