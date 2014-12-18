import pytest

from test.integration.misc import run_da

class TestDAPIIntegration(object):
    # most of the tests that make sense to write will only be sanely doable
    #  after #316 is fixed, most importantly when dapicli respects DEVASSISTANT_HOME
    #  and we can completely cut it from standard devassistant path
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
