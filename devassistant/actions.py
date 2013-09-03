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

    def __eq__(self, other):
        return self.name.__eq__(other.name)

@register_action
class HelpAction(Action):
    name = 'help'
    description = 'Prints out detailed help'

    @classmethod
    def run(cls, **kwargs):
        print cls.get_help()

    @classmethod
    def get_help(cls):
        text = ["""You can either run assistants with:
da {crt,mod,prep} [subassistant [arguments]] ...

Where:
crt - used for creating new projects
mod - used for modifying existing projects
prep - used for preparing environment for upstream projects and various tasks

Or you can run a custom action:"""]
        for action_name, action in sorted(actions.items()):
            text.append('{name} - {desc}'.format(name=action_name, desc=action.description))
        return '\n'.join(text)
