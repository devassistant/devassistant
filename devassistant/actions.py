actions = {}

def register_action(action):
    actions[action.name] = action
    return action

class Action(object):
    name = 'action'
    description = 'Action description'
    args = []

    def run(self, **kwargs):
        raise NotImplementedError()

@register_action
class HelpAction(Action):
    name = 'help'
    description = 'Print detailed help'

    @classmethod
    def run(cls, **kwargs):
        print(cls.get_help())

    @classmethod
    def get_help(cls, with_ascii_format=True):
        # we will justify the action names (and assistant types) to the same width
        just = max(len('crt'), len('mod'), len('prep'), *map(lambda x: len(x), actions)) + 2
        text = ['You can either run assistants with:']
        text.append(cls.format_text('da {crt,mod,prep} [ASSISTANT [ARGUMENTS]] ...',
                                    'bold',
                                    with_ascii_format))
        text.append('')
        text.append('Where:')
        text.append(cls.format_action_line('crt',
                                           'used for creating new projects',
                                           just,
                                           with_ascii_format))
        text.append(cls.format_action_line('mod',
                                           'used for modifying existing projects',
                                           just,
                                           with_ascii_format))
        text.append(cls.format_action_line('prep',
                                           'used for preparing environment for upstream projects and various tasks',
                                            just,
                                            with_ascii_format))
        text.append('')
        text.append('Or you can run a custom action:')
        for action_name, action in sorted(actions.items()):
            text.append(cls.format_action_line(action_name,
                                               action.description,
                                               just,
                                               with_ascii_format))
        return '\n'.join(text)

    @classmethod
    def format_text(cls, text, format, with_ascii_format):
        if with_ascii_format:
            if format == 'bold':
                text = '\033[1m' + text + '\033[0m'
        return text

    @classmethod
    def format_action_line(cls, action_name, action_desc, just, with_ascii_format):
        text = []
        justed_name = action_name.ljust(just)
        text.append(cls.format_text(justed_name, 'bold', with_ascii_format))
        text.append(action_desc)
        return ''.join(text)

@register_action
class VersionAction(Action):
    name = 'version'
    description = 'Print version'

    @classmethod
    def run(cls, **kwargs):
        from devassistant.version import VERSION
        print('DevAssistant {version}'.format(version=VERSION))
