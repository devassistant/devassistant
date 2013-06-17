class ClException(BaseException):
    def __init__(self, command, returncode, output):
        self.command = command
        self.returncode = returncode
        self.output = output

    def __str__(self):
        return self.output

class ExecutionException(BaseException):
    pass

class DependencyException(ExecutionException):
    pass

class RunException(ExecutionException):
    pass
