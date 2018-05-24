
import os

ENVIRON=os.environ

class SettingHolder(object):

    def setup_mainnet(self):
        self.ETH_URL = ""

    def setup_testnet(self):
        self.ETH_URL = "http://127.0.0.1:8545"
    def setup_privtnet(self):
        # self.ETH_URL = "http://192.168.28.139:8545"
        self.ETH_URL = "http://192.168.214.178:8545"

setting=SettingHolder()

if ENVIRON.get("CURRENT_ENVIRON") == "testnet":
    setting.setup_testnet()
elif ENVIRON.get("CURRENT_ENVIRON") == "mainnet":
    setting.setup_mainnet()
else:
    setting.setup_privtnet()
