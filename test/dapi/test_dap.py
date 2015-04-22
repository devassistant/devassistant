# -*- coding: utf-8 -*-
import pytest
import sys
import os
import logging
import itertools
import glob
import subprocess
from flexmock import flexmock
try:
    from cStringIO import StringIO
except:
    try:
        from StringIO import StringIO
    except:
        from io import StringIO
from devassistant.dapi import *
from test import fixtures_dir
from devassistant import utils


def dap_path(fixture):
    '''Return appropriate dap path'''
    return os.path.join(fixtures_dir, 'dapi', 'daps', fixture)


def l(level = logging.WARNING, output = sys.stderr):
    '''Gets the logger'''
    logger = logging.getLogger('daptest')
    handler = logging.StreamHandler(output)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def combinations(pool):
    '''Prepare all various combinations of given list'''
    ret = []
    # the min() is there, because we don't need all the combinations, just lot of them
    for r in range(1, min(len(pool), 2) + 1):
        ret += itertools.combinations(pool, r)
    return ret


class TestDap(object):
    '''Tests for the Dap class'''

    def test_no_gz(self):
        '''Not-gzip archive should raise DapFileError'''
        with pytest.raises(DapFileError):
            Dap(dap_path('bz2.dap'))

    def test_no_exist(self):
        '''Nonexisting file should raise DapFileError'''
        with pytest.raises(DapFileError):
            Dap('foo')

    def test_no_meta(self):
        '''Dap without meta.yaml should raise DapMetaError'''
        with pytest.raises(DapMetaError):
            Dap(dap_path('no_meta.dap'))

    def test_dap_data(self):
        '''Dap should have correct content in meta, basename and files'''
        dap = Dap(dap_path('meta_only/foo-1.0.0.dap'))
        assert dap.meta['package_name'] == 'foo'
        assert dap.meta['version'] == '1.0.0'
        assert u'Hrončok' in dap.meta['authors'][0]
        assert dap.basename == 'foo-1.0.0.dap'
        assert dap.files == ['foo-1.0.0', 'foo-1.0.0/meta.yaml']

    def test_no_toplevel(self):
        '''Dap with no top-level directory is invalid'''
        out = StringIO()
        dap = Dap(dap_path('no_toplevel/foo-1.0.0.dap'))
        assert not DapChecker.check(dap, logger=l(output=out, level=logging.ERROR))
        assert len(out.getvalue().rstrip().split('\n')) == 1
        assert 'not in top-level directory' in out.getvalue()

    @pytest.mark.parametrize('name', ['foo', 'f', 'bar', 'v8', 'foo-bar-foo', 'ffff8ff', 'f-_--s'])
    def test_valid_names(self, name):
        '''Test if valid names are valid'''
        d = Dap('', fake=True)
        d.meta['package_name'] = name
        d._find_bad_meta()
        assert d._isvalid('package_name')

    @pytest.mark.parametrize('name', ['9', '8f', '-a', '-', 'a_', '_', 'ř', 'H', 'aaHa',
                                      '?', 'aa!a', '()', '*', 'ff+a', 'f8--', '.'])
    def test_invalid_names(self, name):
        '''Test if invalid names are invalid'''
        d = Dap('', fake=True)
        d.meta['package_name'] = name
        d._find_bad_meta()
        assert not d._isvalid('package_name')

    @pytest.mark.parametrize('version', ['0', '1', '888', '0.1', '0.1a',
                                         '0.0.0b', '666dev', '0.0.0.0.0', '8.11'])
    def test_valid_versions(self, version):
        '''Test if valid versions are valid'''
        d = Dap('', fake=True)
        d.meta['version'] = version
        d._find_bad_meta()
        assert d._isvalid('version')

    @pytest.mark.parametrize('version', ['00', '01', '0.00.0', '01.0', '1c', '.1',
                                         '1-2', 'h', 'č', '.', '1..0', '1.0.'])
    def test_invalid_versions(self, version):
        '''Test if invalid versions are invalid'''
        d = Dap('', fake=True)
        d.meta['version'] = version
        d._find_bad_meta()
        assert not d._isvalid('version')

    def test_loading_float_version(self):
        '''Test that loading doesn't fail if version is loaded from YAML as float'''
        out = StringIO()
        dap = Dap(dap_path('meta_only/bad_version-0.1.dap'))
        assert DapChecker.check(dap, logger=l(output=out, level=logging.ERROR))

    @pytest.mark.parametrize('url', ['http://g.com/aa?ff=g&g#f',
                                     'ftp://g.aa/',
                                     'http://user:password@fee.com',
                                     'https://f.f.f.f.f.sk/cgi-bin/?f=Program%20Files'])
    def test_valid_urls(self, url):
        '''Test if valid URLs are valid'''
        d = Dap('', fake=True)
        d.meta['homepage'] = url
        d._find_bad_meta()
        assert d._isvalid('homepage')

    @pytest.mark.parametrize('url', ['g.com/a',
                                     'mailto:foo@bar.com',
                                     'ftp://192.168.1.1/?a',
                                     'https://localhost/'])
    def test_invalid_urls(self, url):
        '''Test if invalid URLs are invalid'''
        d = Dap('', fake=True)
        d.meta['homepage'] = url
        d._find_bad_meta()
        assert not d._isvalid('homepage')

    @pytest.mark.parametrize('bug', ['http://g.com/',
                                     'miro@hroncok.cz',
                                     '?ouch@devassiatnt.org',
                                     'par_at_no.id',
                                     'par_at_n@o.id'])
    def test_valid_bugreports(self, bug):
        '''Test if valid URLs or e-mails are valid'''
        d = Dap('', fake=True)
        d.meta['bugreports'] = bug
        d._find_bad_meta()
        assert d._isvalid('bugreports')

    @pytest.mark.parametrize('bug', ['httpr://g.com/',
                                     'miro@h@roncok.cz',
                                     '?ouchdevassiatnt.org',
                                     'par_at_no.iduss',
                                     '@o.id'])
    def test_invalid_bugreports(self, bug):
        '''Test if invalid URLs or e-mails are invalid'''
        d = Dap('', fake=True)
        d.meta['bugreports'] = bug
        d._find_bad_meta()
        assert not d._isvalid('bugreports')

    def test_valid_summary(self):
        '''Test if valid summary is valid'''
        d = Dap('', fake=True)
        d.meta['summary'] = 'foo'
        d._find_bad_meta()
        assert d._isvalid('summary')

    def test_invalid_summary(self):
        '''Test if invalid summary is invalid'''
        d = Dap('', fake=True)
        d.meta['summary'] = 'foo\nbar'
        d._find_bad_meta()
        assert not d._isvalid('summary')

    @pytest.mark.parametrize('item', ['package_name', 'version', 'license', 'authors', 'summary'])
    def test_empty_required(self, item):
        '''Required metadata should fail when undefined'''
        d = Dap('', fake=True)
        assert not d._isvalid(item)

    @pytest.mark.parametrize('license', ['AGPLv3 with exceptions',
                                         'GPL+ or Artistic',
                                         'LGPLv2+ and LGPLv2 and LGPLv3+ and (GPLv3 or '
                                         'LGPLv2) and (GPLv3+ or LGPLv2) and (CC-BY-SA '
                                         'or LGPLv2+) and (CC-BY-SA or LGPLv2) and CC-BY '
                                         'and BSD and MIT and Public Domain'])
    def test_valid_licenses(self, license):
        '''Test if valid licenses are valid'''
        d = Dap('', fake=True)
        d.meta['license'] = license
        d._find_bad_meta()
        assert d._isvalid('license')

    @pytest.mark.parametrize('license', ['Redistributable',
                                         'GPLv4',
                                         'LGPLv2+ and (LGPLv2',
                                         'GNU GPL'])
    def test_invalid_licenses(self, license):
        '''Test if invalid licenses are invalid'''
        d = Dap('', fake=True)
        d.meta['license'] = license
        d._find_bad_meta()
        assert not d._isvalid('license')

    @pytest.mark.parametrize('authors', combinations([u'Miro Hrončok <miro@hroncok.cz>',
                                                      u'Miro Hrončok <miro_at_hroncok.cz>',
                                                      u'Miro Hrončok',
                                                      u'Dr. Voštěp',
                                                      u'Никола I Петровић-Његош']))
    def test_valid_authors(self, authors):
        '''Test if valid authors are valid'''
        d = Dap('', fake=True)
        d.meta['authors'] = list(authors)
        d._find_bad_meta()
        ok, bads = d._arevalid('authors')
        assert ok
        assert not bads

    @pytest.mark.parametrize('authors', combinations([u'Miro Hrončok ',
                                                      ' ',
                                                      u' Miro Hrončok',
                                                      u'Miro Hrončok miro@hroncok.cz',
                                                      u'Miro Hrončok <miro@hr@oncok.cz>',
                                                      '']))
    def test_invalid_authors(self, authors):
        '''Test if invalid authors are invalid'''
        d = Dap('', fake=True)
        d.meta['authors'] = list(authors)
        d._find_bad_meta()
        ok, bads = d._arevalid('authors')
        assert not ok
        assert bads == list(authors)

    def test_invalid_authors_bads(self):
        '''Test if on invalid authors are reported as invalid'''
        d = Dap('', fake=True)
        d.meta['authors'] = ['OK2 <ok@ok.ok>', ' ', '  ', 'OK <ok@ok.ok>']
        d._find_bad_meta()
        ok, bads = d._arevalid('authors')
        assert sorted(bads) == [' ', '  ']

    def test_duplicate_authors(self):
        '''Test if duplicate valid authors are invalid'''
        d = Dap('', fake=True)
        d.meta['authors'] = ['A', 'B', 'A']
        d._find_bad_meta()
        ok, bads = d._arevalid('authors')
        assert not ok
        assert bads == ['A']

    def test_empty_authors(self):
        '''Test if empty authors list is invalid'''
        d = Dap('', fake=True)
        d.meta['authors'] = []
        d._find_bad_meta()
        ok, null = d._arevalid('authors')
        assert not ok

    @pytest.mark.parametrize('deps', combinations(['foo',
                                                   'foo == 1.0.0',
                                                   'foo >= 1.0.0',
                                                   'foo <= 1.0.0',
                                                   'foo > 1.0.0',
                                                   'foo  < 1.0.0',
                                                   'foo <1.0.0',
                                                   'foo<1.0.0',
                                                   'foo< 1.0.0',
                                                   'foo      <    1.0.0',
                                                   'foo                   <1.0.0',
                                                   'foo < 1.0.0b']))
    def test_valid_dependencies(self, deps):
        '''Test if valid dependencies are valid'''
        d = Dap('', fake=True)
        d.meta['dependencies'] = list(deps)
        d._find_bad_meta()
        ok, bads = d._arevalid('dependencies')
        assert ok
        assert not bads

    @pytest.mark.parametrize('deps', combinations(['foo != 1.0.0',
                                                   'foo = 1.0.0',
                                                   'foo =< 1.0.0',
                                                   'foo >> 1.0.0',
                                                   'foo > = 1.0.0',
                                                   '1.0.0',
                                                   'foo-1.0.0',
                                                   ' ',
                                                   '']))
    def test_invalid_dependencies(self, deps):
        '''Test if invalid dependencies are invalid'''
        d = Dap('', fake=True)
        d.meta['dependencies'] = list(deps)
        d._find_bad_meta()
        ok, bads = d._arevalid('dependencies')
        assert not ok
        assert bads == list(deps)

    def test_invalid_dependencies_bads(self):
        '''Test if only invalid dependencies are reported invalid'''
        d = Dap('', fake=True)
        d.meta['dependencies'] = ['foo', '1.0.0', 'foo != 1.0.0', 'bar']
        d._find_bad_meta()
        ok, bads = d._arevalid('dependencies')
        assert sorted(bads) == sorted(['1.0.0', 'foo != 1.0.0'])

    def test_duplicate_dependencies(self):
        '''Test if duplicate valid dependencies are invalid'''
        d = Dap('', fake=True)
        d.meta['dependencies'] = ['A', 'B', 'A']
        d._find_bad_meta()
        ok, bads = d._arevalid('dependencies')
        assert not ok
        assert bads == ['A']

    def test_self_dependency(self):
        '''Test if depending on itself produces error'''
        d = Dap('', fake=True)
        d.meta['dependencies'] = ['a', 'b > 1']
        d.meta['package_name'] = 'b'
        d._find_bad_meta()
        assert DapChecker.check_no_self_dependency(d) != []

        d.meta['package_name'] = 'c'
        d._find_bad_meta()
        assert DapChecker.check_no_self_dependency(d) == []

        d.meta['dependencies'] = ['c', 'b=1', 'a']
        d.meta['package_name'] = 'b'
        d._find_bad_meta()
        assert DapChecker.check_no_self_dependency(d) == []

    def test_empty_dependencies(self):
        '''Test if empty dependencies list is valid'''
        d = Dap('', fake=True)
        d.meta['dependencies'] = []
        d._find_bad_meta()
        ok, null = d._arevalid('dependencies')
        assert ok

    @pytest.mark.parametrize('platforms', combinations(['suse', 'debian', 'fedora', 'redhat',
                                                        'centos', 'mandrake', 'mandriva',
                                                        'rocks', 'slackware', 'yellowdog',
                                                        'gentoo', 'unitedlinux', 'turbolinux',
                                                        'arch', 'mageia', 'ubuntu', 'darwin']))
    def test_valid_supported_platforms(self, platforms):
        '''Test if valid supported_platforms are valid'''
        d = Dap('', fake=True)
        d.meta['supported_platforms'] = list(platforms)
        d._find_bad_meta()
        ok, bads = d._arevalid('supported_platforms')
        assert ok
        assert not bads

    @pytest.mark.parametrize('platforms', combinations(['linux', 'windows', '5', 'Mac OS X']))
    def test_invalid_supported_platforms(self, platforms):
        '''Test if invalid supported_platforms are invalid'''
        d = Dap('', fake=True)
        d.meta['supported_platforms'] = list(platforms)
        d._find_bad_meta()
        ok, bads = d._arevalid('supported_platforms')
        assert not ok
        assert sorted(bads) == sorted(platforms)

    def test_invalid_supported_platforms_bads(self):
        '''Test if only invalid supported_platforms are reported as invalid'''
        d = Dap('', fake=True)
        d.meta['supported_platforms'] = ['fedora', 'bad', 'wrong', 'darwin']
        d._find_bad_meta()
        ok, bads = d._arevalid('supported_platforms')
        assert sorted(bads) == ['bad', 'wrong']

    def test_duplicate_supported_platforms(self):
        '''Test if duplicate valid supported_platforms are invalid'''
        d = Dap('', fake=True)
        d.meta['supported_platforms'] = ['fedora', 'redhat', 'fedora']
        ok, bads = d._arevalid('supported_platforms')
        assert not ok
        assert bads == ['fedora']

    def test_empty_supported_platforms(self):
        '''Test if empty supported_platforms list is valid'''
        d = Dap('', fake=True)
        d.meta['supported_platforms'] = []
        ok, null = d._arevalid('supported_platforms')
        assert ok

    def test_meta_only_check(self):
        '''meta_only.dap should pass the test (errors only)'''
        dap = Dap(dap_path('meta_only/foo-1.0.0.dap'))
        assert DapChecker.check(dap, logger=l(level=logging.ERROR))

    def test_meta_only_warning_check(self):
        '''meta_only.dap shopuld produce warning'''
        out = StringIO()
        dap = Dap(dap_path('meta_only/foo-1.0.0.dap'))
        assert not DapChecker.check(dap, logger=l(output=out))
        assert len(out.getvalue().rstrip().split('\n')) == 1
        assert 'Only meta.yaml in dap' in out.getvalue()

    def test_unknown_metadata(self):
        '''meta_only.dap with added value should fail'''
        out = StringIO()
        dap = Dap(dap_path('meta_only/foo-1.0.0.dap'))
        dap.meta['foo'] = 'bar'
        assert not DapChecker.check(dap, logger=l(output=out, level=logging.ERROR))
        assert len(out.getvalue().rstrip().split('\n')) == 1
        assert 'Unknown metadata' in out.getvalue()
        assert 'foo' in out.getvalue()

    def test_forgotten_version_in_filename_and_dir(self):
        '''Dap without version in filename and dirname should produce 2 errors'''
        out = StringIO()
        dap = Dap(dap_path('meta_only/foo.dap'))
        assert not DapChecker.check(dap, logger=l(output=out, level=logging.ERROR))
        assert len(out.getvalue().rstrip().split('\n')) == 2
        assert 'Top-level directory with meta.yaml is not named foo-1.0.0' in out.getvalue()
        assert 'The dap filename is not foo-1.0.0.dap' in out.getvalue()

    def test_wrong_dap_filename(self):
        '''Dap with OK dirname, but wrong filename should produce 1 error'''
        out = StringIO()
        dap = Dap(dap_path('meta_only/bar.dap'))
        assert not DapChecker.check(dap, logger=l(output=out, level=logging.ERROR))
        assert len(out.getvalue().rstrip().split('\n')) == 1
        assert 'The dap filename is not foo-1.0.0.dap' in out.getvalue()

    def test_wrong_dap_filename_mimicked_to_be_ok(self):
        '''Dap with wrong filename, mimicked to be OK, should produce no error'''
        dap = Dap(dap_path('meta_only/bar.dap'), mimic_filename='foo-1.0.0.dap')
        assert DapChecker.check(dap, logger=l(level=logging.ERROR))

    def test_good_dap_filename_mimicked_to_be_wrong(self):
        '''Error passing dap, should fail with wrong mimicked filename'''
        dap = Dap(dap_path('meta_only/foo-1.0.0.dap'), mimic_filename='wrong')
        assert not DapChecker.check(dap, logger=l(level=logging.ERROR))

    def test_files_outside_of_toplevel_dir(self):
        '''Dap with files outside of top-level directory should produce error for each'''
        out = StringIO()
        dap = Dap(dap_path('outside_toplevel/foo-1.0.0.dap'))
        assert not DapChecker.check(dap, logger=l(output=out, level=logging.ERROR))
        assert len(out.getvalue().rstrip().split('\n')) == 3
        assert 'is outside' in out.getvalue()

    def test_empty_dirs(self):
        '''Dap with empty dirs produces warning'''
        out = StringIO()
        dap = Dap(dap_path('empty_dirs/foo-1.0.0.dap'))
        assert not DapChecker.check(dap, logger=l(output=out))
        assert 'foo-1.0.0/assistants is empty directory (may be nested)' in out.getvalue()
        assert 'foo-1.0.0/assistants/crt is empty directory (may be nested)' in out.getvalue()
        assert 'foo-1.0.0/assistants/twk is empty directory (may be nested)' in out.getvalue()

    def test_wrong_files(self):
        '''Dap with wrong files produces errors'''
        out = StringIO()
        dap = Dap(dap_path('wrong_files/foo-1.0.0.dap'))
        assert not DapChecker.check(dap, logger=l(output=out, level=logging.ERROR))
        assert len(out.getvalue().rstrip().split('\n')) == 21
        assert '/files/wrong.txt is not allowed file' in out.getvalue()
        assert '/files/wrong/ is not allowed directory' in out.getvalue()
        assert '/files/wrong/a is not allowed file' in out.getvalue()
        assert '/files/foo/ is not allowed directory' in out.getvalue()
        assert '/files/foo/wrong is not allowed file' in out.getvalue()
        assert '/files/crt/wrong is not allowed file' in out.getvalue()
        assert '/icons/foo.gif is not allowed file' in out.getvalue()
        assert '/icons/foo.yaml is not allowed file' in out.getvalue()
        assert '/icons/twk/foo.gif is not allowed file' in out.getvalue()
        assert '/icons/twk/foo.yaml is not allowed file' in out.getvalue()
        assert '/icons/foo/ is not allowed directory' in out.getvalue()
        assert '/icons/foo/a.png is not allowed file' in out.getvalue()
        assert '/doc/README is not allowed file' in out.getvalue()
        assert '/snippets/bar/ is not allowed directory' in out.getvalue()
        assert '/snippets/bar/bar.yaml is not allowed file' in out.getvalue()
        assert '/assistants/wrong/ is not allowed directory' in out.getvalue()
        assert '/assistants/wrong/foo.yaml is not allowed file' in out.getvalue()
        assert '/assistants/extra/bar.txt is not allowed file' in out.getvalue()
        assert '/assistants/extra/bar.yaml is not allowed file' in out.getvalue()
        assert '/assistants/crt/test.yaml is not allowed file' in out.getvalue()
        assert '/assistants/prep/foo/ present' in out.getvalue()

    def test_icons_files_warnings(self):
        '''Dap with redundant or missing icons and redundant files should produce warnings'''
        out = StringIO()
        dap = Dap(dap_path('wrong_files/foo-1.0.0.dap'))
        assert not DapChecker.check(dap, logger=l(output=out))
        assert 'Useless icon for non-exisiting assistant twk/foo/a' in out.getvalue()
        assert 'Useless icon for non-exisiting assistant twk/foo/a' in out.getvalue()
        assert 'Useless icon for non-exisiting assistant crt/foo' in out.getvalue()
        assert 'Useless icon for non-exisiting assistant crt/foo' in out.getvalue()
        assert 'Missing icon for assistant twk/foo/bar' in out.getvalue()
        assert 'Missing icon for assistant twk/foo/bar' in out.getvalue()
        assert 'Missing icon for assistant prep/foo/bar' in out.getvalue()
        assert 'Missing icon for assistant prep/foo/bar' in out.getvalue()

    def test_bad_yamls(self):
        '''Dap with malformed YAMLs should produce an error'''
        out = StringIO()
        dap = Dap(dap_path('badyamls/badyamls-1.0.dap'))
        assert not DapChecker.check(dap, logger=l(output=out, level=logging.ERROR))
        desired = '''badyamls-1.0.dap: Source file assistants/crt/badyamls.yaml:
  Problem in: (top level) -> corrupted
Invalid section name: corrupted
'''
        assert out.getvalue() == desired

    def test_empty_yamls(self):
        '''Dap with empty YAMLs should produce warning'''
        out = StringIO()
        dap = Dap(dap_path('badyamls/badyamls-1.0.dap'))
        assert not DapChecker.check(dap, logger=l(output=out))
        assert 'badyamls-1.0.dap: Empty YAML snippets/badyamls.yaml' in out.getvalue()

    def test_dapi_check(self):
        '''Dap that is already on dapi should produce a warning when network is True'''
        out = StringIO()
        flexmock(dapicli).should_receive('data').and_return('something')
        dap = Dap(dap_path('meta_only/foo-1.0.0.dap'))
        DapChecker.check(dap, logger=l(output=out), network=True)
        assert 'This dap name is already registered on Dapi' in out.getvalue()

    def test_dapi_check_false(self):
        '''Dap that is not already on dapi should not produce a warning when network is True'''
        out = StringIO()
        flexmock(dapicli).should_receive('data').and_return('')
        dap = Dap(dap_path('meta_only/foo-1.0.0.dap'))
        DapChecker.check(dap, logger=l(output=out), network=True)
        assert 'This dap name is already registered on Dapi' not in out.getvalue()

    def test_dap_good_dependencies(self):
        '''Dap with good dependencies produces no error'''
        dap = Dap(dap_path('dependencies/good-1.0.0.dap'))
        assert DapChecker.check(dap, logger=l(level=logging.ERROR))

    def test_dap_invalid_dependencies(self):
        '''Dap with invalid dependency produces an error'''
        out = StringIO()
        dap = Dap(dap_path('dependencies/invalid-1.0.0.dap'))
        assert not DapChecker.check(dap, logger=l(output=out, level=logging.ERROR))
        assert 'invalid 0.0.1 in dependencies is not valid' in out.getvalue()

    def test_dap_self_dependenciey(self):
        '''Dap with self dependency produces an error'''
        out = StringIO()
        dap = Dap(dap_path('dependencies/self-1.0.0.dap'))
        assert not DapChecker.check(dap, logger=l(output=out, level=logging.ERROR))
        assert 'Depends on dap with the same name as itself' in out.getvalue()

    @pytest.mark.parametrize('dap', glob.glob(dap_path('meta_only/*.dap')))
    def test_sha256sum(self, dap):
        '''Check that sha256sum of the files is the same as sha256sum command does'''
        try:
            process = subprocess.Popen(['sha256sum', dap], stdout=subprocess.PIPE)
        except OSError:
            # This is the command for sha256sum on Mac
            process = subprocess.Popen(['shasum', '-a', '256', dap], stdout=subprocess.PIPE)
        assert Dap(dap).sha256sum == process.communicate()[0].split()[0].decode(utils.defenc)

    def test_assistants_and_snippets_property(self):
        '''Check that the assistants_and_snippets property contains the right results.

        This was renamed from list_assitants()'''
        # Using set because we don't care about the order
        dapdap = set([
            'assistants/crt/dap',
            'assistants/twk/dap',
            'assistants/twk/dap/add',
            'assistants/twk/dap/pack',
            'snippets/dap',
        ])
        assert set(Dap(dap_path('list_assistants/dap-0.0.1a.dap')).assistants_and_snippets) == dapdap
        assert Dap(dap_path('meta_only/foo-1.0.0.dap')).assistants_and_snippets == []

    @pytest.mark.parametrize(('pkg_name', 'expected'), [
        (201*'a', True),
        ('foobar', False),
    ])
    def test_pkg_name_too_long(self, pkg_name, expected):
        '''Package names must not exceed 200 characters'''
        dap = Dap(pkg_name, fake=True)
        dap.meta['package_name'] = pkg_name
        dap._find_bad_meta()
        problems = DapChecker.check_meta(dap)

        err_string = 'Package name is too long. It must not exceed 200 characters.'
        assert (err_string in [p.message for p in problems]) is expected

    @pytest.mark.parametrize('path', ['empty_dirs/foo-1.0.0.dap', 'no_assistants-0.0.1dev.dap'])
    def test_no_assistants_warning(self, path):
        '''Check if absence of both assitants and snippets is reported

        foo-1.0.0.dap is used because it has YAML assistants missing,
        no_assistants-0.0.1dev.dap doesn't have assistants/ or snippets/ directories at all'''
        dap = Dap(dap_path(path))
        err_out = StringIO()
        warn_out = StringIO()

        DapChecker.check(dap, logger=l(output=warn_out, level=logging.WARNING))
        DapChecker.check(dap, logger=l(output=err_out, level=logging.ERROR))

        assert 'No Assistants or Snippets found' in warn_out.getvalue()
        assert 'No Assistants or Snippets found' not in err_out.getvalue()

    def test_icons(self):
        dap = Dap(None, fake=True, mimic_filename='foo')
        dap.files = ['foo/icons/crt/bar.svg', 'foo/icons/crt/baz.png', 'foo/icons/twk/qux.svg']

        assert dap.icons() == ['icons/crt/bar.svg', 'icons/crt/baz.png', 'icons/twk/qux.svg']
        assert dap.icons(strip_ext=True) == ['icons/crt/bar', 'icons/crt/baz', 'icons/twk/qux']
