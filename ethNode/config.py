
import os

ENVIRON=os.environ


class SettingHolder(object):

    MYSQLDATABASE = {
        "host": "127.0.0.1",
        "user": ENVIRON.get("DATABASE_USERNAME"),
        "passwd": ENVIRON.get("DATABASE_PASSWORD"),
        "db": ENVIRON.get("DATABASE_DB"),
        "db_block_info": ENVIRON.get("DATABASE_DB_BLOCK_INFO")
    }


    def setup_mainnet(self):
        # self.ETH_URL = "http://127.0.0.1:8545"
        self.ETH_URL = "https://mainnet.infura.io/pZc5ZTRYM8wYfRPtoQal"

        self.SmartContract = {
            "ERC20TNC": ("0xc9ad73d11d272c95b5a2c48780a55b6b3c726cac", mainnet_testnet_abi)
        }
        self.ABI_MAPPING = {
            "0xc9ad73d11d272c95b5a2c48780a55b6b3c726cac": mainnet_testnet_abi
        }

        self.CONTRACT_ADDRESS="0xc9ad73d11d272c95b5a2c48780a55b6b3c726cac"
        self.PRIVTKEY=ENVIRON.get("PRIVTKEY")
        self.PASSWD_HASH="$2b$10$F7GVmj.eahbHMIUjOxooYuLBMqZaIGcJZ7KxufGfbxwGTErKCzNQm"
        self.REMOTE_ADDR="47.75.69.238"
        self.FUNDING_ADDRESS="0x0d7C7D0e76E25290aBB5BfEc7D1adFf36BEfb09F"
        self.WEBAPI = "https://tokenswap.trinity.ink/monitor/transactions"

    def setup_testnet(self):
        self.ETH_URL = "http://127.0.0.1:8545"
        self.SmartContract={
            "ERC20TNC":("0x65096f2B7A8dc1592479F1911cd2B98dae4d2218",ropsten_testnet_abi)
        }
        self.ABI_MAPPING = {
            "0x65096f2B7A8dc1592479F1911cd2B98dae4d2218": ropsten_testnet_abi
        }

        self.CONTRACT_ADDRESS="0x65096f2b7a8dc1592479f1911cd2b98dae4d2218"

        self.PRIVTKEY=ENVIRON.get("PRIVTKEY")
        self.PASSWD_HASH="$2b$10$F7GVmj.eahbHMIUjOxooYuLBMqZaIGcJZ7KxufGfbxwGTErKCzNQm"
        # self.REMOTE_ADDR="125.119.251.196"
        self.REMOTE_ADDR="47.75.69.238"
        self.FUNDING_ADDRESS="0xBF3De70657B3C346E72720657Bbc75AbFc4Ec217"
        self.WEBAPI = "http://tokenswap.trinity.tech/monitor/transactions"

    def setup_privtnet(self):
        # self.ETH_URL = "http://192.168.28.139:8545"
        self.ETH_URL = "http://192.168.214.178:8545"
        self.SmartContract={
            "ERC20TNC":("0x8AB0FC62b95AA25EE0FBd80eDc1252DDa670Aa6C",privtnet_abi)
        }
        self.ABI_MAPPING = {
            "0x8AB0FC62b95AA25EE0FBd80eDc1252DDa670Aa6C": privtnet_abi
        }



