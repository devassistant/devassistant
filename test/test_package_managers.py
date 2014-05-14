import pytest

from flexmock import flexmock

from devassistant.command_helpers import ClHelper
from devassistant.package_managers import YUMPackageManager

class TestYUMPackageManager(object):

    def setup_method(self, method):
        self.ypm = YUMPackageManager()

    @pytest.mark.parametrize('result', [True, False])
    def test_is_rpm_installed(self, result):
        flexmock(ClHelper).should_receive('run_command')\
                .with_args('rpm -q --whatprovides "foo"').and_return(result)
        assert self.ypm.is_rpm_installed('foo') is result

    @pytest.mark.parametrize(('group', 'output', 'result'), [
        ('foo', 'Installed Groups', 'foo'),
        ('bar', '', False)
    ])
    def test_is_group_installed(self, group, output, result):
        flexmock(ClHelper).should_receive('run_command')\
                .with_args('yum group list "{grp}"'.format(grp=group)).and_return(output)
        assert self.ypm.is_group_installed(group) is result

