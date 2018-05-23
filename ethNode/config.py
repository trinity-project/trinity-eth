
import os

ENVIRON=os.environ

class SettingHolder(object):

    NEO_ASSETID = "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b"
    GAS_ASSETID = "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7"


    def setup_mainnet(self):
        self.ETH_URL = ""

    def setup_testnet(self):
        self.ETH_URL = "http://47.254.31.231:8545"
    def setup_privtnet(self):
        self.ETH_URL = "http://192.168.214.178:8545"

setting=SettingHolder()

if ENVIRON.get("CURRENT_ENVIRON") == "testnet":
    setting.setup_testnet()
elif ENVIRON.get("CURRENT_ENVIRON") == "mainnet":
    setting.setup_mainnet()
else:
    setting.setup_privtnet()
