import asyncio
import binascii

import time

import requests
from eth_account.datastructures import AttributeDict
from eth_utils import keccak
from py_ecc.secp256k1 import privtopub
# from solc import compile_source, compile_files
from ethereum import utils
from ethereum.utils import ecsign, ecrecover_to_pub, privtoaddr, big_endian_to_int, normalize_key, int_to_big_endian, \
    safe_ord, check_checksum, checksum_encode, sha3, encode_int32
from web3 import Web3, HTTPProvider
import rlp
from ethereum.transactions import Transaction

# w3 = Web3(HTTPProvider('http://192.168.28.139:8545'))
w3 = Web3(HTTPProvider('http://192.168.214.178:8545'))

method=binascii.hexlify( w3.sha3(text="Test(address,address,uint256,uint256,address)"))
# method=binascii.hexlify( w3.sha3(text="Transfer(address,address,uint256)"))
print("method:",method)
k="b6a03207128827eaae0d31d97a7a6243de31f2baf99eabd764e33389ecf436fc"
k = normalize_key(k)
print(k)
x, y = privtopub(k)
print(x,y)
print(encode_int32(x))
addr=sha3(encode_int32(x) + encode_int32(y))[12:]


print(addr)

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
# print(w3.eth.getTransactionCount("0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8"))
#
# gg=big_endian_to_int(b"\xd6\x18'\x1e\x1es\xf3\x11z\xb9{\xc6\xe6\x94\x87\xbf\xe2P\xf4\n\xfb[\xbb<9E\xddI\xe2\xe4\xa6\xa6")
# print(gg)


# tx = Transaction(
#     nonce=w3.eth.getTransactionCount("0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8"),
#     gasprice=w3.eth.gasPrice,
#     startgas=2560000,
#     to="0x537C8f3d3E18dF5517a58B3fB9D9143697996802",
#     value=100,
#     data=b''
# )

# tx = Transaction(
#     nonce=98,
#     gasprice=w3.eth.gasPrice,
#     startgas=2560000,
#     to="0x537C8f3d3E18dF5517a58B3fB9D9143697996802",
#     value=100,
#     data=b'',
#     # v=28,
#     # r=96837623906486680784052655012985722878022151455312662607219766671968890562214,
#     # s=14092329712025910985667934767468484568673182721842620151437634408917438344336
#
# )


privtKey="b6a03207128827eaae0d31d97a7a6243de31f2baf99eabd764e33389ecf436fc"
# #
# UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])
# #
# unsigned_tx=rlp.encode(tx,UnsignedTransaction)
# print("uuuuuuu:",rlp.decode(unsigned_tx))
#
# print ("unsigned_tx:",unsigned_tx,binascii.hexlify(unsigned_tx).decode())
# before_hash= utils.sha3(unsigned_tx)
#
# #
# # print("beforehash:",before_hash,binascii.hexlify(before_hash).decode())
# #
# # tx.sign(privtKey)
# # rawHash=binascii.hexlify(tx.hash)
# #
# # v=tx.v
# # r=tx.r
# # s=tx.s
# # print(v,r,s)
# # v,r,s=ecsign(before_hash,normalize_key(privtKey))
# # signature = binascii.hexlify(int_to_big_endian(r) + int_to_big_endian(s) + bytes(chr(v - 27).encode()))
# # print(signature)
# # signed_tx = w3.toHex(rlp.encode(tx))
# dd=rlp.decode(b"\xf8eb\x85\x040\xe24\x00\x83'\x10\x00\x94S|\x8f=>\x18\xdfU\x17\xa5\x8b?\xb9\xd9\x146\x97\x99h\x02d\x80\x1c\xa0\xd6\x18'\x1e\x1es\xf3\x11z\xb9{\xc6\xe6\x94\x87\xbf\xe2P\xf4\n\xfb[\xbb<9E\xddI\xe2\xe4\xa6\xa6\xa0\x1f'\xf9\xd8t .\xc1Do\x18\xe3\x88!\xb7\xfc\xd7\xe3\xe6\xc6&\x06\x93\x12\xb5\x95\xc6\xae\xe0T\xac\x90")
#
# signature =b"\xd6\x18'\x1e\x1es\xf3\x11z\xb9{\xc6\xe6\x94\x87\xbf\xe2P\xf4\n\xfb[\xbb<9E\xddI\xe2\xe4\xa6\xa6\x1f'\xf9\xd8t .\xc1Do\x18\xe3\x88!\xb7\xfc\xd7\xe3\xe6\xc6&\x06\x93\x12\xb5\x95\xc6\xae\xe0T\xac\x90\x01"
#
#
# r=signature[0:32]
# s=signature[32:64]
# v=bytes(chr(signature[64]+27).encode())
# print(dd)
# print(r,s,v)
# unsigned_items=rlp.decode(unsigned_tx)
# unsigned_items.extend([v,r,s])
# signed_items=unsigned_items
#
# reszult=rlp.encode(signed_items)
# print("reszult:",binascii.hexlify(reszult))

# tx.deserialize("e262850430e234008327100094537c8f3d3e18df5517a58b3fb9d91436979968026480")

# after_hash=w3.eth.sendRawTransaction(signed_tx)
# print("after_hash:",after_hash,binascii.hexlify(after_hash).decode())
#
#
# print ("signed_tx:",signed_tx)


pub1=privtopub("095e53c9c20e23fd01eaad953c01da9e9d3ed9bebcfed8e5b2c2fce94037d963")

