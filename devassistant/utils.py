import os
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
    distro = platform.linux_distribution()[0].lower()
    if not distro and os.path.exists('/etc/os-release'):
        with open('/etc/os-release') as osrel:
            for l in osrel.readlines():
                if l.startswith('ID'):
                    distro = l.split('=')[-1].strip()
    return distro

def get_assistant_attrs_from_dict(d, source):
    # In pre-0.9.0, we required assistant to be a mapping of {name: assistant_attributes}
    # now we allow that, but we also allow omitting the assistant name and putting
    # the attributes to top_level, too.
    # TODO: remove this when we obsolete the old way, perhaps in 0.9.0 final
    name = os.path.splitext(os.path.basename(source))[0]
    if isinstance(d, dict):
        if len(d) == 1 and name in d:
            return d[name]
        else:
            return d
    else:
        return None
