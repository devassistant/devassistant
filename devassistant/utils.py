import platform

try: # ugly hack for using imp instead of importlib on Python <= 2.6
    import importlib
except ImportError:
    import imp as importlib
    def import_module(name):
        fp, pathname, description = importlib.find_module(name.replace('.', '/'))
        return importlib.load_module(name, fp, pathname, description)
    importlib.import_module = import_module
    del import_module

def import_module(module):
    return importlib.import_module(module)

def u(string):
    try:
        return unicode(string)
    except:
        return string

# ok, if we need one more compat thingie, we _will_ start using six :)
def get_distro_name():
    return platform.linux_distribution()[0].lower()
