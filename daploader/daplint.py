from optparse import OptionParser
import sys
from daploader import *


def daplint():
    '''This parses command line arguments and let the user run daplint'''
    parser = OptionParser(usage='usage: %prog [options] dap_file [dap_file2...]', version='%prog 0.0.1')
    parser.add_option('-n', '--no-network', action='store_false', dest='network',
                      default=True, help='don\'t perform checks that require Internet connection')
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

if __name__ == '__main__':
    exit(daplint())
