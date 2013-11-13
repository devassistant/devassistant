import os

from devassistant import settings
from devassistant import yaml_loader
import yaml
from devassistant import utils
from devassistant import command_helpers

class HandlingProjects(object):

    def __init__(self, project_cache=settings.PROJECTS_CACHE_FILE):
        self.project_cache = project_cache
        if os.path.exists(self.project_cache):
            self.cache = yaml_loader.YamlLoader.load_yaml_by_path(project_cache) or {}
        else:
            if not os.path.exists(os.path.dirname(project_cache)):
                os.makedirs(os.path.dirname(project_cache))
            self.cache={}


    def save_project_info(self, kwargs):
        # TODO save project as YAML file into ~/.devassistant/.cache.projects
        path = []
        i = 0
        while settings.SUBASSISTANT_N_STRING.format(i) in kwargs:
            path.append(kwargs[settings.SUBASSISTANT_N_STRING.format(i)].title())
            # delete the dict member so that we don't write it out with other kwargs again
            del kwargs[settings.SUBASSISTANT_N_STRING.format(i)]
            i += 1

        if path and path[0] in settings.ASSISTANT_ROLES:
            path = path[1:]

        # we will only write original cli/gui args, other kwargs are "private" for this run
        if 'basename' in kwargs:
            basename = kwargs['basename']
        if 'dirname' in kwargs:
            dirname = kwargs['dirname']
        dirname = os.path.abspath(dirname)+"/"+basename
        self.cache[self.convert_to_utf_8(dirname)]={'name': self.convert_to_utf_8(basename),
            'subassistant_path': path
        }
        self.save_project_file()

    def convert_to_utf_8(self, text):
        return text.encode('utf-8')

    def save_project_file(self):
        f = open(self.project_cache, 'w')
        yaml.dump(self.cache, stream=f, default_flow_style=False)
        f.close()

    def list_projects_cli(self, **kwargs):
        if not self.cache:
            print 'No project currently handled by DevAssistant available'
            return False
        else:
            if len(self.cache) == 1:
                max_name = len(self.cache.values()[0].get('name'))+4
                max_type = len(self.cache.values()[0].get('subassistant_path',"Not provided"))+4
                max_path = len(self.cache.keys()[0])+4
            else:
                max_name = max(*map(lambda x: len(x.get('name')), self.cache.itervalues()))+4
                max_type = max(*map(lambda x: len(x.get('subassistant_path',"Not provided")), self.cache.itervalues()))+4
                max_path = max(*map(lambda x: len(x), self.cache.iterkeys()))+4
            max_act = max(*map(lambda x: len(' '.join(x)), ['Project exists', 'Project does not exists']))+4
            print '{0}{1}{2}{3}\n'.format("Name".ljust(max_name),"Type".ljust(max_type),"Path".ljust(max_path),"Project active".ljust(max_act))
            for k, v in sorted(self.cache.iteritems(), key=lambda x: x[1].get('name')):
                type=v.get('subassistant_path',"Not provided")
                print '{name}{type}{path}{active}'.format(
                    name=v.get('name').ljust(max_name),
                    type="Not provided".ljust(max_type) if not type else type[0].ljust(max_type),
                    path=k.ljust(max_path),
                    active="Project exists" if os.path.exists(k) else "Project does not exists"
                    )

    def list_projects_gui(self):
        return self.cache

    def delete_project(self, **kwargs):
        full_path = kwargs.get('path')
        if not full_path.startswith('/'):
            print 'Project full path is needed to delete'
            return False
        if not os.path.exists(full_path):
            print 'Project path {0} does not exists. Will be just deleted from project cache'.format(full_path)
            del self.cache[full_path]
            self.save_project_file()
            return False
        cli = command_helpers.CliDialogHelper()
        if not cli.ask_for_confirm_with_message(message="Do you want to really delete the project {0}".format(full_path), prompt="Confirm:"):
            return False
        try:
            import shutil
            shutil.rmtree(full_path)
        except ImportError:
            pass

        del self.cache[full_path]
        self.save_project_file()

