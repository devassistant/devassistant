Feature: Complex DevAssistant scenarios

  Scenario: user selects Creator 1, provides just name and runs it
    Given da-gui is running
      and "Create Project" is the current tab
      When user clicks "Creator 1" assistant
      When user fills "/tmp/myproject" in "Project name"
