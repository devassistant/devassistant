from devassistant import settings

actions = {}

def register_action(action):
    """Decorator that adds an action class to active actions"""
    actions[action.name] = action
    return action

class Action(object):
    """Superclass of custom actions of devassistant"""

    name = 'action'
    description = 'Action description'
    args = []

    def run(self, **kwargs):
        """Runs this actions, accepts arguments parsed from cli/retrieved from gui.

        Raises:
            devassistant.exceptions.ExecutionExceptions if something goes wrong
        """
        raise NotImplementedError()

@register_action
class HelpAction(Action):
    """Can gather info about all actions and assistant types and print it nicely."""
    name = 'help'
    description = 'Print detailed help'

    @classmethod
    def run(cls, **kwargs):
        """Prints nice help."""
        print(cls.get_help(format_type=kwargs.get('format_type')))

    @classmethod
    def get_help(cls, format_type='ascii'):
        """Constructs and formats help for printing.

        Args:
            format_type: type of formatting for nice output, see format_text for possible values
        """
        # we will justify the action names (and assistant types) to the same width
        just = max(
                max(*map(lambda x: len(x), settings.ASSISTANT_ROLES)),
                max(*map(lambda x: len(x), actions))
               ) + 2
        text = ['You can either run assistants with:']
        text.append(cls.format_text('da [--debug] {crt,mod,prep,task} [ASSISTANT [ARGUMENTS]] ...',
                                    'bold',
                                    format_type))
        text.append('')
        text.append('Where:')
        text.append(cls.format_action_line('crt',
                                           'used for creating new projects',
                                           just,
                                           format_type))
        text.append(cls.format_action_line('mod',
                                           'used for modifying existing projects',
                                           just,
                                           format_type))
        text.append(cls.format_action_line('prep',
                                           'used for preparing environment for upstream projects',
                                            just,
                                            format_type))
        text.append(cls.format_action_line('task',
                                           'used for performing custom tasks not related to a specific project',
                                            just,
                                            format_type))
        text.append('')
        text.append('Or you can run a custom action:')
        text.append(cls.format_text('da [--debug] [ACTION] [ARGUMENTS]',
                                    'bold',
                                    format_type))
        text.append('')
        text.append('Available actions:')
        for action_name, action in sorted(actions.items()):
            text.append(cls.format_action_line(action_name,
                                               action.description,
                                               just,
                                               format_type))
        return '\n'.join(text)

    @classmethod
    def format_text(cls, text, format, format_type):
        """Formats text to have given format in given format_type.

        Args:
            text: text to format
            format: format, e.g. 'bold'
            format_type: None (will do nothing) or 'ascii'
        Returns:
            formatted text
        """
        if format_type == 'ascii':
            if format == 'bold':
                text = '\033[1m' + text + '\033[0m'
        return text

    @classmethod
    def format_action_line(cls, action_name, action_desc, just, format_type):
        """Creates and formats action line from given action_name and action_desc.

        Args:
            action_name: name of action
            action_desc: description of action
            just: columns to justify action_name to
            format_type: formats action_name in bold using this format, see
                         format_text help for available format types
        Returns:
            formatted action line
        """
        text = []
        justed_name = action_name.ljust(just)
        text.append(cls.format_text(justed_name, 'bold', format_type))
        text.append(action_desc)
        return ''.join(text)

@register_action
class VersionAction(Action):
    """Prints DevAssistant version, what else?"""
    name = 'version'
    description = 'Print version'

    @classmethod
    def run(cls, **kwargs):
        from devassistant.version import VERSION
        print('DevAssistant {version}'.format(version=VERSION))
