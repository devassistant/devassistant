import os

from devassistant import settings

fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')

settings.CACHE_FILE = os.path.join(fixtures_dir, '.cache.yaml')
settings.DATA_DIRECTORIES = [fixtures_dir]
