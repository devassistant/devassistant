import pytest

from devassistant.assistant_base import AssistantBase
from devassistant import settings

class MainA(AssistantBase):
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

class TestAssistantBase(object):
    def map_sa_to_names(self, sa_list):
        # maps part of chain (list of two-tuples) to names of the top assistants
        # so that I don't have to write it again and again
        return map(lambda x: x[0].name, sa_list)

    def get_sa_from_tuple_list(self, name, sa_list):
        # returns tuple of assistant with given name from list of tuples (part of chain)
        return filter(lambda x: x[0].name == name, sa_list)[0]

    def args_dict_from_names(self, names):
        args_dict = {}
        for i, n in enumerate(names):
            args_dict[settings.SUBASSISTANT_N_STRING.format(i)] = n
        return args_dict

    def test_get_subassistant_chain_constructs_proper_structure(self):
        ch = MainA().get_subassistant_chain()
        main, subas = ch
        assert main.name == MainA.name
        assert len(subas) == 2

        python = self.get_sa_from_tuple_list('python', subas)
        ruby = self.get_sa_from_tuple_list('ruby', subas)

        assert len(python[1]) == 2
        assert self.get_sa_from_tuple_list('django', python[1])
        assert self.get_sa_from_tuple_list('flask', python[1])

        assert len(ruby[1]) == 1
        rails = self.get_sa_from_tuple_list('rails', ruby[1])
        assert len(rails[1]) == 1
        assert self.get_sa_from_tuple_list('crazy', rails[1])

    def test_get_selected_subassistant_path_for_leaf(self):
        path_names = ['ruby', 'rails', 'crazy']
        args_dict = self.args_dict_from_names(path_names)

        path = MainA().get_selected_subassistant_path(**args_dict)
        path_names = ['main'] + path_names
        for i, p in enumerate(path):
            assert p.name == path_names[i]

    def test_get_selected_subassistant_path_for_non_leaf(self):
        path_names = ['ruby', 'rails']
        args_dict = self.args_dict_from_names(path_names)

        path = MainA().get_selected_subassistant_path(**args_dict)
        path_names = ['main'] + path_names
        for i, p in enumerate(path):
            assert p.name == path_names[i]

    def test_is_run_as_leaf(self):
        path_names = ['python', 'django']
        args_dict = self.args_dict_from_names(path_names)

        path = MainA().get_selected_subassistant_path(**args_dict)
        for i in range(0, len(path) - 1):
            assert path[i].is_run_as_leaf(**args_dict) == False
        assert path[-1].is_run_as_leaf(**args_dict) == True