privtnet_abi=[{"constant": True, "inputs": [], "name": "name",
                                                    "outputs": [{"name": "", "type": "string", "value": "TNC1"}],
                                                    "payable": False, "stateMutability": "view", "type": "function"},
                                                   {"constant": False,
                                                    "inputs": [{"name": "_spender", "type": "address"},
                                                               {"name": "_value", "type": "uint256"}],
                                                    "name": "approve", "outputs": [{"name": "success", "type": "bool"}],
                                                    "payable": False, "stateMutability": "nonpayable",
                                                    "type": "function"},
                                                   {"constant": True, "inputs": [], "name": "totalSupply",
                                                    "outputs": [{"name": "", "type": "uint256", "value": "1e+36"}],
                                                    "payable": False, "stateMutability": "view", "type": "function"},
                                                   {"constant": False, "inputs": [{"name": "_from", "type": "address"},
                                                                                  {"name": "_to", "type": "address"},
                                                                                  {"name": "_value",
                                                                                   "type": "uint256"}],
                                                    "name": "transferFrom",
                                                    "outputs": [{"name": "success", "type": "bool"}], "payable": False,
                                                    "stateMutability": "nonpayable", "type": "function"},
                                                   {"constant": True, "inputs": [], "name": "decimals",
                                                    "outputs": [{"name": "", "type": "uint8", "value": "18"}],
                                                    "payable": False, "stateMutability": "view", "type": "function"},
                                                   {"constant": False,
                                                    "inputs": [{"name": "_value", "type": "uint256"}], "name": "burn",
                                                    "outputs": [{"name": "success", "type": "bool"}], "payable": False,
                                                    "stateMutability": "nonpayable", "type": "function"},
                                                   {"constant": True, "inputs": [{"name": "", "type": "address"}],
                                                    "name": "balanceOf",
                                                    "outputs": [{"name": "", "type": "uint256", "value": "0"}],
                                                    "payable": False, "stateMutability": "view", "type": "function"},
                                                   {"constant": False, "inputs": [{"name": "_from", "type": "address"},
                                                                                  {"name": "_value",
                                                                                   "type": "uint256"}],
                                                    "name": "burnFrom",
                                                    "outputs": [{"name": "success", "type": "bool"}], "payable": False,
                                                    "stateMutability": "nonpayable", "type": "function"},
                                                   {"constant": True, "inputs": [], "name": "symbol",
                                                    "outputs": [{"name": "", "type": "string", "value": "TNC1"}],
                                                    "payable": False, "stateMutability": "view", "type": "function"},
                                                   {"constant": False, "inputs": [{"name": "_to", "type": "address"},
                                                                                  {"name": "_value",
                                                                                   "type": "uint256"}],
                                                    "name": "transfer", "outputs": [], "payable": False,
                                                    "stateMutability": "nonpayable", "type": "function"},
                                                   {"constant": False,
                                                    "inputs": [{"name": "_spender", "type": "address"},
                                                               {"name": "_value", "type": "uint256"},
                                                               {"name": "_extraData", "type": "bytes"}],
                                                    "name": "approveAndCall",
                                                    "outputs": [{"name": "success", "type": "bool"}], "payable": False,
                                                    "stateMutability": "nonpayable", "type": "function"},
                                                   {"constant": True, "inputs": [{"name": "", "type": "address"},
                                                                                 {"name": "", "type": "address"}],
                                                    "name": "allowance",
                                                    "outputs": [{"name": "", "type": "uint256", "value": "0"}],
                                                    "payable": False, "stateMutability": "view", "type": "function"}, {
                                                       "inputs": [
                                                           {"name": "initialSupply", "type": "uint256", "index": 0,
                                                            "typeShort": "uint", "bits": "256",
                                                            "displayName": "initial Supply",
                                                            "template": "elements_input_uint",
                                                            "value": "1000000000000000000"},
                                                           {"name": "tokenName", "type": "string", "index": 1,
                                                            "typeShort": "string", "bits": "",
                                                            "displayName": "token Name",
                                                            "template": "elements_input_string", "value": "TNC1"},
                                                           {"name": "tokenSymbol", "type": "string", "index": 2,
                                                            "typeShort": "string", "bits": "",
                                                            "displayName": "token Symbol",
                                                            "template": "elements_input_string", "value": "TNC1"}],
                                                       "payable": False, "stateMutability": "nonpayable",
                                                       "type": "constructor"}, {"anonymous": False, "inputs": [
                                                      {"indexed": True, "name": "from", "type": "address"},
                                                      {"indexed": True, "name": "to", "type": "address"},
                                                      {"indexed": False, "name": "value", "type": "uint256"}],
                                                                                "name": "Transfer", "type": "event"},
                                                   {"anonymous": False,
                                                    "inputs": [{"indexed": False, "name": "value", "type": "uint256"}],
                                                    "name": "Logger", "type": "event"}, {"anonymous": False, "inputs": [
                                                      {"indexed": True, "name": "from", "type": "address"},
                                                      {"indexed": False, "name": "value", "type": "uint256"}],
                                                                                         "name": "Burn",
                                                                                         "type": "event"}]
