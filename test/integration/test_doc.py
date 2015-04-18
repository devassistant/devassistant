import pytest
import os

from test import fixtures_dir
from test.integration.misc import run_da


DAP = os.path.join(fixtures_dir, 'dapi', 'daps', 'integration', 'integration-1.0.dap')


class TestDoc(object):
    def test_doc(self):
        res = run_da('pkg install ' + DAP)
        res = res.run_da('doc integration')

        assert res.stdout == '''INFO: DAP integration has these docs:
INFO: README
INFO: Use "da doc integration <DOC>" to see a specific document
'''

        res = res.run_da('doc integration README')
        assert res.stdout == 'This is README\n'
