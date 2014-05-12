from optparse import OptionParser
import sys
from . import *


def lint():
    '''This parses command line arguments and let the user run daplint'''
    parser = OptionParser(usage='usage: %prog [options] dap_file [dap_file2...]')
    parser.add_option('-n', '--network', action='store_true', dest='network',
                      default=False, help='perform checks that require Internet connection')
    options, args = parser.parse_args()
    exitcode = 0
    if not args:
        parser.error('No dap specified')
    for dap in args:
        try:
            d = Dap(dap)
            if not d.check(network=options.network):
                exitcode += 1
        except (DapFileError, DapMetaError) as e:
            sys.stderr.write(str(e) + '\n')
            exitcode += 1
    return exitcode
