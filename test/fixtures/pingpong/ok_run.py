from dapp import DAPPClient

class MyClient(DAPPClient):
    def run(self, ctxt):
        self.call_command(ctxt, 'log_i', 'from var: $foo')
        self.call_command(ctxt, 'log_i', 'from ctxt: ' + ctxt['foo'])
        ctxt['set_by_pp_client'] = 'bar'
        del ctxt['foo']
        self.call_command(ctxt, 'cl', 'echo "foo"')
        return True, 'Everything OK'

if __name__ == '__main__':
    MyClient().pingpong()
