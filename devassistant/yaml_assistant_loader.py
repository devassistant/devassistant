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
    # mapping of assistant names to assistant instances
    _assistants = {}

    @classmethod
    def get_top_level_assistants(cls, roles=['creator', 'modifier', 'preparer']):
        assistants = cls.get_all_assistants()
        are_subassistants = set()
        for a in assistants:
            are_subassistants.update(a._subassistant_names)
        top_level = filter(lambda x: x.name not in are_subassistants, assistants)
        return list(filter(lambda x: x.role in roles, top_level))

    @classmethod
    def get_all_assistants(cls):
        if not cls._assistants:
            parsed_yamls = yaml_loader.YamlLoader.load_all_yamls(cls.assistants_dirs)

            for s, y in parsed_yamls.items():
                new_as = cls.assistant_from_yaml(s, y)
                cls._assistants[new_as.name] = new_as

            # handle _superassistant_name fields
            have_super = filter(lambda a: a._superassistant_name is not None, cls._assistants.values())
            for assistant in have_super:
                cls._assistants[assistant._superassistant_name]._subassistant_names.append(assistant.name)

            for assistant in cls._assistants.values():
                # set subassistants of assistant according to names in _subassistant_names
                assistant._subassistants = [cls._assistants[n] for n in assistant._subassistant_names]

        return list(cls._assistants.values())

    @classmethod
    def assistant_from_yaml(cls, source, y):
        assistant = yaml_assistant.YamlAssistant()
        # assume only one key and value
        name, attrs = y.popitem()

        # arguments that we need to create cli parser/gui
        assistant.name = name
        assistant.fullname = attrs.get('fullname', '')
        assistant.description = attrs.get('description', '')
        assistant.role = attrs.get('role', 'creator')
        assistant.args = cls._args_from_struct(assistant, attrs.get('args', {}))
        assistant.source_file = source

        # arguments that are only needed at runtime
        assistant._template_dir = attrs.get('template_dir', yaml_loader.YamlLoader._default_template_dir_for(source))
        assistant._files = attrs.get('files', {})
        assistant._subassistant_names = attrs.get('subassistants', [])
        assistant._superassistant_name = attrs.get('superassistant', None)
        assistant._logging = attrs.get('logging', [])
        assistant._dependencies = attrs.get('dependencies', [])
        # handle more dependencies* and run* sections
        for k, v in attrs.items():
            if k.startswith('run') or k.startswith('dependencies'):
                setattr(assistant, '_{0}'.format(k), v)
        assistant._pre_run = attrs.get('pre_run', [])
        assistant._post_run = attrs.get('post_run', [])

        return assistant

    @classmethod
    def _args_from_struct(cls, assistant, struct):
        args = []
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
            args.append(arg)
        return args
