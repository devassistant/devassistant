import os
import sys
import six
import pytest
from flexmock import flexmock
from devassistant import settings

settings.CONFIG_FILE = '/dev/null'

from devassistant.config_manager import ConfigManager

test_lines = ["somekey=somevalue", "somebool=True", "bad\\=key=badvalue", "other\\\\bad\\=key=bad\\=val\\\\\\=ue"]
test_filename = '/tmp/cmconfigfile'

class FakeLogger(object):

    def __init__(self):
        self.contents = []

    def warning(self, text):
        self.contents.append(text)

class FakeFileObject(object):

    def __init__(self, contents):
        self.contents = contents
        self.i = 0;

    def next(self):
        if self.i < len(self.contents):
            self.i = self.i + 1
            return self.contents[self.i - 1]
        raise StopIteration

    def __next__(self):
        return self.next()

    def __iter__(self):
        return self

    def write(self, line):
        self.contents.append(line.rstrip('\n'))

    def __enter__(self):
        return self

    def __exit__(self, a, b, c):
        pass

class TestConfigManager(object):

    def override_open(self, mode, contents):
        fake_file_object = FakeFileObject(contents)
        mock = flexmock(six.moves.builtins)
        mock.should_call('open')
        mock.should_receive('open').with_args('/dev/null', mode).and_return(fake_file_object)
        return fake_file_object

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
        cm = ConfigManager()
        cm.set_config_value(key, setvalue)
        if resetvalue is not None:
            cm.set_config_value(key, resetvalue)
        assert cm.get_config_value(key) == getvalue

    def test_save_correct_values(self):
        cm = ConfigManager()
        fake_write_object = self.override_open('w', [])
        # Set some normal config values
        cm.set_config_value("somekey", "somevalue")
        cm.set_config_value("somebool", True)
        # Set config values with '=' or '\' inside key or value
        cm.set_config_value("bad=key", "badvalue")
        cm.set_config_value("other\\bad=key", "bad=val\\=ue")
        # Finally save configuration file. Check the saved config file.
        cm.save_configuration_file()
        lines = fake_write_object.contents
        assert len(lines) == 4
        assert "somekey=somevalue" in lines
        assert "somebool=True" in lines
        assert "bad\\=key=badvalue" in lines
        assert "other\\\\bad\\=key=bad\\=val\\\\\\=ue" in lines

    def test_save_file_exists(self):
        # Check if ConfigManager creates physical file
        cm = ConfigManager()
        cm.config_file = test_filename
        cm.set_config_value("somekey", "somevalue")
        cm.set_config_value("somebool", True)
        cm.save_configuration_file()
        assert(os.path.exists(test_filename))
        assert(os.path.getsize(test_filename)) == 32

    def test_load_nonexistent_file(self):
        # Create new ConfigManager. It should have no config.
        logger = FakeLogger()
        cm = ConfigManager()
        cm.logger = logger
        cm.config_file = test_filename
        assert not cm.config_dict
        # Attempt to load nonexistent config file. It should have no config and no error was logged.
        cm.load_configuration_file()
        assert not cm.config_dict
        assert len(logger.contents) == 0

    def test_load_file(self):
        # Load config file. It should have all config.
        cm = ConfigManager()
        self.override_open('r', test_lines)
        cm.load_configuration_file()
        assert len(cm.config_dict) == 4

    @pytest.mark.parametrize(('key', 'getvalue'), [
        ("somekey",        "somevalue"),
        ("somebool",       "True"),
        ("bad=key",        "badvalue"),
        ("other\\bad=key", "bad=val\\=ue"),
        ("nonexistent",     None)
    ])
    def test_loaded_values(self, key, getvalue):
        # Check if configuration loaded from file is correct
        cm = ConfigManager()
        self.override_open('r', test_lines)
        cm.load_configuration_file()
        assert cm.get_config_value(key) == getvalue

    @pytest.mark.parametrize(('contents'), [
        (["somekey=somevalue", "malformedline", "next=line"]),
        (["somekey=somevalue", "mal=formed=line", "next=line"])
    ])
    def test_load_malformed_file(self, contents):
        # Try to load malformed file. It should fail.
        logger = FakeLogger()
        cm = ConfigManager()
        cm.logger = logger
        self.override_open('r', contents)
        cm.load_configuration_file()
        assert not cm.config_dict
        assert len(logger.contents) == 1
        assert "Malformed configuration file" in logger.contents[0]
    
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
        cm = ConfigManager()
        self.override_open('r', test_lines)
        cm.load_configuration_file()
        if key:
            cm.set_config_value(key, setvalue)
        assert cm.config_changed == result

    def setup_method(self, method):
        if os.path.exists(test_filename):
            os.remove(test_filename)

