
import os

ENVIRON = os.environ


class SettingHolder(object):

    def setup_mainnet(self):
        self.ETH_URL = "https://mainnet.infura.io/pZc5ZTRYM8wYfRPtoQal"

        self.SmartContract = {
            "ERC20TNC": (
                "0xc9ad73d11d272c95b5a2c48780a55b6b3c726cac",
                mainnet_testnet_abi)}
        self.ABI_MAPPING = {
            "0xc9ad73d11d272c95b5a2c48780a55b6b3c726cac": erc721_abi
        }

        self.CONTRACT_ADDRESS = "0xc9ad73d11d272c95b5a2c48780a55b6b3c726cac"


    def setup_testnet(self):
        self.ETH_URL = "https://ropsten.infura.io/pZc5ZTRYM8wYfRPtoQal"
        self.SmartContract = {
            "ERC20TNC": (
                "0x65096f2B7A8dc1592479F1911cd2B98dae4d2218",
                ropsten_testnet_abi)}
        self.ABI_MAPPING = {
            "0x65096f2B7A8dc1592479F1911cd2B98dae4d2218": erc721_abi
        }

        self.CONTRACT_ADDRESS = "0x65096f2b7a8dc1592479f1911cd2b98dae4d2218"



    def setup_private_net(self):
        self.ETH_URL = "https://ropsten.infura.io/pZc5ZTRYM8wYfRPtoQal" 
        self.ASSET_CONTRACT_ADDRESS = "0x593d4581b7c012bD62a2018883308759b40Bd50a"
        self.ASSET_CONTRACT_ABI = ERC20_abi
        #self.ETH_CONTRACT_ADDRESS = "0xB50D0542E190D5F86a79D329e562F2Bab35f5B44"  SUCCESS
        self.ETH_CONTRACT_ADDRESS = "0x181098d6fbe45C171937351c5bE3ac7b44691435" 
        self.ETH_CONTRACT_ABI = eth_contract_abi


ERC20_abi = [
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
				"name": "success",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
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
				"name": "success",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
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
				"name": "success",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"constant": True,
		"inputs": [
			{
				"name": "",
				"type": "address"
			}
		],
		"name": "balanceOf",
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
				"name": "success",
				"type": "bool"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
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
				"name": "_value",
				"type": "uint256"
			},
			{
				"name": "_extraData",
				"type": "bytes"
			}
		],
		"name": "approveAndCall",
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
		"constant": True,
		"inputs": [
			{
				"name": "",
				"type": "address"
			},
			{
				"name": "",
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
		"inputs": [
			{
				"name": "initialSupply",
				"type": "uint256"
			},
			{
				"name": "tokenName",
				"type": "string"
			},
			{
				"name": "tokenSymbol",
				"type": "string"
			}
		],
		"payable": False,
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
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
		"anonymous": False,
		"inputs": [
			{
				"indexed": True,
				"name": "from",
				"type": "address"
			},
			{
				"indexed": False,
				"name": "value",
				"type": "uint256"
			}
		],
		"name": "Burn",
		"type": "event"
	}
]

eth_contract_abi = [
	{
		"anonymous": False,
		"inputs": [
			{
				"indexed": False,
				"name": "channelId",
				"type": "bytes32"
			},
			{
				"indexed": False,
				"name": "sender",
				"type": "address"
			},
			{
				"indexed": False,
				"name": "receiver",
				"type": "address"
			}
		],
		"name": "WithdrawFailure",
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
				"name": "re_addr",
				"type": "address"
			}
		],
		"name": "Logger",
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
				"name": "tokenValue",
				"type": "address"
			}
		],
		"name": "SetToken",
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
		"name": "UpdateDeposit",
		"type": "event"
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

setting = SettingHolder()
'''
if ENVIRON.get("CURRENT_ENVIRON") == "testnet":
    setting.setup_testnet()
elif ENVIRON.get("CURRENT_ENVIRON") == "mainnet":
    setting.setup_mainnet()
else:
'''
setting.setup_private_net()


