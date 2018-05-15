import binascii

import time

from eth_account.datastructures import AttributeDict
from py_ecc.secp256k1 import privtopub
from solc import compile_source, compile_files
from ethereum import utils
from ethereum.utils import ecsign, ecrecover_to_pub, privtoaddr
from web3 import Web3, HTTPProvider
import rlp
from ethereum.transactions import Transaction

w3 = Web3(HTTPProvider('http://192.168.214.178:8545'))
# w3 = Web3(HTTPProvider('http://192.168.28.139:8545'))

method=binascii.hexlify( w3.sha3(text="depoist2(uint256)"))







def sendTransaction(addressFrom,addressTo,value,privtKey,data=b'',startgas=2560000):

    tx = Transaction(
        nonce=w3.eth.getTransactionCount(addressFrom),
        gasprice=w3.eth.gasPrice,
        startgas=startgas,
        to=addressTo,
        value=value,
        data=data
    )

    tx.sign(privtKey)
    raw_tx = w3.toHex(rlp.encode(tx))

    tx_id=w3.eth.sendRawTransaction(raw_tx)

    return "0x"+binascii.hexlify(tx_id).decode()



contract_source_code = '''
pragma solidity ^0.4.18;

interface token {
    function transfer(address receiver, uint amount) external;
}

contract test_invoke {
    token public tokenReward;

    function test_invoke (
        address addressOfTokenUsedAsReward
    ) public{

        tokenReward = token(addressOfTokenUsedAsReward);
    }


    function () payable public {

        tokenReward.transfer(msg.sender, 100000000);
    }
}
'''

def deploy_contract(contract_source_code,addressFrom,privtKey):

    compiled_sol = compile_source(contract_source_code)
    print(compiled_sol.keys())
    contract_interface = compiled_sol["<stdin>:test_invoke"]
    bytecode=contract_interface['bin']
    data=binascii.unhexlify(bytecode.encode())
    reszult=sendTransaction(addressFrom=addressFrom,
                    addressTo="",
                    value=0,
                    data=data,
                    privtKey=privtKey)

    # tx_receipt = w3.eth.getTransactionReceipt(reszult)
    # contract_address = tx_receipt['contractAddress']

    return {
        "txid":reszult,
        # "contract_address":contract_address
    }


# res=deploy_contract(contract_source_code=contract_source_code,addressFrom="0x3aE88fe370c39384FC16dA2C9e768Cf5d2495b48",
#                 privtKey="095e53c9c20e23fd01eaad953c01da9e9d3ed9bebcfed8e5b2c2fce94037d963")


# data = 'a9059cbb000000000000000000000000537c8f3d3e18df5517a58b3fb9d91436979968020000000000000000000000000000000000000000000000000000000000002710'
# txid=sendTransaction(
#                 addressFrom="0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8",
#                 addressTo="0x15b0042D6E7c8f22fCB98c0C4bc76D19C3e51402",
#                 value=0,
#                 privtKey="b6a03207128827eaae0d31d97a7a6243de31f2baf99eabd764e33389ecf436fc",
#                 data=binascii.unhexlify(data.encode())
# )


#
# transaction = {
#     'gas': 2560000,
#     'to': '0x80C328dcFD607AB2da1E4A3949AC1b20d36b86FF',
#     'value': 100000000000000000,
#     'gasPrice': w3.eth.gasPrice,
#     'nonce': w3.eth.getTransactionCount("0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8"),
#     # 'chainId': None
# }
# privtKey="b6a03207128827eaae0d31d97a7a6243de31f2baf99eabd764e33389ecf436fc"
# signed = w3.eth.account.signTransaction(transaction, privtKey)
#
# raw=signed.rawTransaction
# tx_id=binascii.hexlify(signed.hash)

# w3.eth.sendRawTransaction(signed.rawTransaction)


