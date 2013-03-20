#!/usr/bin/env python

import os

import flask
from flask.ext.script import Manager, Command, Option

from NAME import app
from NAME import db

class CreateDBCommand(Command):
    'Create DB and tables'
    def run(self, alembic_ini=None):
        if flask.current_app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            # strip sqlite:///
            datadir_name = os.path.dirname(flask.current_app.config['SQLALCHEMY_DATABASE_URI'][len('sqlite:///'):])
            if not os.path.exists(datadir_name):
                os.makedirs(datadir_name)
        db.create_all()
            
class DropDBCommand(Command):
    'Drop DB tables'
    def run(self):
        db.drop_all()

manager = Manager(app)
manager.add_command('create_db', CreateDBCommand())
manager.add_command('drop_db', DropDBCommand())

if __name__ == '__main__':
    manager.run()
