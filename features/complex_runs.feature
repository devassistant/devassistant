Feature: Complex DevAssistant scenarios

  Scenario: user selects Creator 1, provides just name and runs it
    Given da-gui is running
      and "Create Project" is the current tab
      When user clicks "Creator 1" assistant
      # TODO: check for prefilled default values (@whoami@, @pwd@, defaults)
      When user fills "myproject" in "Project name"
       and user fills "/tmp/" in "Create in"
       and user clicks "Run" button
      When assistant run finishes with "Done"
      Then log window should show
        | output              |
        | make_awesome: True  |
        | yourname: $yourname |
        | somepath: $somepath |
        | "someconst: "       |