# address="0x94Ab3ea9206038B9542a09a3fC4C914443dbad98"
# abi=[ { "constant": True, "inputs": [], "name": "name", "outputs": [ { "name": "", "type": "string", "value": "TNC3" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_spender", "type": "address" }, { "name": "_value", "type": "uint256" } ], "name": "approve", "outputs": [ { "name": "success", "type": "bool" } ], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [], "name": "totalSupply", "outputs": [ { "name": "", "type": "uint256", "value": "1e+29" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_from", "type": "address" }, { "name": "_to", "type": "address" }, { "name": "_value", "type": "uint256" } ], "name": "transferFrom", "outputs": [ { "name": "success", "type": "bool" } ], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [], "name": "decimals", "outputs": [ { "name": "", "type": "uint8", "value": "18" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_value", "type": "uint256" } ], "name": "burn", "outputs": [ { "name": "success", "type": "bool" } ], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [ { "name": "", "type": "address" } ], "name": "balanceOf", "outputs": [ { "name": "", "type": "uint256", "value": "1e+29" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_from", "type": "address" }, { "name": "_value", "type": "uint256" } ], "name": "burnFrom", "outputs": [ { "name": "success", "type": "bool" } ], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [], "name": "symbol", "outputs": [ { "name": "", "type": "string", "value": "TNC3" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_to", "type": "address" }, { "name": "_value", "type": "uint256" } ], "name": "transfer", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": False, "inputs": [ { "name": "_spender", "type": "address" }, { "name": "_value", "type": "uint256" }, { "name": "_extraData", "type": "bytes" } ], "name": "approveAndCall", "outputs": [ { "name": "success", "type": "bool" } ], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [ { "name": "", "type": "address" }, { "name": "", "type": "address" } ], "name": "allowance", "outputs": [ { "name": "", "type": "uint256", "value": "0" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "inputs": [ { "name": "initialSupply", "type": "uint256", "index": 0, "typeShort": "uint", "bits": "256", "displayName": "initial Supply", "template": "elements_input_uint", "value": "100000000000" }, { "name": "tokenName", "type": "string", "index": 1, "typeShort": "string", "bits": "", "displayName": "token Name", "template": "elements_input_string", "value": "TNC3" }, { "name": "tokenSymbol", "type": "string", "index": 2, "typeShort": "string", "bits": "", "displayName": "token Symbol", "template": "elements_input_string", "value": "TNC3" } ], "payable": False, "stateMutability": "nonpayable", "type": "constructor" }, { "anonymous": False, "inputs": [ { "indexed": True, "name": "from", "type": "address" }, { "indexed": True, "name": "to", "type": "address" }, { "indexed": False, "name": "value", "type": "uint256" } ], "name": "Transfer", "type": "event" }, { "anonymous": False, "inputs": [ { "indexed": True, "name": "from", "type": "address" }, { "indexed": False, "name": "value", "type": "uint256" } ], "name": "Burn", "type": "event" }, { "anonymous": False, "inputs": [ { "indexed": False, "name": "value", "type": "uint256" } ], "name": "Logger", "type": "event" } ]
#
# store_var_contract = w3.eth.contract(address=address,abi=abi)
# ddd=dir(store_var_contract.functions)
# transaction = store_var_contract.functions.approveAndCall(
# "0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8",100000,b''
# ).buildTransaction({
#     "gas":2560000,
#     'gasPrice': w3.eth.gasPrice,
#     'nonce': w3.eth.getTransactionCount("0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8"),
# })
#
#
# privtKey="b6a03207128827eaae0d31d97a7a6243de31f2baf99eabd764e33389ecf436fc"
# signed = w3.eth.account.signTransaction(transaction, privtKey)
#
# raw=signed.rawTransaction
# tx_id=binascii.hexlify( signed.hash)
#
# w3.eth.sendRawTransaction(signed.rawTransaction)

# add=ecrecover_to_pub(rawhash=b'VMFA\xfea}\xa6q\x11\x0c\xeb2QM\n \xb9\x8a\xb8\xc0\xe2U\xb11\xcd\xb1d\xf1\x9f\xfcL',
#                      v=28,
#                      r=19232881185755273564444963484854558308342991354574649254440192350924784797243,
#                      s=48265039148446167892303804482724631937759784570456316334174191275971178910768
#                      )
# pub=binascii.hexlify(add)
# 
# 

tx = Transaction(
    nonce=w3.eth.getTransactionCount("0x3aE88fe370c39384FC16dA2C9e768Cf5d2495b48"),
    gasprice=w3.eth.gasPrice,
    startgas=2560000,
    to="0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8",
    value=100000000,
    data=b''
)
privtKey="095e53c9c20e23fd01eaad953c01da9e9d3ed9bebcfed8e5b2c2fce94037d963"

UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])

before_hash=binascii.hexlify( utils.sha3(rlp.encode(tx,UnsignedTransaction)))

print("beforehash:",before_hash)

tx.sign(privtKey)
rawHash=binascii.hexlify(tx.hash)

v=tx.v
r=tx.r
s=tx.s
raw_tx = w3.toHex(rlp.encode(tx))

# tx_id=w3.eth.sendRawTransaction(raw_tx)

# pub1=privtopub("095e53c9c20e23fd01eaad953c01da9e9d3ed9bebcfed8e5b2c2fce94037d963")

