from devassistant import actions

class TestActions(object):
    ha = actions.HelpAction

    def test_get_help_contains_task_keywords(self):
        gh = self.ha.get_help()
        assert 'crt' in gh
        assert 'mod' in gh
        assert 'prep' in gh
        assert 'task' in gh

    def test_get_help_contains_action_name(self):
        a = actions.Action()
        a.name = 'foobar_action_name'
        a.description = 'foobar_action_description'
        actions.register_action(a)

        assert 'foobar_action_name' in self.ha.get_help()
        assert 'foobar_action_description' in self.ha.get_help()

    def test_format_text_returns_original_text_on_bogus_formatting(self):
        assert self.ha.format_text('aaa', 'foo', 'bar') == 'aaa'
        assert self.ha.format_text('', 'foo', 'bar') == ''

    def test_format_text_returns_bold(self):
        assert self.ha.format_text('aaa', 'bold', 'ascii') == '\033[1maaa\033[0m'

    def test_version_action(self, capsys):
        va = actions.VersionAction
        from devassistant import __version__ as VERSION
        va.run()
        assert VERSION in capsys.readouterr()[0]