class Client(object):

    def __init__(self,eth_url):
        self.web3=Web3(HTTPProvider(eth_url))

    def sign(self,tx,privtKey):
        signed = self.web3.eth.account.signTransaction(tx, privtKey)
        raw_data=signed.rawTransaction
        tx_id=signed.hash

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

    def construct_erc20_tx(self,transc):
        tx = Transaction(
            nonce=transc.get("nonce"),
            gasprice=transc.get("gasPrice"),
            startgas=transc.get("gas"),
            to=transc.get("to"),
            value=transc.get("value"),
            data=binascii.unhexlify(transc.get("data")[2:]))

        UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])
        unsigned_tx = rlp.encode(tx, UnsignedTransaction)
        return binascii.hexlify(unsigned_tx).decode()


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

        return transaction



    # def invoke_contract(self,contract,method,args):
    #
    #
    #
    #     transaction = contract.functions.transfer(
    #         "0x537C8f3d3E18dF5517a58B3fB9D9143697996802",
    #         10000
    #     ).buildTransaction({
    #         "gas": 100000,
    #         'gasPrice': self.web3.eth.gasPrice,
    #         'nonce': self.web3.eth.getTransactionCount("0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8"),
    #     })
    #
    #     privtKey = "b6a03207128827eaae0d31d97a7a6243de31f2baf99eabd764e33389ecf436fc"
    #     signed = self.web3.eth.account.signTransaction(transaction, privtKey)
    #
    #     raw = signed.rawTransaction
    #     print(binascii.hexlify(raw))
    #     tx_id = signed.hash
    #     print(binascii.hexlify(tx_id))
    #
    #     self.web3.eth.sendRawTransaction(signed.rawTransaction)

    def get_balance_of_eth(self,address):
        return self.web3.getBalance(address)

    def get_balance_of_erc20(self,contract,address):
        return contract.functions.balanceOf(address).call()




address="0x8AB0FC62b95AA25EE0FBd80eDc1252DDa670Aa6C"
abi=[{"constant": True, "inputs": [], "name": "name",
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
# my_contract = w3.eth.contract(address=address,abi=abi)

# my_client=Client("http://192.168.28.139:8545")
# contract_instance=my_client.get_contract_instance(address,abi)
# transc=my_client.invoke_contract(contract_instance,"transfer",("0x3aE88fe370c39384FC16dA2C9e768Cf5d2495b48",100))
# print(transc)
# unsigned_tx_data=my_client.construct_erc20_tx(transc)
# print(unsigned_tx_data)


# print(w3.eth.getBalance("0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8"))
#
# print(dir(my_contract))
# print(dir(my_contract.interface))
# print(dir(my_contract.abi))
# print(my_contract.functions.totalSupply().call())

def get_privtKey_from_keystore(filename,password):
    with open(filename) as keyfile:
        encrypted_key = keyfile.read()
        private_key = w3.eth.account.decrypt(encrypted_key, password)
        print(private_key)
        return binascii.hexlify(private_key).decode()

from enum import Enum
class ASSET_TYPE(Enum):
    TNC=2443
    NEO=1376
    GAS=1785
    ETH=1027

def get_price_from_coincapmarket(asset_type):
    coincapmarket_api="https://api.coinmarketcap.com/v2/ticker/{0}/?convert=CNY".format(asset_type)
    print(coincapmarket_api)
    res=requests.get(coincapmarket_api).json()
    return res.get("data").get("quotes").get("CNY").get("price")

#
# ff="0000000000000000000000009dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8"+"0000000000000000000000003aE88fe370c39384FC16dA2C9e768Cf5d2495b48" + "0000000000000000000000000000000000000000000000000000000000000005"
#
# gg=binascii.hexlify(Web3.sha3(hexstr=ff))


# eth_client=Client(eth_url="http://192.168.214.178:8545")
#
# tx=eth_client.construct_common_tx("0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8",
#                                "0x537C8f3d3E18dF5517a58B3fB9D9143697996802",
#                                100)
# signeddata=eth_client.sign(tx,"b6a03207128827eaae0d31d97a7a6243de31f2baf99eabd764e33389ecf436fc")
#
# res=eth_client.broadcast(signeddata["raw_data"])

pass


# [b'b', b'\x040\xe24\x00', b"'\x10\x00", b'S|\x8f=>\x18\xdfU\x17\xa5\x8b?\xb9\xd9\x146\x97\x99h\x02', b'd', b'']
# [b'b', b'\x040\xe24\x00', b"'\x10\x00", b'S|\x8f=>\x18\xdfU\x17\xa5\x8b?\xb9\xd9\x146\x97\x99h\x02', b'd', b'', b'\x1c', b"\xd6\x18'\x1e\x1es\xf3\x11z\xb9{\xc6\xe6\x94\x87\xbf\xe2P\xf4\n\xfb[\xbb<9E\xddI\xe2\xe4\xa6\xa6", b"\x1f'\xf9\xd8t .\xc1Do\x18\xe3\x88!\xb7\xfc\xd7\xe3\xe6\xc6&\x06\x93\x12\xb5\x95\xc6\xae\xe0T\xac\x90"]

#
# def checksum_encode(addr): # Takes a 20-byte binary address as input
#     o = ''
#     v = utils.big_endian_to_int(utils.sha3(addr))
#     for i, c in enumerate(addr.encode()):
#         if c in '0123456789':
#             o += c
#         else:
#             o += c.upper() if (v & (2**(255 - i))) else c.lower()
#     return '0x'+o

# dd=checksum_encode("8AB0FC62b95AA25EE0FBd80eDc1252DDa670Aa6C")
# print(dd)
dd=check_checksum("0x8aB0FC62b95AA25EE0FBd80eDc1252DDa670Aa6C")
print(dd)
cc=checksum_encode("0x8AB0FC62b95AA25EE0FBd80eDc1252DDa670Aa6c")
print(cc)