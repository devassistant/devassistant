import os

from devassistant import argument
from devassistant import exceptions
from devassistant.logger import logger
from devassistant import yaml_loader
from devassistant import yaml_snippet_loader
from devassistant import settings
from devassistant.assistants import yaml_assistant

class YamlAssistantLoader(object):
    assistants_dirs = list(map(lambda x: os.path.join(x, 'assistants'), settings.DATA_DIRECTORIES))
    _assistants = []

    @classmethod
    def get_top_level_assistants(cls, roles=['creator', 'modifier', 'preparer']):
        assistants = cls.get_all_assistants()
        are_subassistants = set()
        for a in assistants:
            if a._subassistant_names:
                are_subassistants.update(a._subassistant_names)
        top_level = filter(lambda x: x.name not in are_subassistants, assistants)
        return list(filter(lambda x: x.role in roles, top_level))

    @classmethod
    def get_all_assistants(cls):
        if not cls._assistants:
            parsed_yamls = yaml_loader.YamlLoader.load_all_yamls(cls.assistants_dirs)

            for s, y in parsed_yamls.items():
                cls._assistants.append(cls.assistant_from_yaml(s, y))
                cls._assistants[-1]._source_file = s

            for sa in cls._assistants:
                if hasattr(sa, '_subassistant_names'):
                    # get subassistants of sa assistant
                    sa._subassistants = list(filter(lambda x: x.name in sa._subassistant_names, cls._assistants))

        return cls._assistants

    @classmethod
    def assistant_from_yaml(cls, source, y):
        assistant = yaml_assistant.YamlAssistant()
        # assume only one key and value
        name, attrs = y.popitem()

        # arguments that we can handle right away
        assistant.name = name
        assistant.fullname = attrs.get('fullname', '')
        assistant.description = attrs.get('description', '')
        assistant.role = attrs.get('role', 'creator')
        assistant.template_dir = attrs.get('template_dir', yaml_loader.YamlLoader._default_template_dir_for(source))
        # cli arguments
        cls._args_from_struct(assistant, attrs.get('args', {}))

        # arguments that will be handled by YamlAssistant methods
        assistant._files = attrs.get('files', {})
        assistant._subassistant_names = attrs.get('subassistants', [])
        assistant._logging = attrs.get('logging', [])
        assistant._dependencies = attrs.get('dependencies', [])
        # handle more dependencies* and run* sections
        for k, v in attrs.items():
            if k.startswith('run') or k.startswith('dependencies'):
                setattr(assistant, '_{0}'.format(k), v)
        assistant.pre_run = attrs.get('pre_run', [])
        assistant.post_run = attrs.get('post_run', [])

        return assistant

    @classmethod
    def _args_from_struct(cls, assistant, struct):
        assistant.args = []
        for arg_name, arg_params in struct.items():
            use_snippet = arg_params.pop('snippet', None)
            if use_snippet:
                # if snippet is used, take this parameter from snippet and update
                # it with current arg_params, if any
                try:
                    problem = None
                    snippet = yaml_snippet_loader.YamlSnippetLoader.get_snippet_by_name(use_snippet)
                    arg_params = dict(snippet.args.pop(arg_name), **arg_params)
                except exceptions.SnippetNotFoundException as e:
                    problem = 'Couldn\'t expand argument {arg} in assistant {a}: ' + str(e)
                except KeyError as e: # snippet doesn't have the requested argument
                    problem = 'Couldn\'t find argument {arg} in snippet {snip} wanted by assistant {a}.'

                if problem:
                    logger.warning(problem.format(snip=use_snippet,
                                                  arg=arg_name,
                                                  a=assistant.name))
                    continue

                # this works much like snippet.args.pop(arg_name).update(arg_params),
                # but unlike it, this actually returns the updated dict

            arg = argument.Argument(*arg_params.pop('flags'), **arg_params)
            assistant.args.append(arg)
