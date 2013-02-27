import logging
import os
import string

import plumbum
import getpass
import git

from devassistant import assistant_base
from devassistant import exceptions
from devassistant import settings
from devassistant.command_helpers import ClHelper, RPMHelper, YUMHelper, PathHelper
from devassistant.logger import logger

class YamlAssistant(assistant_base.AssistantBase):
    _dependencies = {}

    _fail_if = []
    _run = []

    def logging(self, **kwargs):
        for l in self._logging:
            handler_type, l_list = l.popitem()
            if handler_type == 'file':
                level, lfile = l_list
                expanded_lfile = self._format(lfile, **kwargs)
                # make dirs, create logger
                if not os.path.exists(os.path.dirname(expanded_lfile)):
                    os.makedirs(os.path.dirname(expanded_lfile))
                # add handler and formatter
                handler = logging.FileHandler(expanded_lfile, 'a+')
                formatter = logging.Formatter('%(asctime)-15s %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                handler.setLevel(getattr(logging, level.upper()))
                # register handler with the global logger
                logger.addHandler(handler)
            else:
                logger.warning('Unknown logger type {0}, ignoring.'.format(handler_type))

    def errors(self, **kwargs):
        errors = []

        for command_dict in self._fail_if:
            for comm_type, comm in command_dict.items():
                if comm_type.startswith('cl'):
                    try:
                        a = self._format(comm, **kwargs)
                        self._format_and_run_cl_command(comm_type, comm, **kwargs)
                        # command succeeded -> error
                        errors.append('Cannot proceed because command returned 0: {0}'.format(a))
                    except exceptions.RunException:
                        pass # everything ok, go on
                elif comm_type == 'log':
                    self._log(comm, **kwargs)
                else:
                    logger.warning('Unkown action type {0}, skipping.'.format(comm_type))

        return errors

    def dependencies(self, **kwargs):
        for sect in self._dependencies:
            condition, section = sect.popitem()
            if condition == 'default' or kwargs.get(condition[1:], False):
                self._dependencies_section(section)

    def _dependencies_section(self, section, **kwargs):
        for dep in section:
            dep_type, dep_list = dep.popitem()
            # rpm dependencies (can't handle anything else yet)
            if dep_type == 'rpm':
                to_install = []
                for dep in dep_list:
                        if dep.startswith('@'):
                            if not YUMHelper.is_group_installed(dep):
                                to_install.append(dep)
                        else:
                            if not RPMHelper.is_rpm_installed(dep):
                                to_install.append(dep)
                if to_install:
                    YUMHelper.install(*to_install)
            else:
                logger.warning('Unkown dependency type {0}, skipping.'.format(dep_type))

    def run(self, **kwargs):
        # determine which run* section to invoke
        to_run = self._run
        for method in dir(self):
            if method.startswith('_run_'):
                parameter = method.split('_', 2)[-1]
                if kwargs.get(parameter, False):
                    to_run = getattr(self, method)

        self._run_one_section(to_run, **kwargs)


    def _run_one_section(self, section, **kwargs):
        skip_else = False

        for i, command_dict in enumerate(section):
            for comm_type, comm in command_dict.items():
                if comm_type.startswith('cl'):
                    self._format_and_run_cl_command(comm_type, comm, **kwargs)
                elif comm_type == 'log':
                    self._log(comm, **kwargs)
                elif comm_type == 'github':
                    self.git_hub_registration(comm, **kwargs)
                elif comm_type.startswith('if'):
                    if self._evaluate_condition(comm_type[2:].strip(), **kwargs):
                        self._run_one_section(comm)
                    else:
                        # look if next comm_type is else, if so, execute it
                        if len(section) > i + 1:
                            next_section_dict = section[i + 1]
                            next_section_comm_type, next_section_comm = next_section_dict.items()[0]
                            if next_section_comm_type == 'else':
                                self._run_one_section(next_section_comm, **kwargs)
                elif comm_type == 'else':
                    # else on its own means error, otherwise ok
                    if not section[i - 1].items()[0][0].startswith('if'):
                        logger.warning('Yaml error: encountered "else" with no associated "if", skipping.')
                else:
                    logger.warning('Unkown action type {0}, skipping.'.format(comm_type))

    def _evaluate_condition(self, condition, **kwargs):
        result = True
        invert_result = False
        cond = condition.strip()
        if cond.startswith('not '):
            invert_result = True
            cond = cond[4:]

        if cond.startswith('_'):
            if cond[1:] in kwargs and kwargs[cond[1:]]:
                result = True
            else:
                result = False
        else:
            try:
                c = self._format_and_run_cl_command('cl', cond, **kwargs)
                result = True
            except exceptions.RunException:
                result = False
        return result != invert_result # != is basically xor

    def _format_and_run_cl_command(self, command_type, command, **kwargs):
        c = self._format(command, **kwargs)
        fg = False
        i = False
        if 'f' in command_type:
            fg = True
        if 'i' in command_type:
            i = True
        try:
            result = ClHelper.run_command(c, fg, i)
        except plumbum.ProcessExecutionError as e:
            raise exceptions.RunException(e)

        return result

    def _log(self, log_action, **kwargs):
        # make level lowercase
        log_action = (log_action[0].upper(), log_action[1])
        if log_action[0] in logging._levelNames:
            logger.log(logging._levelNames[log_action[0]], self._format(log_action[1], **kwargs))
        else:
            logger.warning('Unknow logging level {0}, with message {1}'.format(*log_action))

    def _format(self, comm, **kwargs):
        # If command is false/true in yaml file, it gets coverted to False/True
        # which is bool object => convert
        if isinstance(comm, bool):
            comm = str(comm).lower()

        new_comm = []
        if not isinstance(comm, list):
            parts_list = comm.split()
        else:
            parts_list = comm

        # replace parts that match something from _files (can be either name
        # if "&" didn't expand in yaml; or the dict if "&" did expand)
        for c in parts_list:
            if isinstance(c, dict):
                # TODO: raise a proper error if c['source'] is not present
                new_comm.append(os.path.join(self.template_dir, c['source']))
            elif c.startswith('*'):
                c_file = c[1:].strip('{}')
                if c_file in self._files:
                    new_comm.append(os.path.join(self.template_dir, self._files[c_file]['source']))
                else:
                    new_comm.append(c)
            else:
                new_comm.append(c)

        new_comm = ' '.join(new_comm)

        # substitute cli arguments for their values
        return string.Template(new_comm).safe_substitute(kwargs)

    def git_hub_registration(self, comm, **kwargs):
        logger.info("Check whether repository is existing")
        gitname = kwargs['name']
        print "{0}.git".format(gitname)
        if PathHelper.path_exists('{0}/.git'.format(gitname)) == False:
            logger.info("Repository is not existing. Creating newer one")
            repo = git.Repo.init("{0}".format(gitname))
            repo.config_writer()
            untracked = repo.untracked_files
            logger.info(repo.git.status())
            for f in untracked:
                repo.git.add(f)
            repo.git.commit(m=comm[0])
            logger.info(repo.git.status())
            username = getpass.getuser()
            plumbum.local.cwd.chdir(kwargs['name'])
            remote_string = "https://github.com/{0}/{1}".format(username,gitname)
            ClHelper.run_command("git remote add origin {0}".format(remote_string),fg=True,log_as_info=True)
            ClHelper.run_command("git push -u origin master",True,True)
        else:
            logger.info("Repository is already existing")
