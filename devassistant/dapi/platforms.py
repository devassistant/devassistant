import platform


def get_platforms_set():
    '''Returns set of all possible platforms'''
    # arch and mageia are not in Py2 _supported_dists, so we add them manually
    # Ubuntu adds itself to the list on Ubuntu
    platforms = set([x.lower() for x in platform._supported_dists])
    platforms |= set(['darwin', 'arch', 'mageia', 'ubuntu'])
    return platforms


def get_platforms_list():
    '''Returns sorted list of all possible platforms'''
    return sorted(get_platforms_set())


def match(p):
    '''Returns True if given platform field is correct.
    It's named match() to mimic a compiled regexp.'''
    return p in get_platforms_set()
