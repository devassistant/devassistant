import pytest
import itertools
import os

from test import fixtures_dir
from test.integration.misc import run_da


DAP = os.path.join(fixtures_dir, 'dapi', 'daps', 'integration', 'integration-1.0.dap')


class TestRunAssistants(object):
    @pytest.mark.parametrize(('assistant', 'word', 'store'),
                             itertools.product(('crt', 'twk', 'prep', 'extra'),
                                               ('foo', ''),
                                               (True, False)))
    def test_run_assistant(self, assistant, word, store):
        res = run_da('pkg install ' + DAP)

        ex = not bool(word)
        opt = ' -w ' + word if word else ''
        if store:
            opt += ' --store'

        res = res.run_da(assistant + ' integration' + opt, expect_error=ex, expect_stderr=ex)

        if ex:
            assert '-w/--word' in res.stderr
        else:
            assert res.stdout == 'INFO: Word: {0}\nINFO: Store was {1}\n'.format(word, store)
