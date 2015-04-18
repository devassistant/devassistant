import pytest
import os

from test import fixtures_dir
from test.integration.misc import run_da


DAP = os.path.join(fixtures_dir, 'dapi', 'daps', 'integration', 'integration-1.0.dap')


class TestPkgLint(object):
    def test_pkg_lint(self):
        res = run_da('pkg lint ' + DAP, expect_error=True)
        outlines = res.stdout.rstrip().split('\n')

        assert len(outlines) == 3

        warning = 'WARNING: integration-1.0.dap: Missing icon for assistant {0}/integration'
        assert warning.format('extra') in outlines
        assert warning.format('prep') in outlines
        assert warning.format('twk') in outlines

        assert warning.format('crt') not in outlines

    def test_pkg_lint_nowarn(self):
        res = run_da('pkg lint -w ' + DAP)
        assert not res.stdout
