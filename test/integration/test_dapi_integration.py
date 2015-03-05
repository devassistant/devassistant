import pytest
import os

from test import fixtures_dir
from test.integration.misc import run_da


def dap_path(fixture):
    '''Return appropriate dap path'''
    return os.path.join(fixtures_dir, 'dapi', 'daps', fixture)


class TestDAPIIntegration(object):
    @pytest.mark.webtest
    def test_installation_of_nonexistent_package(self):
        res = run_da('pkg install hope_there_is_never_dap_named_like_this', expect_error=True)
        stdout = '\n'.join(['INFO: Installing DAP hope_there_is_never_dap_named_like_this ...',
            'ERROR: DAP hope_there_is_never_dap_named_like_this not found.', ''])
        assert res.stdout == stdout

    @pytest.mark.webtest
    def test_info(self):
        # the actual output can change, so just test that this doesn't fail
        res = run_da('pkg info dap')

    def test_install_local(self):
        res = run_da('pkg install ' + dap_path('meta_only/foo-1.0.0.dap'))
        assert 'INFO: Successfully installed DAPs foo' in res.stdout

    @pytest.mark.webtest
    def test_install_dapi(self):
        res = run_da('pkg install common_args')
        assert 'INFO: Successfully installed DAPs common_args' in res.stdout
