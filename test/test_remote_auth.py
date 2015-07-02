import os
import stat

from devassistant import remote_auth


class TestGitHubAuth(object):

    def test_start_ssh_agent(self):
        '''Test that the ssh-agent get's started and appropriate env is returned'''
        env = remote_auth.GitHubAuth._start_ssh_agent()

        try:
            assert 'SSH_AUTH_SOCK' in env
            assert 'SSH_AGENT_PID' in env

            # Sending signal 0 to a pid will raise an OSError exception
            # if the pid is not running, and do nothing otherwise
            os.kill(int(env['SSH_AGENT_PID']), 0)

            # Check if the socket exists
            mode = os.stat(env['SSH_AUTH_SOCK']).st_mode
            assert stat.S_ISSOCK(mode)
        finally:
            # Kill the ssh-agent
            try:
                os.kill(int(env['SSH_AGENT_PID']), 15)
            except:
                pass
