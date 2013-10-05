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
