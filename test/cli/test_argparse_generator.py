from devassistant.cli import argparse_generator

from test.fake_assistants import *

class TestArgparseGenerator(object):
    def setup_method(self, method):
        self.crazy_chain = (CrazyA(), [])
        self.rails_chain = (RailsA(), [self.crazy_chain])
        self.ruby_chain = (RubyA(), [self.rails_chain])
        self.flask_chain = (FlaskA(), [])
        self.django_chain = (DjangoA(), [])
        self.python_chain = (PythonA(), [self.flask_chain, self.django_chain])
        self.chain = (MainA(), [self.ruby_chain, self.python_chain])

        self.ag = argparse_generator.ArgparseGenerator

    def test_generate_argument_parser_one_level(self):
        parser = self.ag.generate_argument_parser(self.crazy_chain)
        assert parser.parse_args([])

    def test_generate_argument_parser_multiple_levels(self):
        parser = self.ag.generate_argument_parser(self.chain)
        assert parser.parse_args(['python', 'django'])
        assert parser.parse_args(['ruby', 'rails', 'crazy'])
        # can't test something that doesn't get parsed, because argparse would sys.exit :(
