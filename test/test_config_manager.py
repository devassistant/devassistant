import os
from devassistant.config_manager import ConfigManager
from devassistant import settings

class TestConfigManager(object):

    def setup_class(cls):
        settings.CONFIG_FILE = "./config_test"

    def test_create_config(self):
        assert not os.path.isfile(settings.CONFIG_FILE)
        # Create new ConfigManager. It should have no config.
        cm = ConfigManager()
        assert not cm.config_dict
        # Attempt to load non-existent config file. It should have no config.
        cm.load_configuration_file()
        assert not cm.config_dict
        # Now set some configuration
        cm.set_config_value("somekey", "somevalue")
        assert cm.get_config_value("somekey") == "somevalue"
        cm.set_config_value("somebool", True)
        assert cm.get_config_value("somebool") == "True"
        cm.set_config_value("aaa", True)
        cm.set_config_value("aaa", False)
        assert cm.get_config_value("aaa") == None
        cm.set_config_value("aaa", True)
        assert cm.get_config_value("aaa") == "True"
        cm.set_config_value("aaa", "bbb")
        assert cm.get_config_value("aaa") == "bbb"
        cm.set_config_value("aaa", False)
        assert cm.get_config_value("aaa") == None
        # Set config values with '=' or '\' inside key or value
        cm.set_config_value("bad=key", "badvalue")
        cm.set_config_value("other\\bad=key", "bad=val\\=ue")
        # Finally save configuration file. Check the saved config file.
        cm.save_configuration_file()
        assert os.path.isfile(settings.CONFIG_FILE)
        lines = open(settings.CONFIG_FILE, 'r').read().splitlines()
        assert len(lines) == 4
        assert "somekey=somevalue" in lines
        assert "somebool=True" in lines
        assert "bad\\=key=badvalue" in lines
        assert "other\\\\bad\\=key=bad\\=val\\\\\\=ue" in lines

    def test_load_config(self):
        # Create new ConfigManager. It should have no config.
        cm = ConfigManager()
        assert not cm.config_dict
        # Load config file. It should have all config.
        cm.load_configuration_file()
        assert len(cm.config_dict) == 4
        assert cm.get_config_value("somekey") == "somevalue"
        assert cm.get_config_value("somebool") == "True"
        assert cm.get_config_value("bad=key") == "badvalue"
        assert cm.get_config_value("other\\bad=key") == "bad=val\\=ue"
        assert cm.get_config_value("nonexistent") == None
        assert not cm.config_changed
        # Try to set same config values.
        cm.set_config_value("somekey", "somevalue")
        assert not cm.config_changed
        cm.set_config_value("somebool", True)
        assert not cm.config_changed
        # Try to set different config values.
        cm.set_config_value("somekey", "othervalue")
        assert cm.config_changed

    def teardown_class(cls):
        if os.path.isfile(settings.CONFIG_FILE):
            os.remove(settings.CONFIG_FILE)

