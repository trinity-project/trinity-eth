import binascii
import rlp
from ethereum import utils
from ethereum.utils import ecsign, normalize_key, int_to_big_endian, checksum_encode
from web3 import Web3, HTTPProvider
from ethereum.transactions import Transaction
from config import setting

class Client(object):

    def __init__(self, eth_url):
        self.web3 = Web3(HTTPProvider(eth_url))

    def get_contract_instance(self, contract_address, abi):
        contract = self.web3.eth.contract(address=checksum_encode(contract_address), abi=abi)
        return contract

    def invoke_contract(self, invoker, contract, method, args,gasLimit=800000):
        tx_dict = contract.functions[method](*args).buildTransaction({
            "gas": gasLimit,
            'gasPrice': self.web3.eth.gasPrice,
            'nonce': self.web3.eth.getTransactionCount(checksum_encode(invoker)),
        })
        tx = Transaction(
            nonce=tx_dict.get("nonce"),
            gasprice=tx_dict.get("gasPrice"),
            startgas=tx_dict.get("gas"),
            to=tx_dict.get("to"),
            value=tx_dict.get("value"),
            data=binascii.unhexlify(tx_dict.get("data")[2:]))

        UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])
        unsigned_tx = rlp.encode(tx, UnsignedTransaction)

        return binascii.hexlify(unsigned_tx).decode()

    def sign(self, unsigned_tx, privtKey):
        before_hash = utils.sha3(binascii.unhexlify(unsigned_tx.encode()))
        v,r,s=ecsign(before_hash,normalize_key(privtKey))
        signature = binascii.hexlify(int_to_big_endian(r) + int_to_big_endian(s) +
                                     bytes(chr(v).encode())).decode()
        return signature

    def broadcast(self, unsigned_tx,signature):
        signature=binascii.unhexlify(signature.encode())
        unsigned_tx=binascii.unhexlify(unsigned_tx.encode())
        r = signature[0:32]
        s = signature[32:64]
        v = bytes(chr(signature[64]).encode())

        unsigned_items = rlp.decode(unsigned_tx)
        unsigned_items.extend([v, r, s])
        signed_items = unsigned_items

        signed_tx_data = rlp.encode(signed_items)
        tx_id = self.web3.eth.sendRawTransaction(signed_tx_data)
        return "0x"+binascii.hexlify(tx_id).decode()


    def sign_args(self,typeList, valueList, privtKey):
        '''

        :param typeList: ['bytes32', 'bytes32', 'uint256', 'uint256']
        :param valueList: ["0x3ae88fe370c39384fc16da2c9e768cf5d2495b48", "0x9da26fc2e1d6ad9fdd46138906b0104ae68a65d8", 1, 1]
        :param privtKey: "095e53c9c20e23fd01eaad953c01da9e9d3ed9bebcfed8e5b2c2fce94037d963"
        :return:
        '''
        data_hash = Web3.soliditySha3(typeList, valueList)
        
        v, r, s = ecsign(data_hash, normalize_key(privtKey))
        signature = binascii.hexlify(int_to_big_endian(r) + int_to_big_endian(s)
                                     + bytes(chr(v - 27).encode()))
        return signature

    def call_contract(self,contract,method,args):
        return contract.functions[method](*args).call()


    def contruct_Transaction(self, invoker, contract, method, args, privateKey, gasLimit=4600000):
        tx_dict = contract.functions[method](*args).buildTransaction({
            "gas": gasLimit,
            'gasPrice': self.web3.eth.gasPrice*2,
            'nonce': self.web3.eth.getTransactionCount(checksum_encode(invoker)),
        })
        signed = self.web3.eth.account.signTransaction(tx_dict, privateKey)
        tx_id = self.web3.eth.sendRawTransaction(signed.rawTransaction)

        return binascii.hexlify(tx_id).decode()

