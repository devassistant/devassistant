# -*- coding: utf-8 -*-
import pytest
import sys
import os
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
        name = 'meta_only'
        basename = name + '.dap'
        dap = Dap('test/' + basename)
        assert dap.meta['package_name'] == 'foo'
        assert dap.meta['version'] == '1.0.0'
        assert u'Hrončok' in dap.meta['authors'][0]
        assert dap.basename == basename
        assert dap.files == [name, name + '/meta.yaml']

    def test_no_toplevel(self):
        '''Dap with no top-level directory is invalid'''
        out = StringIO()
        Dap('test/no_toplevel.dap').check(output=out)
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
