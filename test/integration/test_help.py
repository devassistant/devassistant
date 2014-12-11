from test.integration.misc import run_da

class TestHelp(object):
    def test_top_level_help(self):
        res = run_da('-h')
        # TODO: assert the output, write more tests :)
