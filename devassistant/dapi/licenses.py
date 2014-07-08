import re

# https://fedoraproject.org/w/index.php?title=Licensing:Main&oldid=362524
# Revision as of 18:55, 26 November 2013
# TODO Ask Fedora for API?
VALID_LICENSES = ['AAL', 'ADSL', 'AFL', 'AGPLv1', 'AGPLv3', 'AGPLv3 with exceptions',
                  'AGPLv3+', 'AMDPLPA', 'AML', 'AMPAS BSD', 'APAFML', 'APSL 2.0',
                  'ARL', 'ASL 1.0', 'ASL 1.1', 'ASL 2.0', 'Abstyles', 'Adobe', 'Afmparse',
                  'Artistic 2.0', 'Artistic clarified', 'BSD', 'BSD Protection',
                  'BSD with advertising', 'BSD with attribution', 'Bahyph', 'Barr',
                  'BeOpen', 'Beerware', 'Bibtex', 'BitTorrent', 'Boost', 'Borceux',
                  'CATOSL', 'CC-BY', 'CC-BY-SA', 'CC0', 'CDDL', 'CDL', 'CNRI', 'CPAL',
                  'CPL', 'CeCILL', 'CeCILL-B', 'CeCILL-C', 'Condor', 'Copyright only',
                  'Crossword', 'Crystal Stacker', 'Cube', 'DMIT', 'DOC', 'DSDP', 'Dotseqn',
                  'ECL 1.0', 'ECL 2.0', 'EFL 2.0', 'EPL', 'ERPL', 'EU Datagrid',
                  'EUPL 1.1', 'Entessa', 'Eurosym', 'FBSDDL', 'FSFUL', 'FSFULLR',
                  'FTL', 'Fair', 'GFDL', 'GL2PS', 'GPL+', 'GPL+ or Artistic',
                  'GPL+ with exceptions', 'GPLv1', 'GPLv2', 'GPLv2 or Artistic',
                  'GPLv2 with exceptions', 'GPLv2+', 'GPLv2+ or Artistic',
                  'GPLv2+ with exceptions', 'GPLv3', 'GPLv3 with exceptions', 'GPLv3+',
                  'GPLv3+ with exceptions', 'Giftware', 'Glide', 'Glulxe', 'HaskellReport',
                  'IBM', 'IEEE', 'IJG', 'ISC', 'ImageMagick', 'Imlib2', 'Intel ACPI',
                  'Interbase', 'JPython', 'Jabber', 'JasPer', 'Julius', 'Knuth', 'LBNL BSD',
                  'LDPL', 'LGPLv2', 'LGPLv2 with exceptions', 'LGPLv2+', 'LGPLv2+ or Artistic',
                  'LGPLv2+ with exceptions', 'LGPLv3', 'LGPLv3 with exceptions', 'LGPLv3+',
                  'LGPLv3+ with exceptions', 'LLGPL', 'LOSLA', 'LPL', 'LPPL', 'Latex2e',
                  'Leptonica', 'Lhcyr', 'Logica', 'MIT', 'MIT with advertising',
                  'MITNFA', 'MPLv1.0', 'MPLv1.1', 'MPLv2.0', 'MS-PL', 'MS-RL', 'MTLL',
                  'MakeIndex', 'MirOS', 'Motosoto', 'Mup', 'NCSA', 'NGPL', 'NLPL', 'NOSL',
                  'Naumen', 'NetCDF', 'Netscape', 'Newmat', 'Newsletr', 'Nokia', 'Noweb',
                  'OFSFDL', 'OML', 'OReilly', 'OSL 1.0', 'OSL 1.1', 'OSL 2.0', 'OSL 2.1',
                  'OSL 3.0', 'Open Publication', 'OpenLDAP', 'OpenPBS', 'OpenSSL', 'PHP',
                  'Par', 'Phorum', 'PlainTeX', 'Plexus', 'PostgreSQL', 'Public Domain',
                  'Public Use', 'Python', 'QPL', 'Qhull', 'REX', 'RPSL', 'Rdisc', 'RiceBSD',
                  'Romio', 'Rsfs', 'Ruby', 'SCEA', 'SCRIP', 'SISSL', 'SLIB', 'SNIA', 'SPL',
                  'STMPL', 'SWL', 'Saxpath', 'Sendmail', 'Sequence', 'Sleepycat', 'TCL',
                  'TMate', 'TORQUEv1.1', 'TOSL', 'TPL', 'Teeworlds', 'Threeparttable', 'Tolua',
                  'UCD', 'VNLSL', 'VOSTROM', 'VSL', 'Verbatim', 'Vim', 'W3C', 'WTFPL', 'Webmin',
                  'Wsuipa', 'XSkat', 'Xerox', 'YPLv1.1', 'ZPLv1.0', 'ZPLv2.0', 'ZPLv2.1', 'Zed',
                  'Zend', 'diffmark', 'dvipdfm', 'eCos', 'eGenix', 'gnuplot', 'iMatix',
                  'libtiff', 'mecab-ipadic', 'midnight', 'mod_macro', 'psfrag', 'psutils',
                  'softSurfer', 'wxWidgets', 'xinetd', 'xpp', 'zlib', 'zlib with acknowledgement']

_regex = re.compile('\(([^)]+)\)|\s(?:and|or)\s')


def _split_license(license):
    '''Returns all individual licenses in the input'''
    return (x.strip() for x in (l for l in _regex.split(license) if l))


def match(license):
    '''Returns True if given license field is correct
    Taken from rpmlint.

    It's named match() to mimic a compiled regexp.'''
    if license not in VALID_LICENSES:
        for l1 in _split_license(license):
            if l1 in VALID_LICENSES:
                continue
            for l2 in _split_license(l1):
                if l2 not in VALID_LICENSES:
                    return False
                    valid_license = False
    return True
