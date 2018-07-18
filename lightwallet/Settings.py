
import os
from blockchain.web3client import Client





class SettingsHolder:

    headers = {
        "Content-Type": "application/json"
    }

    DIR_CURRENT = os.path.dirname(os.path.abspath(__file__))
    ADDRESS_VERSION = 23

    TNC = "0x0c34a8fd0109df360c7cf7ca454404901db77f5e"


    NODEURL = None
    NET_NAME = None
    EthClient =None



    def setup_mainnet(self):
        self.NET_NAME = "MainNet"
        self.NODEURL = "http://main:"
        self.TNC = "0x08e8c4400f1af2c20c28e0018f29535eb85d15b6"
        self.create_client()
    def setup_testnet(self):
        self.NET_NAME = "TestNet"
        self.NODEURL = "https://ropsten.infura.io"
        self.TNC = "0x849d095d07950b9e56d0c895ec48ec5100cfdff1"
        self.create_client()
    def setup_privnet(self):
        self.NET_NAME = "PrivateNet"
        self.NODEURL = "http://localhost:8888"
        self.TNC = "0x0c34a8fd0109df360c7cf7ca454404901db77f5e"
        self.create_client()

    def create_client(self):
        self.EthClient = Client(self.NODEURL)


settings = SettingsHolder()


