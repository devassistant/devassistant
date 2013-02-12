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
        self.chainx = [(MainA(),
                         [(PythonA(),
                             [(DjangoA(), []),
                              (FlaskA(), [])
                             ]
                          ),
                          (RubyA(),
                              [(RailsA(),
                                  [(CrazyA(), [])]
                               )
                              ]
                          )
                         ]
                      )
                     ]
        self.ag = argparse_generator.ArgparseGenerator
    
    def test_generate_parser_one_assistant(self):
        parser = self.ag.generate_argument_parser(self.crazy_chain)
        assert parser.parse_args([])
