import os
import sys
import six
import re
import pytest
import tempfile
from flexmock import flexmock

from devassistant.config_manager import ConfigManager

class TestConfigManager(object):

    def create_tempfile(self, contents):
        tmp = tempfile.NamedTemporaryFile(mode='w', delete=False)
        for line in contents:
            tmp.write(line + '\n')
        self.tmpfile = tmp.name
        return tmp.name

    def setup_method(self, method):
        self.cm = ConfigManager()
        self.cm.config_file = '/foo/bar'
        self.test_lines = ["somekey=somevalue", "somebool=True", "bad\\=key=badvalue", "other\\\\bad\\=key=bad\\=val\\\\\\=ue"]
        self.tmpfile = None

    def teardown_method(self, method):
        if self.tmpfile and os.path.exists(self.tmpfile):
            os.remove(self.tmpfile)

    @pytest.mark.parametrize(('key', 'setvalue', 'resetvalue', 'getvalue'), [
        ("somekey",  "somevalue",  None,  "somevalue"),
        ("somebool",  True,        None,  "True"),
        ("aaa",       True,        False,  None ),
        ("aaa",       True,       "bbb",  "bbb" ),
        ("aaa",       False,       None,   None ),
        ("aaa",      "bbb",        True,  "True"),
        ("aaa",      "bbb",        False,  None )
    ])
    def test_set_get_config_values(self, key, setvalue, resetvalue, getvalue):
        # Check if ConfigManager returns correct values
        self.cm.set_config_value(key, setvalue)
        if resetvalue is not None:
            self.cm.set_config_value(key, resetvalue)
        assert self.cm.get_config_value(key) == getvalue

    def test_save_correct_values(self):
        # Set some normal config values
        self.cm.set_config_value("somekey", "somevalue")
        self.cm.set_config_value("somebool", True)
        # Set config values with '=' or '\' inside key or value
        self.cm.set_config_value("bad=key", "badvalue")
        self.cm.set_config_value("other\\bad=key", "bad=val\\=ue")
        # Create fake file object which should receive 'write's with given contents
        wrt = flexmock(write=lambda l: True)
        wrt.should_call('write').with_args("somekey=somevalue\n").once()
        wrt.should_call('write').with_args("somebool=True\n").once()
        wrt.should_call('write').with_args("bad\\=key=badvalue\n").once()
        wrt.should_call('write').with_args("other\\\\bad\\=key=bad\\=val\\\\\\=ue\n").once()
        # Override open() to return fake file object and os.path.exists() to return True
        flexmock(six.moves.builtins).should_receive('open').with_args('/foo/bar', 'w').and_return(wrt).once()
        flexmock(os.path).should_receive('exists').and_return(True)
        # Finally save configuration file
        self.cm.save_configuration_file()

    def test_load_nonexistent_file(self):
        self.cm.logger = flexmock()
        self.cm.logger.should_receive("warning").never()
        flexmock(os.path).should_receive('exists').with_args('/foo/bar').and_return(False)
        # Attempt to load nonexistent config file. It should have no config and no error was logged.
        self.cm.load_configuration_file()
        assert not self.cm.config_dict

    def test_load_error(self):
        self.cm.logger = flexmock()
        self.cm.logger.should_receive("warning").with_args(re.compile('^Could not load configuration file')).once()
        flexmock(six.moves.builtins).should_receive('open').with_args('/foo/bar', 'r').and_raise(IOError)
        flexmock(os.path).should_receive('exists').with_args('/foo/bar').and_return(True)
        # Attempt to load config file which cannot be read. It should have no config and error was logged.
        self.cm.load_configuration_file()
        assert not self.cm.config_dict

    def test_save_error(self):
        self.cm.logger = flexmock()
        self.cm.logger.should_receive("warning").with_args(re.compile('^Could not save configuration file')).once()
        flexmock(six.moves.builtins).should_receive('open').with_args('/foo/bar', 'w').and_raise(IOError)
        flexmock(os.path).should_receive('exists').with_args('/foo/bar').and_return(False)
        flexmock(os.path).should_receive('exists').with_args('/foo').and_return(True)
        # Attempt to save config file which cannot be written. Error should be logged.
        self.cm.save_configuration_file()

    def test_load_file(self):
        # Load config file. It should have all config.
        self.cm.config_file = self.create_tempfile(self.test_lines)
        self.cm.load_configuration_file()
        assert len(self.cm.config_dict) == 4

    @pytest.mark.parametrize(('key', 'getvalue'), [
        ("somekey",        "somevalue"),
        ("somebool",       "True"),
        ("bad=key",        "badvalue"),
        ("other\\bad=key", "bad=val\\=ue"),
        ("nonexistent",     None)
    ])
    def test_loaded_values(self, key, getvalue):
        # Check if configuration loaded from file is correct
        self.cm.config_file = self.create_tempfile(self.test_lines)
        self.cm.load_configuration_file()
        assert self.cm.get_config_value(key) == getvalue

    @pytest.mark.parametrize(('contents'), [
        (["somekey=somevalue", "malformedline", "next=line"]),
        (["somekey=somevalue", "mal=formed=line", "next=line"])
    ])
    def test_load_malformed_file(self, contents):
        # Try to load malformed file. It should fail.
        self.cm.config_file = self.create_tempfile(contents)
        self.cm.logger = flexmock()
        self.cm.logger.should_receive("warning").with_args(re.compile('^Malformed configuration file')).once()
        self.cm.load_configuration_file()
        assert not self.cm.config_dict

    @pytest.mark.parametrize(('key', 'setvalue', 'result'), [
        ( None,       None,        False),
        ("empty",     False,       False),
        ("nonempty", "somevalue",  True),
        ("somekey",  "somevalue",  False),
        ("somebool",  True,        False),
        ("somekey",  "othervalue", True)
    ])
    def test_config_changed(self, key, setvalue, result):
        # Check if config_changed property behaves correctly
        self.cm.config_file = self.create_tempfile(self.test_lines)
        self.cm.load_configuration_file()
        if key:
            self.cm.set_config_value(key, setvalue)
        assert self.cm.config_changed == result

