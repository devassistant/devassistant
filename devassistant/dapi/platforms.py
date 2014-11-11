import platform

def match(p):
    '''Returns True if given platform field is correct.
    It's named match() to mimic a compiled regexp.'''
    # arch and mageia are not in Py2 _supported_dists, so we add them manually
    platforms = [x.lower() for x in platform._supported_dists] + ['darwin', 'arch', 'mageia']
    return p in platforms
