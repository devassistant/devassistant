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

class SnippetNotFoundException(BaseException):
    pass

class YamlSyntaxError(BaseException):
    pass


class PackageManagerNotOperational(DependencyException):
    """
    this exception should be thrown when  package manager is missing:
    yum, dpkg, rpm etc. This means that we don't how to proceed (this could
    happen in sandbox e.g. virtualenv)
    """
    pass


class PackageManagerUnknown(DependencyException):
    """
    specified package manager is not defined and thus we don't know how
    to install dependencies
    """
    pass
