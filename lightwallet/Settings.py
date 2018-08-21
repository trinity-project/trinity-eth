
import os
from blockchain.web3client import Client
from trinity import SUPPORTED_ASSET_TYPE


class SettingsHolder:

    headers = {
        "Content-Type": "application/json"
    }

    DIR_CURRENT = os.path.dirname(os.path.abspath(__file__))
    ADDRESS_VERSION = 23

    #TNC = "0x0c34a8fd0109df360c7cf7ca454404901db77f5e"


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
        self.TNC = SUPPORTED_ASSET_TYPE['TNC']
        self.TNC_abi = erc20_asset_abi
        self.Eth_Contract_address = "0xdE5909c60f90b79a23ecF812a65dc649191dBafC" #"0x1002D9FE1afD4DDB629E3fcdB578297EFf380106"
        self.Eth_Contract_abi = eth_contract_abi
        self.create_client()
    def setup_privnet(self):
        self.NET_NAME = "PrivateNet"
        self.NODEURL = "http://localhost:8888"
        self.TNC = "0x0c34a8fd0109df360c7cf7ca454404901db77f5e"
        self.create_client()

    def create_client(self):
        self.EthClient = Client(self.NODEURL)


settings = SettingsHolder()

erc20_asset_abi =[
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

eth_contract_abi = [
    {
        "constant": False,
        "inputs": [
            {
                "name": "_dataContract",
                "type": "address"
            }
        ],
        "name": "setDataContract",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            }
        ],
        "name": "getChannelBalance",
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
        "constant": False,
        "inputs": [
            {
                "name": "tokenAddress",
                "type": "address"
            }
        ],
        "name": "setToken",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "debugInfo",
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
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "funder",
                "type": "address"
            },
            {
                "name": "funderBalance",
                "type": "uint256"
            },
            {
                "name": "partner",
                "type": "address"
            },
            {
                "name": "partnerBalance",
                "type": "uint256"
            },
            {
                "name": "closerSignature",
                "type": "bytes"
            },
            {
                "name": "partnerSignature",
                "type": "bytes"
            }
        ],
        "name": "quickCloseChannel",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "funderAddress",
                "type": "address"
            },
            {
                "name": "funderAmount",
                "type": "uint256"
            },
            {
                "name": "partnerAddress",
                "type": "address"
            },
            {
                "name": "partnerAmount",
                "type": "uint256"
            },
            {
                "name": "funderSignature",
                "type": "bytes"
            },
            {
                "name": "partnerSignature",
                "type": "bytes"
            }
        ],
        "name": "updateDeposit",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [],
        "name": "unpause",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "Mytoken",
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
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            }
        ],
        "name": "settleTransaction",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [],
        "name": "pause",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
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
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "funderAddress",
                "type": "address"
            },
            {
                "name": "funderAmount",
                "type": "uint256"
            },
            {
                "name": "partnerAddress",
                "type": "address"
            },
            {
                "name": "partnerAmount",
                "type": "uint256"
            },
            {
                "name": "funderSignature",
                "type": "bytes"
            },
            {
                "name": "partnerSignature",
                "type": "bytes"
            }
        ],
        "name": "deposit",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "sender",
                "type": "address"
            },
            {
                "name": "receiver",
                "type": "address"
            },
            {
                "name": "lockTime",
                "type": "uint256"
            },
            {
                "name": "lockAmount",
                "type": "uint256"
            },
            {
                "name": "partnerAsignature",
                "type": "bytes"
            },
            {
                "name": "partnerBsignature",
                "type": "bytes"
            },
            {
                "name": "lockHash",
                "type": "bytes32"
            }
        ],
        "name": "withdrawUpdate",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "trinityDataContract",
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
                "name": "channelId",
                "type": "bytes32"
            }
        ],
        "name": "getChannelStatus",
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
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "sender",
                "type": "address"
            },
            {
                "name": "receiver",
                "type": "address"
            },
            {
                "name": "lockTime",
                "type": "uint256"
            },
            {
                "name": "lockAmount",
                "type": "uint256"
            },
            {
                "name": "lockHash",
                "type": "bytes32"
            },
            {
                "name": "partnerAsignature",
                "type": "bytes"
            },
            {
                "name": "partnerBsignature",
                "type": "bytes"
            },
            {
                "name": "secret",
                "type": "bytes32"
            }
        ],
        "name": "withdraw",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "partnerA",
                "type": "address"
            },
            {
                "name": "updateBalanceA",
                "type": "uint256"
            },
            {
                "name": "partnerB",
                "type": "address"
            },
            {
                "name": "updateBalanceB",
                "type": "uint256"
            },
            {
                "name": "signedStringA",
                "type": "bytes"
            },
            {
                "name": "signedStringB",
                "type": "bytes"
            }
        ],
        "name": "updateTransaction",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "founder",
                "type": "address"
            },
            {
                "name": "founderBalance",
                "type": "uint256"
            },
            {
                "name": "partner",
                "type": "address"
            },
            {
                "name": "partnerBalance",
                "type": "uint256"
            },
            {
                "name": "closerSignature",
                "type": "bytes"
            },
            {
                "name": "partnerSignature",
                "type": "bytes"
            }
        ],
        "name": "closeChannel",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "lockHash",
                "type": "bytes32"
            },
            {
                "name": "secret",
                "type": "bytes32"
            }
        ],
        "name": "withdrawSettle",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "name": "_tokenAddress",
                "type": "address"
            },
            {
                "name": "_dataAddress",
                "type": "address"
            }
        ],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "fallback"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "partnerA",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountA",
                "type": "uint256"
            },
            {
                "indexed": False,
                "name": "partnerB",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountB",
                "type": "uint256"
            }
        ],
        "name": "Deposit",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "partnerA",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountA",
                "type": "uint256"
            },
            {
                "indexed": False,
                "name": "partnerB",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountB",
                "type": "uint256"
            }
        ],
        "name": "UpdateDeposit",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "closer",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amount1",
                "type": "uint256"
            },
            {
                "indexed": False,
                "name": "partner",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amount2",
                "type": "uint256"
            }
        ],
        "name": "QuickCloseChannel",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "closer",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "partner",
                "type": "address"
            }
        ],
        "name": "CloseChannel",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "partnerA",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountA",
                "type": "uint256"
            },
            {
                "indexed": False,
                "name": "partnerB",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountB",
                "type": "uint256"
            }
        ],
        "name": "UpdateTransaction",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "partnerA",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountA",
                "type": "uint256"
            },
            {
                "indexed": False,
                "name": "partnerB",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountB",
                "type": "uint256"
            }
        ],
        "name": "Settle",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "hashLock",
                "type": "bytes32"
            }
        ],
        "name": "Withdraw",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "hashLock",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "balance",
                "type": "uint256"
            }
        ],
        "name": "WithdrawUpdate",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "hashLock",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "balance",
                "type": "uint256"
            }
        ],
        "name": "WithdrawSettle",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "timeoutBlock",
                "type": "uint256"
            }
        ],
        "name": "SetSettleTimeout",
        "type": "event"
    }
]

