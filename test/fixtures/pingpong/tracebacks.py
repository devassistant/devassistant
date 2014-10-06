from dapp import DAPPClient

class MyClient(DAPPClient):
    def run(self, ctxt):
        raise BaseException('problem')

if __name__ == '__main__':
    MyClient().pingpong()
