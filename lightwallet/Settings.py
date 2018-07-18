
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
        self.TNC = "0x65096f2B7A8dc1592479F1911cd2B98dae4d2218"
        self.TNCabi = testnet_abi
        self.create_client()
    def setup_privnet(self):
        self.NET_NAME = "PrivateNet"
        self.NODEURL = "http://localhost:8888"
        self.TNC = "0x0c34a8fd0109df360c7cf7ca454404901db77f5e"
        self.create_client()

    def create_client(self):
        self.EthClient = Client(self.NODEURL)


settings = SettingsHolder()

testnet_abi =[
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
mainnet_testnet_abi = [
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
