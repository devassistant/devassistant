class NoCheck(object):
    '''Class that mimics a compiled regexp, so it can be used instead'''
    def match(self, anything):
        '''This always matches'''
        return True
