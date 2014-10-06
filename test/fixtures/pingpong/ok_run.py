from dapp import DAPPClient

class MyClient(DAPPClient):
    def run(self, ctxt):
        self.call_command('log_i', 'from var: $foo', ctxt)
        self.call_command('log_i', 'from ctxt: ' + ctxt['foo'], ctxt)
        ctxt['set_by_pp_client'] = 'bar'
        del ctxt['foo']
        self.call_command('cl', 'echo "foo"', ctxt)
        return True, 'Everything OK'

if __name__ == '__main__':
    MyClient().pingpong()
