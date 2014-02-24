import pytest

from devassistant import exceptions
from devassistant import settings

from test.fake_assistants import *

class TestAssistantBase(object):
    def map_sa_to_names(self, sa_list):
        # maps part of tree (list of two-tuples) to names of the top assistants
        # so that I don't have to write it again and again
        return map(lambda x: x[0].name, sa_list)

    def get_sa_from_tuple_list(self, name, sa_list):
        # returns tuple of assistant with given name from list of tuples (part of tree)
        return list(filter(lambda x: x[0].name == name, sa_list))[0]

    def args_dict_from_names(self, names):
        args_dict = {}
        for i, n in enumerate(names):
            args_dict[settings.SUBASSISTANT_N_STRING.format(i)] = n
        return args_dict

    def test_get_subassistants_returns_empty_list_on_leaves(self):
        ch = FlaskA().get_subassistants()
        assert ch == []

    def test_get_subassistants_returns_correct_instance(self):
        al = RubyA().get_subassistants()
        assert len(al) == 1
        assert isinstance(al[0], RailsA)


    def test_get_subassistant_tree_constructs_proper_structure(self):
        ch = MainA().get_subassistant_tree()
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

    def test_get_selected_subassistant_path_for_non_existing_raises(self):
        path_names = ['nanana']
        args_dict = self.args_dict_from_names(path_names)

        with pytest.raises(exceptions.AssistantNotFoundException):
            MainA().get_selected_subassistant_path(**args_dict)

    def test_is_run_as_leaf(self):
        path_names = ['python', 'django']
        args_dict = self.args_dict_from_names(path_names)

        path = MainA().get_selected_subassistant_path(**args_dict)
        for i in range(0, len(path) - 1):
            assert path[i].is_run_as_leaf(**args_dict) == False
        assert path[-1].is_run_as_leaf(**args_dict) == True
