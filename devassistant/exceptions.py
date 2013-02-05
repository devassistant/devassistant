class ExecutionException(BaseException):
    pass

class DependencyException(ExecutionException):
    pass

class RunException(ExecutionException):
    pass
