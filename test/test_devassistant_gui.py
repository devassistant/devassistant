import os
import pytest
from devassistant.gui import run_gui


class TestDevAssistantGUI(object):
    """
    Test class for running DevAssistant GUI
    """
    def test_environment_display(self):
        """
        test for detection wrong environment DISPLAY variable
        """
        display = os.environ.get('DISPLAY', None)
        if display:
            os.environ['DISPLAY'] = ""

        with pytest.raises(SystemExit):
            run_gui()

        if display:
            os.environ['DISPLAY'] = display