ropsten_testnet_abi=[
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"name": "from",
				"type": "address"
			},
			{
				"indexed": True,
				"name": "to",
				"type": "address"
			},
			{
				"indexed": False,
				"name": "value",
				"type": "uint256"
			}
		],
		"name": "Transfer",
		"type": "event"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_spender",
				"type": "address"
			},
			{
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "approve",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "burn",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_from",
				"type": "address"
			},
			{
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "burnFrom",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "newAdmin",
				"type": "address"
			}
		],
		"name": "changeAdmin",
		"outputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "changeAll",
		"outputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_spender",
				"type": "address"
			},
			{
				"name": "_subtractedValue",
				"type": "uint256"
			}
		],
		"name": "decreaseApproval",
		"outputs": [
			{
				"name": "success",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "token",
				"type": "address"
			},
			{
				"name": "amount",
				"type": "uint256"
			}
		],
		"name": "emergencyERC20Drain",
		"outputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_spender",
				"type": "address"
			},
			{
				"name": "_addedValue",
				"type": "uint256"
			}
		],
		"name": "increaseApproval",
		"outputs": [
			{
				"name": "success",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "newPausedPublic",
				"type": "bool"
			},
			{
				"name": "newPausedOwnerAdmin",
				"type": "bool"
			}
		],
		"name": "pause",
		"outputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"name": "_burner",
				"type": "address"
			},
			{
				"indexed": False,
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "Burn",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"name": "previousOwner",
				"type": "address"
			},
			{
				"indexed": True,
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "OwnershipTransferred",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"name": "newState",
				"type": "bool"
			}
		],
		"name": "PauseOwnerAdmin",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"name": "newState",
				"type": "bool"
			}
		],
		"name": "PausePublic",
		"type": "event"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_to",
				"type": "address"
			},
			{
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "transfer",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"name": "previousAdmin",
				"type": "address"
			},
			{
				"indexed": True,
				"name": "newAdmin",
				"type": "address"
			}
		],
		"name": "AdminTransferred",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"name": "owner",
				"type": "address"
			},
			{
				"indexed": True,
				"name": "spender",
				"type": "address"
			},
			{
				"indexed": False,
				"name": "value",
				"type": "uint256"
			}
		],
		"name": "Approval",
		"type": "event"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_from",
				"type": "address"
			},
			{
				"name": "_to",
				"type": "address"
			},
			{
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "transferFrom",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "transferOwnership",
		"outputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "admin",
		"outputs": [
			{
				"name": "",
				"type": "address"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [
			{
				"name": "_owner",
				"type": "address"
			},
			{
				"name": "_spender",
				"type": "address"
			}
		],
		"name": "allowance",
		"outputs": [
			{
				"name": "",
				"type": "uint256"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [
			{
				"name": "_owner",
				"type": "address"
			}
		],
		"name": "balanceOf",
		"outputs": [
			{
				"name": "balance",
				"type": "uint256"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "decimals",
		"outputs": [
			{
				"name": "",
				"type": "uint8"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "name",
		"outputs": [
			{
				"name": "",
				"type": "string"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"name": "",
				"type": "address"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "pausedOwnerAdmin",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "pausedPublic",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "symbol",
		"outputs": [
			{
				"name": "",
				"type": "string"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "totalSupply",
		"outputs": [
			{
				"name": "",
				"type": "uint256"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	}
]
mainnet_testnet_abi=[
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"name": "from",
				"type": "address"
			},
			{
				"indexed": True,
				"name": "to",
				"type": "address"
			},
			{
				"indexed": False,
				"name": "value",
				"type": "uint256"
			}
		],
		"name": "Transfer",
		"type": "event"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_spender",
				"type": "address"
			},
			{
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "approve",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "burn",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_from",
				"type": "address"
			},
			{
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "burnFrom",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "newAdmin",
				"type": "address"
			}
		],
		"name": "changeAdmin",
		"outputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "changeAll",
		"outputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_spender",
				"type": "address"
			},
			{
				"name": "_subtractedValue",
				"type": "uint256"
			}
		],
		"name": "decreaseApproval",
		"outputs": [
			{
				"name": "success",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "token",
				"type": "address"
			},
			{
				"name": "amount",
				"type": "uint256"
			}
		],
		"name": "emergencyERC20Drain",
		"outputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_spender",
				"type": "address"
			},
			{
				"name": "_addedValue",
				"type": "uint256"
			}
		],
		"name": "increaseApproval",
		"outputs": [
			{
				"name": "success",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "newPausedPublic",
				"type": "bool"
			},
			{
				"name": "newPausedOwnerAdmin",
				"type": "bool"
			}
		],
		"name": "pause",
		"outputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"name": "_burner",
				"type": "address"
			},
			{
				"indexed": False,
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "Burn",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"name": "previousOwner",
				"type": "address"
			},
			{
				"indexed": True,
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "OwnershipTransferred",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"name": "newState",
				"type": "bool"
			}
		],
		"name": "PauseOwnerAdmin",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"name": "newState",
				"type": "bool"
			}
		],
		"name": "PausePublic",
		"type": "event"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_to",
				"type": "address"
			},
			{
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "transfer",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"name": "previousAdmin",
				"type": "address"
			},
			{
				"indexed": True,
				"name": "newAdmin",
				"type": "address"
			}
		],
		"name": "AdminTransferred",
		"type": "event"
	},
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"name": "owner",
				"type": "address"
			},
			{
				"indexed": True,
				"name": "spender",
				"type": "address"
			},
			{
				"indexed": False,
				"name": "value",
				"type": "uint256"
			}
		],
		"name": "Approval",
		"type": "event"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "_from",
				"type": "address"
			},
			{
				"name": "_to",
				"type": "address"
			},
			{
				"name": "_value",
				"type": "uint256"
			}
		],
		"name": "transferFrom",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": False,
		"inputs": [
			{
				"name": "newOwner",
				"type": "address"
			}
		],
		"name": "transferOwnership",
		"outputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "admin",
		"outputs": [
			{
				"name": "",
				"type": "address"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [
			{
				"name": "_owner",
				"type": "address"
			},
			{
				"name": "_spender",
				"type": "address"
			}
		],
		"name": "allowance",
		"outputs": [
			{
				"name": "",
				"type": "uint256"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [
			{
				"name": "_owner",
				"type": "address"
			}
		],
		"name": "balanceOf",
		"outputs": [
			{
				"name": "balance",
				"type": "uint256"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "decimals",
		"outputs": [
			{
				"name": "",
				"type": "uint8"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "name",
		"outputs": [
			{
				"name": "",
				"type": "string"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "owner",
		"outputs": [
			{
				"name": "",
				"type": "address"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "pausedOwnerAdmin",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "pausedPublic",
		"outputs": [
			{
				"name": "",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "symbol",
		"outputs": [
			{
				"name": "",
				"type": "string"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [],
		"name": "totalSupply",
		"outputs": [
			{
				"name": "",
				"type": "uint256"
			}
		],
		"payable": False,
		"stateMutability": "view",
		"type": "function"
	}
]


setting=SettingHolder()

if ENVIRON.get("CURRENT_ENVIRON") == "testnet":
    setting.setup_testnet()
elif ENVIRON.get("CURRENT_ENVIRON") == "mainnet":
    setting.setup_mainnet()
else:
    setting.setup_privtnet()