'''
eth_contract_abi = [
    
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "tokenValue",
                "type": "address"
            }
        ],
        "name": "SetToken",
        "type": "event"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "closer",
                "type": "address"
            },
            {
                "name": "closeBalance",
                "type": "uint256"
            },
            {
                "name": "partner",
                "type": "address"
            },
            {
                "name": "partnerBalance",
                "type": "uint256"
            },
            {
                "name": "closerSignature",
                "type": "bytes"
            },
            {
                "name": "partnerSignature",
                "type": "bytes"
            }
        ],
        "name": "closeChannel",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "funderAddress",
                "type": "address"
            },
            {
                "name": "funderAmount",
                "type": "uint256"
            },
            {
                "name": "partnerAddress",
                "type": "address"
            },
            {
                "name": "partnerAmount",
                "type": "uint256"
            },
            {
                "name": "funderSignature",
                "type": "bytes"
            },
            {
                "name": "partnerSignature",
                "type": "bytes"
            }
        ],
        "name": "deposit",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "closer",
                "type": "address"
            },
            {
                "name": "closerBalance",
                "type": "uint256"
            },
            {
                "name": "partner",
                "type": "address"
            },
            {
                "name": "partnerBalance",
                "type": "uint256"
            },
            {
                "name": "closerSignature",
                "type": "bytes"
            },
            {
                "name": "partnerSignature",
                "type": "bytes"
            }
        ],
        "name": "quickCloseChannel",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "blockNumber",
                "type": "uint256"
            }
        ],
        "name": "setSettleTimeout",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            }
        ],
        "name": "settleTransaction",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "tokenAddress",
                "type": "address"
            }
        ],
        "name": "setToken",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "funderAddress",
                "type": "address"
            },
            {
                "name": "funderAmount",
                "type": "uint256"
            },
            {
                "name": "partnerAddress",
                "type": "address"
            },
            {
                "name": "partnerAmount",
                "type": "uint256"
            },
            {
                "name": "funderSignature",
                "type": "bytes"
            },
            {
                "name": "partnerSignature",
                "type": "bytes"
            }
        ],
        "name": "updateDeposit",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "partnerA",
                "type": "address"
            },
            {
                "name": "updateBalanceA",
                "type": "uint256"
            },
            {
                "name": "partnerB",
                "type": "address"
            },
            {
                "name": "updateBalanceB",
                "type": "uint256"
            },
            {
                "name": "signedStringA",
                "type": "bytes"
            },
            {
                "name": "signedStringB",
                "type": "bytes"
            }
        ],
        "name": "updateTransaction",
        "outputs": [],
        "payable": True,
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "sender",
                "type": "address"
            },
            {
                "name": "receiver",
                "type": "address"
            },
            {
                "name": "lockTime",
                "type": "uint256"
            },
            {
                "name": "lockAmount",
                "type": "uint256"
            },
            {
                "name": "lockHash",
                "type": "bytes32"
            },
            {
                "name": "partnerAsignature",
                "type": "bytes"
            },
            {
                "name": "partnerBsignature",
                "type": "bytes"
            },
            {
                "name": "secret",
                "type": "bytes32"
            }
        ],
        "name": "withdraw",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "sender",
                "type": "address"
            },
            {
                "name": "receiver",
                "type": "address"
            },
            {
                "name": "lockTime",
                "type": "uint256"
            },
            {
                "name": "lockAmount",
                "type": "uint256"
            },
            {
                "name": "lockHash",
                "type": "bytes32"
            },
            {
                "name": "partnerAsignature",
                "type": "bytes"
            },
            {
                "name": "partnerBsignature",
                "type": "bytes"
            },
            {
                "name": "secret",
                "type": "bytes32"
            }
        ],
        "name": "withdrawSettle",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            },
            {
                "name": "nonce",
                "type": "uint256"
            },
            {
                "name": "sender",
                "type": "address"
            },
            {
                "name": "receiver",
                "type": "address"
            },
            {
                "name": "lockTime",
                "type": "uint256"
            },
            {
                "name": "lockAmount",
                "type": "uint256"
            },
            {
                "name": "lockHash",
                "type": "bytes32"
            },
            {
                "name": "partnerAsignature",
                "type": "bytes"
            },
            {
                "name": "partnerBsignature",
                "type": "bytes"
            }
        ],
        "name": "withdrawUpdate",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "hashLock",
                "type": "bytes32"
            }
        ],
        "name": "WithdrawUpdate",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "timeoutBlock",
                "type": "uint256"
            }
        ],
        "name": "SetSettleTimeout",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "hashLock",
                "type": "bytes32"
            }
        ],
        "name": "WithdrawSettle",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "hashLock",
                "type": "bytes32"
            }
        ],
        "name": "Withdraw",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "partnerA",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "partnerB",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountB",
                "type": "uint256"
            }
        ],
        "name": "Deposit",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "partnerA",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "partnerB",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountB",
                "type": "uint256"
            }
        ],
        "name": "DepositFalture",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "partnerA",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "partnerB",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountB",
                "type": "uint256"
            }
        ],
        "name": "UpdateDeposit",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "closer",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amount1",
                "type": "uint256"
            },
            {
                "indexed": False,
                "name": "partner",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amount2",
                "type": "uint256"
            }
        ],
        "name": "QuickCloseChannel",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "closer",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "partner",
                "type": "address"
            }
        ],
        "name": "CloseChannel",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "partnerA",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountA",
                "type": "uint256"
            },
            {
                "indexed": False,
                "name": "partnerB",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amountB",
                "type": "uint256"
            }
        ],
        "name": "UpdateTransaction",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "channleId",
                "type": "bytes32"
            },
            {
                "indexed": False,
                "name": "sender",
                "type": "address"
            },
            {
                "indexed": False,
                "name": "amount",
                "type": "uint256"
            }
        ],
        "name": "Settle",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": False,
                "name": "re_addr",
                "type": "address"
            }
        ],
        "name": "Logger",
        "type": "event"
    },
    {
        "inputs": [
            {
                "name": "token_address",
                "type": "address"
            },
            {
                "name": "Timeout",
                "type": "uint256"
            }
        ],
        "payable": True,
        "stateMutability": "payable",
        "type": "constructor"
    },
    {
        "constant": True,
        "inputs": [
            {
                "name": "channelId",
                "type": "bytes32"
            }
        ],
        "name": "getChannelBalance",
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
                "name": "channelId",
                "type": "bytes32"
            }
        ],
        "name": "getChannelById",
        "outputs": [
            {
                "name": "channelCloser",
                "type": "address"
            },
            {
                "name": "channelSettler",
                "type": "address"
            },
            {
                "name": "timeLockVerifier",
                "type": "address"
            },
            {
                "name": "partner1",
                "type": "address"
            },
            {
                "name": "partner2",
                "type": "address"
            },
            {
                "name": "channelTotalBalance",
                "type": "uint256"
            },
            {
                "name": "closingNonce",
                "type": "uint256"
            },
            {
                "name": "withdrawNonce",
                "type": "uint256"
            },
            {
                "name": "expectedSettleBlock",
                "type": "uint256"
            },
            {
                "name": "closerSettleBalance",
                "type": "uint256"
            },
            {
                "name": "partnerSettleBalance",
                "type": "uint256"
            },
            {
                "name": "channelStatus",
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
        "name": "getChannelCount",
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
        "inputs": [],
        "name": "Mytoken",
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
        "name": "trinityData",
        "outputs": [
            {
                "name": "channelNumber",
                "type": "uint8"
            },
            {
                "name": "settleTimeout",
                "type": "uint256"
            },
            {
                "name": "contractOwner",
                "type": "address"
            }
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]
'''