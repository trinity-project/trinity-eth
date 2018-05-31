import binascii
import rlp
from ethereum import utils
from ethereum.utils import ecsign, normalize_key,int_to_big_endian
from web3 import Web3, HTTPProvider
from ethereum.transactions import Transaction
from config import setting






class Client(object):

    def __init__(self, eth_url):
        self.web3 = Web3(HTTPProvider(eth_url))




    def construct_common_tx(self, addressFrom, addressTo, value, gasLimit=25600):
        tx = Transaction(
            nonce=self.web3.eth.getTransactionCount(addressFrom),
            gasprice=self.web3.eth.gasPrice,
            startgas=gasLimit,
            to=addressTo,
            value=int(value*(10**18)),
            data=b''
        )
        UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])
        unsigned_tx = rlp.encode(tx, UnsignedTransaction)
        before_hash = utils.sha3(unsigned_tx)
        return binascii.hexlify(unsigned_tx).decode(),binascii.hexlify(before_hash).decode()

    def construct_erc20_tx(self,addressFrom,addressTo,value,gasLimit=256000):
        contract_instance=self.get_contract_instance(setting.SmartContract["ERC20TNC"][0],
                                                     setting.SmartContract["ERC20TNC"][1])
        tx_dict = contract_instance.functions.transfer(
            addressTo,
            value
        ).buildTransaction({
            "gas": gasLimit,
            'gasPrice': self.web3.eth.gasPrice,
            'nonce': self.web3.eth.getTransactionCount(addressFrom),
        })

        tx = Transaction(
            nonce=tx_dict.get("nonce"),
            gasprice=tx_dict.get("gasPrice"),
            startgas=tx_dict.get("gas"),
            to=tx_dict.get("to"),
            value=int(tx_dict.get("value")*(10**8)),
            data=binascii.unhexlify(tx_dict.get("data")[2:]))

        UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])
        unsigned_tx = rlp.encode(tx, UnsignedTransaction)
        before_hash = utils.sha3(unsigned_tx)
        return binascii.hexlify(unsigned_tx).decode(),binascii.hexlify(before_hash).decode()


    def get_contract_instance(self, contract_address, abi):
        contract = self.web3.eth.contract(address=contract_address, abi=abi)
        return contract

    def invoke_contract(self, invoker, contract, method, args,gasLimit=2560000):
        tx_dict = contract.functions[method](*args).buildTransaction({
            "gas": gasLimit,
            'gasPrice': self.web3.eth.gasPrice,
            'nonce': self.web3.eth.getTransactionCount(invoker),
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
        print("before_hash:",before_hash)
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

    def get_balance_of_eth(self,address):
        return self.web3.eth.getBalance(address)/(10**18)

    def get_balance_of_erc20(self,contract,address):
        return contract.functions.balanceOf(address).call()/(10**8)

    def get_transaction_by_hash(self,txId):
        res=self.web3.eth.getTransaction(txId)
        return res

if __name__ == "__main__":
    myclient = Client("http://192.168.214.178:8545")
    contract = myclient.get_contract_instance(contract_address=setting.SmartContract["ERC20TNC"][0],
                                              abi=setting.SmartContract["ERC20TNC"][1])


    a=myclient.sign_args(typeList=['bytes32', 'bytes32', 'uint256', 'uint256',"uint256"],
                         valueList=["0x3ae88fe370c39384fc16da2c9e768cf5d2495b48","0x537C8f3d3E18dF5517a58B3fB9D9143697996802",20,20,0],
                         privtKey="095e53c9c20e23fd01eaad953c01da9e9d3ed9bebcfed8e5b2c2fce94037d963")

    print(a)

    pass
