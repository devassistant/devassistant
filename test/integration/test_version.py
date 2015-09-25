import pytest

from devassistant import __version__

from test.integration.misc import run_da


class TestVersion(object):
    def test_version(self):
        res = run_da('version')
        assert res.stdout == 'INFO: DevAssistant {0}\n'.format(__version__)
