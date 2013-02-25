#!/usr/bin/env python
import argparse
import itertools
import os
import sys

import yaml

from devassistant import settings
from devassistant import yaml_loader

# this would definitely welcome some refactoring...
class YamlAssistantChecker(object):
    yaml_dir = os.path.join('devassistant', yaml_loader.YamlLoader.yaml_dir)
    action_types = ['log', 'cl']
    # it may not be completely obvious what this does ;)
    # since itertools have permutations and combinations, but not variations, this simulates varations of letters 'fi' (prepended with 'cl')
    # the last map actually creates the variations, the reduce concatenates the resulting list and the first map prepends them with 'cl'
    # sweet, isn't it?
    action_types += map(lambda x: 'cl' + ''.join(x), reduce(lambda x, y: x + y, map(lambda x: list(itertools.permutations('fi', x)), range(1, 3))))

    @classmethod
    def check_assistants(cls, yaml_files_list):
        loaded_assistants = {}
        # no files specified => check all
        if not yaml_files_list:
            yaml_files_list = filter(lambda x: x.endswith('.yaml'), os.listdir(cls.yaml_dir))
        # relative paths => may be in current dir or in devassistant/assistants/yaml/
        for f in filter(lambda x: not x.startswith('/'), yaml_files_list):
            if os.path.exists(os.path.abspath(f)):
                yaml_files_list[yaml_files_list.index(f)] = os.path.abspath(f)
            else:
                yaml_files_list[yaml_files_list.index(f)] = os.path.join(cls.yaml_dir, f)

        loaded_yamls = {}
        for a in yaml_files_list:
            with open(a) as stream:
                loaded_yamls[a] = yaml.load(stream)

        results = {}
        for fname, assistant_yaml in loaded_yamls.items():
            results[fname] = cls.check_yaml(fname, assistant_yaml)

        return results

    @classmethod
    def check_yaml(cls, fname, assistant_yaml):
        results = []
        name, attrs = assistant_yaml.popitem()
        # one assistant per file
        if len(assistant_yaml):
            results.append(('ERROR', 'More than one assistant in file {0}, checking only {1}'.format(fname, name)))

        # names checking
        if name != os.path.basename(fname).split('.')[0]:
            results.append(('ERROR', 'Assistant and file containing it should have then same name. ({0} != {1})'.format(name, fname)))
        if not 'fullname' in attrs:
            results.append(('WARNING', 'Fullname attribute is not specified.'))

        # arguments
        args = attrs.get('args', {})
        for arg_name, arg_params in args.items():
            # just to be sure nothing breaks, we shouldn't name arguments using settings.SUBASSISTANT_PREFIX
            if arg_name.startswith(settings.SUBASSISTANT_PREFIX):
                results.append(('WARNING', 'Arguments shouldn\'t be named using string {0}'.format(settings.SUBASSISTANT_PREFIX)))
            # argument must have at least one flag
            if 'flags' not in arg_params or not arg_params['flags']:
                results.append(('ERROR', 'Argument {0} must have at least one flag'.format(arg_name)))
            # warn if no help
            if 'help' not in arg_params:
                results.append(('WARNING', 'No help for argument {0}'.format(arg_name)))

        # logging
        lgs = attrs.get('logging', [])
        for lg in lgs:
            lg_type, lg_list = lg.popitem()
            # check supported logging destination types
            if lg_type not in ['file']: # TODO: don't hardcode, refactor this to settings or somewhere else appropriate
                results.append(('WARNING', 'Unknow logging destination {0}, will be ignored'.format(lg_type)))
            # check that lg_list is actually list :)
            if not isinstance(lg_list, list):
                results.append(('ERROR', 'Logging entry must be a list, not {0}'.format(type(dep_list).__name__)))
            else:
                if len(lg_list) != 2:
                    results.append(('ERROR', 'Logging entry must have 2 items, not {0}'.format(len(lg_list))))
                if lg_list[0].lower() not in ['debug', 'info', 'warning', 'error']:
                    results.append(('ERROR', 'Unknown logging level {0}'.format(lg_list[0])))

        # dependencies
        deps = attrs.get('dependencies', [])
        for dep in deps:
            dep_type, dep_list = dep.popitem()
            # check supported dependency types
            if dep_type not in ['rpm']: # TODO: don't hardcode, refactor this to settings or somewhere else appropriate
                results.append(('WARNING', 'Unknow dependency type {0}, will be ignored'.format(dep_type)))
            # check that dep_list is actually list :)
            if not isinstance(dep_list, list):
                results.append(('ERROR', 'Dependencies must be a list, not {0}'.format(type(dep_list).__name__)))

        # check fail_if section
        fail_if = attrs.get('fail_if', [])
        for act in fail_if:
            action_type, action = act.popitem()
            # check supported actions
            if action_type not in cls.action_types: # TODO don't hardcode...
                results.append(('WARNING', 'Unknown action type {0} in section fail_if, will be skipped'.format(action_type)))

        # check all run_* sections
        run_sections = filter(lambda x: x.startswith('run'), attrs.keys())
        # should have "run" section
        if not 'run' in run_sections:
            results.append(('WARNING', 'No default run section'))
        for rs in run_sections:
            comm_sequence = attrs.get(rs)
            for act in comm_sequence:
                action_type, action = act.popitem()
                # check supported actions
                if action_type not in cls.action_types: # TODO don't hardcode...
                    results.append(('WARNING', 'Unknown action type {0} in section {1}, will be skipped'.format(action_type, rs)))
                # if it is non-default run_* section, check that there is an argument that triggers it
                if rs.startswith('run_') and rs[4:] not in args:
                    results.append(('WARNING', 'Section {0} doesn\'t have an argument that would trigger its running'.format(rs)))

        # files
        files = attrs.get('files', {})
        for filename, file_dict in files.items():
            # each file must specify its source
            if 'source' not in file_dict:
                results.append(('ERROR', 'File {0} doesn\'t specify its source'.format(filename)))

        return results

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('yaml_file', nargs='*', default=[])

    args = parser.parse_args()
    results = YamlAssistantChecker.check_assistants(args.yaml_file)
    cli_res = 0
    for fname, res in results.items():
        if res:
            print('\n{0}:'.format(fname))
            for r in res:
                if r[0] == 'ERROR':
                    cli_res = 1
                print '{0}: {1}'.format(*r)

    sys.exit(cli_res)
