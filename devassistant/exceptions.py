class ClException(BaseException):
    def __init__(self, command, returncode, stdout, stderr):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return self.stderr

class ExecutionException(BaseException):
    pass

class DependencyException(ExecutionException):
    pass

class RunException(ExecutionException):
    pass
