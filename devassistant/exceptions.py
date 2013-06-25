class ExecutionException(BaseException):
    pass

class DependencyException(ExecutionException):
    pass

class RunException(ExecutionException):
    pass

class ClException(RunException):
    def __init__(self, command, returncode, output):
        self.command = command
        self.returncode = returncode
        self.output = output

    def __str__(self):
        return self.output

class AssistantNotFoundException(BaseException):
    pass