class Client(object):

    def __init__(self,eth_url):
        self.web3=Web3(HTTPProvider(eth_url))

    def sign(self,tx,privtKey):
        signed = self.web3.eth.account.signTransaction(tx, privtKey)
        raw_data=signed.rawTransaction
        tx_id=binascii.unhexlify(signed.hash.encode())

        return {
            "raw_data":raw_data,
            "tx_id":tx_id
        }

    def broadcast(self,raw_data):

        return self.web3.eth.sendRawTransaction(raw_data)


    def construct_common_tx(self,addressFrom,addressTo,value,gasLimit=2560000):

        tx = {
            'gas': gasLimit,
            'to': addressTo,
            'value': value,
            'gasPrice': self.web3.eth.gasPrice,
            'nonce': self.web3.eth.getTransactionCount(addressFrom),
        }

        return tx

    def get_contract_instance(self,contract_address,abi):
        contract = self.web3.eth.contract(address=contract_address, abi=abi)
        return contract

    def invoke_contract(self,contract,method,args):



        transaction = contract.functions.transfer(
            "0x537C8f3d3E18dF5517a58B3fB9D9143697996802",
            10000
        ).buildTransaction({
            "gas": 100000,
            'gasPrice': self.web3.eth.gasPrice,
            'nonce': self.web3.eth.getTransactionCount("0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8"),
        })

        privtKey = "b6a03207128827eaae0d31d97a7a6243de31f2baf99eabd764e33389ecf436fc"
        signed = self.web3.eth.account.signTransaction(transaction, privtKey)

        raw = signed.rawTransaction
        tx_id = signed.hash

        self.web3.eth.sendRawTransaction(signed.rawTransaction)




address="0x8AB0FC62b95AA25EE0FBd80eDc1252DDa670Aa6C"
abi=[ { "constant": True, "inputs": [], "name": "name", "outputs": [ { "name": "", "type": "string", "value": "TNC1" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_spender", "type": "address" }, { "name": "_value", "type": "uint256" } ], "name": "approve", "outputs": [ { "name": "success", "type": "bool" } ], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [], "name": "totalSupply", "outputs": [ { "name": "", "type": "uint256", "value": "1e+36" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_from", "type": "address" }, { "name": "_to", "type": "address" }, { "name": "_value", "type": "uint256" } ], "name": "transferFrom", "outputs": [ { "name": "success", "type": "bool" } ], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [], "name": "decimals", "outputs": [ { "name": "", "type": "uint8", "value": "18" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_value", "type": "uint256" } ], "name": "burn", "outputs": [ { "name": "success", "type": "bool" } ], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [ { "name": "", "type": "address" } ], "name": "balanceOf", "outputs": [ { "name": "", "type": "uint256", "value": "0" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_from", "type": "address" }, { "name": "_value", "type": "uint256" } ], "name": "burnFrom", "outputs": [ { "name": "success", "type": "bool" } ], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [], "name": "symbol", "outputs": [ { "name": "", "type": "string", "value": "TNC1" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_to", "type": "address" }, { "name": "_value", "type": "uint256" } ], "name": "transfer", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": False, "inputs": [ { "name": "_spender", "type": "address" }, { "name": "_value", "type": "uint256" }, { "name": "_extraData", "type": "bytes" } ], "name": "approveAndCall", "outputs": [ { "name": "success", "type": "bool" } ], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [ { "name": "", "type": "address" }, { "name": "", "type": "address" } ], "name": "allowance", "outputs": [ { "name": "", "type": "uint256", "value": "0" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "inputs": [ { "name": "initialSupply", "type": "uint256", "index": 0, "typeShort": "uint", "bits": "256", "displayName": "initial Supply", "template": "elements_input_uint", "value": "1000000000000000000" }, { "name": "tokenName", "type": "string", "index": 1, "typeShort": "string", "bits": "", "displayName": "token Name", "template": "elements_input_string", "value": "TNC1" }, { "name": "tokenSymbol", "type": "string", "index": 2, "typeShort": "string", "bits": "", "displayName": "token Symbol", "template": "elements_input_string", "value": "TNC1" } ], "payable": False, "stateMutability": "nonpayable", "type": "constructor" }, { "anonymous": False, "inputs": [ { "indexed": True, "name": "from", "type": "address" }, { "indexed": True, "name": "to", "type": "address" }, { "indexed": False, "name": "value", "type": "uint256" } ], "name": "Transfer", "type": "event" }, { "anonymous": False, "inputs": [ { "indexed": False, "name": "value", "type": "uint256" } ], "name": "Logger", "type": "event" }, { "anonymous": False, "inputs": [ { "indexed": True, "name": "from", "type": "address" }, { "indexed": False, "name": "value", "type": "uint256" } ], "name": "Burn", "type": "event" } ]

store_var_contract = w3.eth.contract(address=address,abi=abi)

ddddd=store_var_contract.events.Logger.createFilter(fromBlock=0,toBlock="latest")

transfer_filter = store_var_contract.eventFilter('Transfer')
while True:
    aa=transfer_filter.get_new_entries()
    for a in aa:
        print(a.args)
    time.sleep(2)


pass