'''
if __name__ == "__main__":
    abi=[ { "constant": True, "inputs": [], "name": "name", "outputs": [ { "name": "", "type": "string", "value": "W0BT" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_to", "type": "address" }, { "name": "_tokenId", "type": "uint256" } ], "name": "approve", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [ { "name": "_tokenId", "type": "uint256" } ], "name": "getNFTbyTokenId", "outputs": [ { "name": "attribute", "type": "string" }, { "name": "birthTime", "type": "uint256" }, { "name": "status", "type": "bool" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": True, "inputs": [], "name": "totalSupply", "outputs": [ { "name": "", "type": "uint256", "value": "0" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_idArray", "type": "uint256[]" }, { "name": "_owner", "type": "address" } ], "name": "createNFT", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": False, "inputs": [ { "name": "_from", "type": "address" }, { "name": "_to", "type": "address" }, { "name": "_tokenId", "type": "uint256" } ], "name": "transferFrom", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": False, "inputs": [ { "name": "_newOwner", "type": "address" } ], "name": "setCEO", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [], "name": "getAllTokens", "outputs": [ { "name": "", "type": "uint256[]", "value": [ "0" ] } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [], "name": "unpause", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [], "name": "paused", "outputs": [ { "name": "", "type": "bool", "value": False } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": True, "inputs": [ { "name": "_tokenId", "type": "uint256" } ], "name": "ownerOf", "outputs": [ { "name": "owner", "type": "address", "value": "0x" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": True, "inputs": [ { "name": "_owner", "type": "address" } ], "name": "balanceOf", "outputs": [ { "name": "count", "type": "uint256", "value": "1" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": True, "inputs": [], "name": "WOBOwner", "outputs": [ { "name": "", "type": "address", "value": "0x6a9a07a7e4bc5faef2f53a6d341fa4977077e340" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [], "name": "pause", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": True, "inputs": [ { "name": "_owner", "type": "address" } ], "name": "tokensOfOwner", "outputs": [ { "name": "", "type": "uint256[]", "value": [ "0" ] } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": True, "inputs": [], "name": "symbol", "outputs": [ { "name": "", "type": "string", "value": "WOB" } ], "payable": False, "stateMutability": "view", "type": "function" }, { "constant": False, "inputs": [ { "name": "_to", "type": "address" }, { "name": "_tokenId", "type": "uint256" } ], "name": "transfer", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "constant": False, "inputs": [ { "name": "_tokenId", "type": "uint256" }, { "name": "attribute", "type": "string" }, { "name": "status", "type": "bool" } ], "name": "setNFTbyTokenId", "outputs": [], "payable": False, "stateMutability": "nonpayable", "type": "function" }, { "inputs": [], "payable": True, "stateMutability": "payable", "type": "constructor" }, { "anonymous": False, "inputs": [ { "indexed": False, "name": "owner", "type": "address" }, { "indexed": False, "name": "tokenId", "type": "uint256" } ], "name": "Create", "type": "event" }, { "anonymous": False, "inputs": [ { "indexed": False, "name": "from", "type": "address" }, { "indexed": False, "name": "to", "type": "address" }, { "indexed": False, "name": "tokenId", "type": "uint256" } ], "name": "Transfer", "type": "event" }, { "anonymous": False, "inputs": [ { "indexed": False, "name": "owner", "type": "address" }, { "indexed": False, "name": "approved", "type": "address" }, { "indexed": False, "name": "tokenId", "type": "uint256" } ], "name": "Approval", "type": "event" } ]
    myclient = Client("https://ropsten.infura.io/pZc5ZTRYM8wYfRPtoQal")
    contract = myclient.get_contract_instance(contract_address="0x733e8130533dcdbb1637f08e1db4d86ad811d8ac",
                                              abi=abi)

    import time
    # print(myclient.call_contract(contract,"WOBOwner",[]))
    t1=time.time()
    unsigned_tx=myclient.invoke_contract("0xBF3De70657B3C346E72720657Bbc75AbFc4Ec217",contract,"createNFT",[[5,6,7],"0xBF3De70657B3C346E72720657Bbc75AbFc4Ec217"])
    t2=time.time()
    print(t2-t1)
    print(unsigned_tx)

    # signature=myclient.sign(unsigned_tx,"9f56b1bc6c7ae9a715c7af2415f4c8c72ea3e2ebb8479b516918ae19dd3354ab")
    # print(signature)
    # tx_id=myclient.broadcast(unsigned_tx,signature)
    # print(tx_id)

    pass
'''
