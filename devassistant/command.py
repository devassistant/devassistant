from devassistant import exceptions
from devassistant import command_runners

class Command(object):
    def __init__(self, comm_type, input_log_res, input_res, kwargs={}):
        self.comm_type = comm_type
        self.input_log_res = input_log_res
        self.input_res = input_res
        self.files_dir = kwargs.get('__files_dir__', [''])[-1]
        self.files = kwargs.get('__files__', [''])[-1]
        self.kwargs = kwargs

    def run(self):
        for cr in command_runners.command_runners:
            if cr.matches(self):
                return cr.run(self)

        raise exceptions.CommandException('No runner for command "{ct}: {c}".'.\
            format(ct=self.comm_type, c=self.comm))
