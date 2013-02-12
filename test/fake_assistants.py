from devassistant import assistant_base

class MainA(assistant_base.AssistantBase):
    name = 'main'
    fullname = 'Main'

    def get_subassistants(self):
        return [PythonA, RubyA]

class PythonA(MainA):
    name = 'python'
    fullname = 'Python'

    def get_subassistants(self):
        return [DjangoA, FlaskA]

class RubyA(MainA):
    name = 'ruby'
    fullname = 'Ruby'

    def get_subassistants(self):
        return [RailsA]

class DjangoA(PythonA):
    name = 'django'
    fullname = 'Django'

    # intentionally no get_subassistants

class FlaskA(PythonA):
    name = 'flask'
    fullname = 'Flask'

    def get_subassistants(self):
        return []

class RailsA(RubyA):
    name = 'rails'
    fullname = 'Rails'

    def get_subassistants(self):
        return [CrazyA]

class CrazyA(RailsA):
    name = 'crazy'
    fullname = 'Crazy'

    def get_subassistants(self):
        return []
