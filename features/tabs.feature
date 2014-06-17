Feature: Tabs switching

  Scenario: "Create Project" tab is default
    Given da-gui has just started
    # TODO: is "is the current tab" vs. "assistant should" the right way to say this in BDD?
     Then "Create Project" is the current tab
      and "Creator 1" assistant should be listed


  Scenario: Tab switching works
    Given da-gui is running
     When user clicks "Modify Project" tab
     Then "Modify Project" is the current tab
      and "Modifier 1" assistant should be listed
     When user clicks "Prepare Environment" tab
     Then "Preparer 1" assistant should be listed
     When user clicks "Custom Task" tab
     Then "Task 1" assistant should be listed
