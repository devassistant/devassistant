from devassistant import exceptions
from devassistant import utils

class Command(object):
    """A class that represents a Yaml command. It has these members:

    - comm_type: type of command
    - input_log_res: logical result of command input
    - input_res: result of command input
    - kwargs: global context taken at point of execution of this command
    """

    command_runners = None

    @classmethod
    def load_command_runners(cls):
        if not cls.command_runners:
            cls.command_runners = utils.import_module('devassistant.command_runners')
        return cls.command_runners

    def __init__(self, comm_type, input_log_res, input_res, kwargs={}):
        self.comm_type = comm_type
        self.had_exec_flag = False
        if comm_type.endswith('~'):
            self.comm_type = self.comm_type[:-1]
            self.had_exec_flag = True
        self.input_log_res = input_log_res
        self.input_res = input_res
        self.files_dir = kwargs.get('__files_dir__', [''])[-1]
        self.files = kwargs.get('__files__', [''])[-1]
        self.kwargs = kwargs

    def run(self):
        for cr in type(self).load_command_runners().command_runners:
            if cr.matches(self):
                return cr.run(self)

        raise exceptions.CommandException('No runner for command "{ct}: {c}".'.\
            format(ct=self.comm_type, c=self.input_res))
