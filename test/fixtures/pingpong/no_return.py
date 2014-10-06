from dapp import DAPPClient

class MyClient(DAPPClient):
    def run(self, ctxt):
        pass

if __name__ == '__main__':
    MyClient().pingpong()
