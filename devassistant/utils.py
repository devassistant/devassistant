import os
import platform
import sys
import yaml
try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

try:  # ugly hack for using imp instead of importlib on Python <= 2.6
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


def cl_string_for_da_eval(section, context=None):
    if context is None:
        context = {}
    # filter variables that we don't want to pass from context
    unwanted = ['__assistant__', '__section__']
    ctxt_to_dump = dict(filter(lambda i: i[0] not in unwanted, context.items()))

    dumped = yaml.dump({'ctxt': ctxt_to_dump, 'run': section}, stream=None, Dumper=Dumper)
    dumped_in_heredoc = '\n'.join(['\VERY_LONG_RANDOM_EOF', dumped, 'VERY_LONG_RANDOM_EOF'])

    cl_string = ' '.join([sys.executable,
                          '-m devassistant.cli.cli_runner',
                          'eval - <<',
                          dumped_in_heredoc])
    return cl_string
