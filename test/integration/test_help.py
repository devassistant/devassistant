from __future__ import unicode_literals
import sys

import pytest

from test.integration.misc import populate_dapath, run_da

class TestHelp(object):
    top_level_help = '\n'.join([
        'You can either run assistants with:',
        '\033[1mda [--debug] {create,tweak,prepare,extras} [ASSISTANT [ARGUMENTS]] ...\033[0m',
        '',
        'Where:',
        '\033[1mcreate   \033[0mused for creating new projects',
        '\033[1mtweak    \033[0mused for working with existing projects',
        '\033[1mprepare  \033[0mused for preparing environment for upstream projects',
        '\033[1mextras   \033[0mused for performing custom tasks not related to a specific project',
        'You can shorten "create" to "crt", "tweak" to "twk" and "extras" to "extra".',
        '',
        'Or you can run a custom action:',
        '\033[1mda [--debug] [ACTION] [ARGUMENTS]\033[0m',
        '',
        'Available actions:',
        '\033[1mdoc      \033[0mDisplay documentation for a DAP package.',
        '\033[1mhelp     \033[0mPrint detailed help.',
        '\033[1mpkg      \033[0mLets you interact with online DAPI service and your local DAP packages.',
        '\033[1mversion  \033[0mPrint version',
        ''])

    no_assistant_help_newlines = '\n'.join([
        'No subassistants available.',
        '',
        'To search DevAssistant Package Index (DAPI) for new assistants,',
        'you can either browse https://dapi.devassistant.org/ or run',
        '',
        '"da pkg search <term>".',
        '',
        'Then you can run',
        '',
        '"da pkg install <DAP-name>"',
        '',
        'to install the desired DevAssistant package (DAP).'
    ])

    no_assistants_help_singleline = '\n'.join([
        '  No subassistants available. To search DevAssistant Package Index (DAPI)',
        '  for new assistants, you can either browse https://dapi.devassistant.org/',
        '  or run "da pkg search <term>". Then you can run "da pkg install <DAP-',
        '  name>" to install the desired DevAssistant package (DAP).'
    ])

    @pytest.mark.parametrize('h', [
        '--help',
        '-h',
        'help',
    ])
    def test_top_level_help(self, h):
        res = run_da(h)
        # use repr because of bash formatting chars
        assert repr(res.stdout) == repr(self.top_level_help)

    def test_top_level_without_arguments(self):
        res = run_da('', expect_error=True)
        msg = 'Couldn\'t parse input, displaying help ...\n\n'
        # use repr because of bash formatting chars
        assert repr(res.stdout) == repr(msg + self.top_level_help)

    @pytest.mark.parametrize('alias', [
        # test both assistant primary name and an alias
        'crt',
        'create',
    ])
    def test_category_with_no_assistants_without_arguments(self, alias):
        res = run_da(alias, expect_error=True, expect_stderr=True)
        assert self.no_assistant_help_newlines in res.stderr

    @pytest.mark.parametrize('alias', [
        # test both assistant primary name and an alias
        'crt',
        'create',
    ])
    def test_category_with_no_assistants_help(self, alias):
        res = run_da(alias + ' -h')
        assert self.no_assistants_help_singleline in res.stdout

    def test_didnt_choose_subassistant(self):
        env = populate_dapath({'assistants': {'crt': ['a.yaml', {'a': ['b.yaml']}]}})
        res = env.run_da('create a', expect_error=True, expect_stderr=True)
        assert 'You have to select a subassistant' in res.stderr

    def test_subassistants_help(self):
        env = populate_dapath({'assistants': {'crt': ['a.yaml', {'a': ['b.yaml']}]}})
        res = env.run_da('create a -h')
        assert res.stdout == '\n'.join([
            'usage: create a [-h] {b} ...',
            '',
            'optional arguments:',
            '  -h, --help  show this help message and exit',
            '',
            'subassistants:',
            '  Following subassistants will help you with setting up your project.',
            '',
            '  {b}',
            ''])

    def test_didnt_choose_subaction(self):
        res = run_da('pkg', expect_error=True, expect_stderr=True)
        assert 'You have to select a subaction' in res.stderr

    def test_subactions_help(self):
        res = run_da('pkg -h')
        # TODO: seems that subparsers order cannot be influenced in 2.6
        #  investigate and possibly improve this test
        if sys.version_info[:2] == (2, 6):
            return
        assert res.stdout == '\n'.join([
            'usage:  pkg [-h] {info,install,lint,list,remove,search,uninstall,update} ...',
            '',
            'Lets you interact with online DAPI service and your local DAP packages.',
            '',
            'optional arguments:',
            '  -h, --help            show this help message and exit',
            '',
            'subactions:',
            '  This action has following subactions.',
            '',
            '  {info,install,lint,list,remove,search,uninstall,update}',
            ''])
