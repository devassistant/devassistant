# -*- coding: utf-8 -*-
import pytest
import sys
import os
import logging
import itertools
try:
    from cStringIO import StringIO
except:
    try:
        from StringIO import StringIO
    except:
        from io import StringIO
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from daploader import *


class TestDap(object):
    '''Tests for the Dap class'''
    def test_no_gz(self):
        '''Not-gzip archive should raise DapFileError'''
        with pytest.raises(DapFileError):
            Dap('test/bz2.dap')

    def test_no_exist(self):
        '''Nonexisting file should raise DapFileError'''
        with pytest.raises(DapFileError):
            Dap('foo')

    def test_no_meta(self):
        '''Dap without meta.yaml should raise DapMetaError'''
        with pytest.raises(DapMetaError):
            Dap('test/no_meta.dap')

    def test_dap_data(self):
        '''Dap should have correct content in meta, basename and files'''
        dap = Dap('test/meta_only/foo-1.0.0.dap')
        assert dap.meta['package_name'] == 'foo'
        assert dap.meta['version'] == '1.0.0'
        assert u'Hrončok' in dap.meta['authors'][0]
        assert dap.basename == 'foo-1.0.0.dap'
        assert dap.files == ['foo-1.0.0', 'foo-1.0.0/meta.yaml']

    def test_no_toplevel(self):
        '''Dap with no top-level directory is invalid'''
        out = StringIO()
        assert not Dap('test/no_toplevel/foo-1.0.0.dap').check(output=out, level=logging.ERROR)
        assert len(out.getvalue().rstrip().split('\n')) == 1
        assert 'not in top-level directory' in out.getvalue()

    def test_valid_names(self):
        '''Test if valid names are valid'''
        d = Dap('', fake=True)
        for name in 'foo f bar v8 foo-bar-foo ffffff8ff f-_--s '.split():
            d.meta['package_name'] = name
            assert d._isvalid('package_name')

    def test_invalid_names(self):
        '''Test if invalid names are invalid'''
        d = Dap('', fake=True)
        for name in '9 8f -a - a_ _ ř H aaHa ? aa!a () * ff+a f8-- .'.split():
            d.meta['package_name'] = name
            assert not d._isvalid('package_name')

    def test_valid_versions(self):
        '''Test if valid versions are valid'''
        d = Dap('', fake=True)
        for version in '0 1 888 0.1 0.1a 0.0.0b 666dev 0.0.0.0.0 8.11'.split():
            d.meta['version'] = version
            assert d._isvalid('version')

    def test_invalid_versions(self):
        '''Test if invalid versions are invalid'''
        d = Dap('', fake=True)
        for version in '00 01 0.00.0 01.0 1c .1 1-2 h č . 1..0 1.0.'.split():
            d.meta['version'] = version
            assert not d._isvalid('version')

    def test_valid_urls(self):
        '''Test if valid URLs are valid'''
        d = Dap('', fake=True)
        urls = ['http://g.com/aa?ff=g&g#f',
                'ftp://g.aa/',
                'http://user:password@fee.com',
                'https://f.f.f.f.f.sk/cgi-bin/?f=Program%20Files']
        for url in urls:
            d.meta['homepage'] = url
            assert d._isvalid('homepage')

    def test_invalid_urls(self):
        '''Test if invalid URLs are invalid'''
        d = Dap('', fake=True)
        urls = ['g.com/a',
                'mailto:foo@bar.com',
                'ftp://192.168.1.1/?a',
                'https://localhost/']
        for url in urls:
            d.meta['homepage'] = url
            assert not d._isvalid('homepage')

    def test_valid_bugreports(self):
        '''Test if valid URLs or e-mails are valid'''
        d = Dap('', fake=True)
        bugs = ['http://g.com/',
                'miro@hroncok.cz',
                '?ouch@devassiatnt.org',
                'par_at_no.id',
                'par_at_n@o.id']
        for bug in bugs:
            d.meta['bugreports'] = bug
            assert d._isvalid('bugreports')

    def test_invalid_bugreports(self):
        '''Test if invalid URLs or e-mails are invalid'''
        d = Dap('', fake=True)
        bugs = ['httpr://g.com/',
                'miro@h@roncok.cz',
                '?ouchdevassiatnt.org',
                'par_at_no.iduss',
                '@o.id']
        for bug in bugs:
            d.meta['bugreports'] = bug
            assert not d._isvalid('bugreports')

    def test_valid_summary(self):
        '''Test if valid summary is valid'''
        d = Dap('', fake=True)
        d.meta['summary'] = 'foo'
        assert d._isvalid('summary')

    def test_invalid_summary(self):
        '''Test if invalid summary is invalid'''
        d = Dap('', fake=True)
        d.meta['summary'] = 'foo\nbar'
        assert not d._isvalid('summary')

    def test_empty_required(self):
        '''Required metadata should fail when undefined'''
        d = Dap('', fake=True)
        for item in 'package_name version license authors summary'.split():
            assert not d._isvalid(item)

    def test_valid_licenses(self):
        '''Test if valid licenses are valid'''
        d = Dap('', fake=True)
        licenses = ['AGPLv3 with exceptions',
                    'GPL+ or Artistic',
                    'LGPLv2+ and LGPLv2 and LGPLv3+ and (GPLv3 or LGPLv2) and (GPLv3+ or LGPLv2) and (CC-BY-SA or LGPLv2+) and (CC-BY-SA or LGPLv2) and CC-BY and BSD and MIT and Public Domain']
        for license in licenses:
            d.meta['license'] = license
            assert d._isvalid('license')

    def test_invalid_licenses(self):
        '''Test if invalid licenses are invalid'''
        d = Dap('', fake=True)
        licenses = ['Redistributable',
                    'GPLv4',
                    'LGPLv2+ and (LGPLv2',
                    'GNU GPL']
        for license in licenses:
            d.meta['license'] = license
            assert not d._isvalid('license')

    def test_valid_authors(self):
        '''Test if valid authors are valid'''
        d = Dap('', fake=True)
        pool = [u'Miro Hrončok <miro@hroncok.cz>',
                u'Miro Hrončok <miro_at_hroncok.cz>',
                u'Miro Hrončok',
                u'Dr. Voštěp',
                u'Никола I Петровић-Његош']
        for r in range(1, len(pool) + 1):
            for authors in itertools.combinations(pool, r):
                d.meta['authors'] = list(authors)
                ok, bads = d._arevalid('authors')
                assert ok
                assert not bads

    def test_invalid_authors(self):
        '''Test if invalid authors are invalid'''
        d = Dap('', fake=True)
        pool = [u'Miro Hrončok ',
                ' ',
                u' Miro Hrončok',
                u'Miro Hrončok miro@hroncok.cz',
                u'Miro Hrončok <miro@hr@oncok.cz>',
                '']
        for r in range(1, len(pool) + 1):
            for authors in itertools.combinations(pool, r):
                d.meta['authors'] = list(authors)
                ok, bads = d._arevalid('authors')
                assert not ok
                assert bads == list(authors)
        d.meta['authors'] = ['OK2 <ok@ok.ok>'] + pool + ['OK <ok@ok.ok>']
        ok, bads = d._arevalid('authors')
        assert bads == pool

    def test_duplicate_authors(self):
        '''Test if duplicate valid authors are invalid'''
        d = Dap('', fake=True)
        d.meta['authors'] = ['A', 'B', 'A']
        ok, bads = d._arevalid('authors')
        assert not ok
        assert bads == ['A']

    def test_empty_authors(self):
        '''Test if empty authors list is invalid'''
        d = Dap('', fake=True)
        d.meta['authors'] = []
        ok, null = d._arevalid('authors')
        assert not ok

    def test_meta_only_check(self):
        '''meta_only.dap should pass the test (errors only)'''
        dap = Dap('test/meta_only/foo-1.0.0.dap')
        assert dap.check(level=logging.ERROR)

    def test_meta_only_warning_check(self):
        '''meta_only.dap shopuld produce warning'''
        out = StringIO()
        dap = Dap('test/meta_only/foo-1.0.0.dap')
        assert not dap.check(output=out)
        assert len(out.getvalue().rstrip().split('\n')) == 1
        assert 'Only meta.yaml in dap' in out.getvalue()

    def test_unknown_metadata(self):
        '''meta_only.dap with added value should fail'''
        out = StringIO()
        dap = Dap('test/meta_only/foo-1.0.0.dap')
        dap.meta['foo'] = 'bar'
        assert not dap.check(output=out, level=logging.ERROR)
        assert len(out.getvalue().rstrip().split('\n')) == 1
        assert 'Unknown metadata' in out.getvalue()
        assert 'foo' in out.getvalue()

    def test_forgotten_version_in_filename_and_dir(self):
        '''Dap without version in filename and dirname should produce 2 errors'''
        out = StringIO()
        assert not Dap('test/meta_only/foo.dap').check(output=out, level=logging.ERROR)
        assert len(out.getvalue().rstrip().split('\n')) == 2
        assert 'Top-level directory with meta.yaml is not named foo-1.0.0' in out.getvalue()
        assert 'The dap filename is not foo-1.0.0.dap' in out.getvalue()

    def test_wrong_dap_filename(self):
        '''Dap with OK dirname, but wrong filename should produce 1 error'''
        out = StringIO()
        assert not Dap('test/meta_only/bar.dap').check(output=out, level=logging.ERROR)
        assert len(out.getvalue().rstrip().split('\n')) == 1
        assert 'The dap filename is not foo-1.0.0.dap' in out.getvalue()

    def test_files_outside_of_toplevel_dir(self):
        '''Dap with files outside of top-level directory should produce error for each'''
        out = StringIO()
        assert not Dap('test/outside_toplevel/foo-1.0.0.dap').check(output=out, level=logging.ERROR)
        assert len(out.getvalue().rstrip().split('\n')) == 3
        assert 'is outside' in out.getvalue()

    def test_empty_dirs(self):
        '''Dap with empty dirs produces warning'''
        out = StringIO()
        assert not Dap('test/empty_dirs/foo-1.0.0.dap').check(output=out)
        assert len(out.getvalue().rstrip().split('\n')) == 3
        assert ' is empty directory' in out.getvalue()

    def test_wrong_files(self):
        '''Dap with wrong files produces errors'''
        out = StringIO()
        assert not Dap('test/wrong_files/foo-1.0.0.dap').check(output=out, level=logging.ERROR)
        assert len(out.getvalue().rstrip().split('\n')) == 17
        assert '/files/wrong.txt is not allowed file' in out.getvalue()
        assert '/files/wrong/ is not allowed directory' in out.getvalue()
        assert '/files/wrong/a is not allowed file' in out.getvalue()
        assert '/files/foo/ is not allowed directory' in out.getvalue()
        assert '/files/foo/wrong is not allowed file' in out.getvalue()
        assert '/files/crt/wrong is not allowed file' in out.getvalue()
        assert '/icons/foo.gif is not allowed file' in out.getvalue()
        assert '/icons/foo.yaml is not allowed file' in out.getvalue()
        assert '/doc/README is not allowed file' in out.getvalue()
        assert '/snippets/bar/ is not allowed directory' in out.getvalue()
        assert '/snippets/bar/bar.yaml is not allowed file' in out.getvalue()
        assert '/assistants/wrong/ is not allowed directory' in out.getvalue()
        assert '/assistants/wrong/foo.yaml is not allowed file' in out.getvalue()
        assert '/assistants/task/bar.txt is not allowed file' in out.getvalue()
        assert '/assistants/task/bar.yaml is not allowed file' in out.getvalue()
        assert '/assistants/crt/test.yaml is not allowed file' in out.getvalue()
        assert '/assistants/prep/foo/ present' in out.getvalue()

    def test_icons_files_warnings(self):
        '''Dap with redundant or missing icons and redundant files should produce warnings'''
        out = StringIO()
        assert not Dap('test/wrong_files/foo-1.0.0.dap').check(output=out)
        assert 'Useless icon for non-exisiting assistant foo/a' in out.getvalue()
        assert 'Missing icon for assistant foo/bar' in out.getvalue()
        assert 'Useless files for non-exisiting assistant snippets/foo/deep' in out.getvalue()
        assert 'Useless files for non-exisiting assistant crt/foo' in out.getvalue()
