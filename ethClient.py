import binascii
import rlp
from ethereum import utils
from ethereum.utils import ecsign, normalize_key, int_to_big_endian, checksum_encode, privtoaddr
from solc import compile_source, compile_files
from web3 import Web3, HTTPProvider
from ethereum.transactions import Transaction


CONTRACT_ADDRESS="0x65096f2b7a8dc1592479f1911cd2b98dae4d2218"
CONTRACT_ABI=[
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

def load_solidity_code(filepath):
    with open(filepath) as f:
        content = f.read()
        return content


def hander_contract_args(args):
    tmp_list = []
    for a in args:
        tmp_bytearray = bytearray(32)
        assert isinstance(a,str)
        if a[:2] == "0x":
            a = a[2:]
        len_of_a = len(bytes.fromhex(a))
        tmp_bytearray[-len_of_a:] = bytes.fromhex(a)

        tmp_list.append(tmp_bytearray.hex())

    return "".join(tmp_list)

class Client(object):

    def __init__(self, eth_url):
        self.web3 = Web3(HTTPProvider(eth_url))

    def get_privtKey_from_keystore(self,filename, password):
        with open(filename) as keyfile:
            encrypted_key = keyfile.read()
            private_key = self.web3.eth.account.decrypt(encrypted_key, password)
            print(private_key)
            return binascii.hexlify(private_key).decode()

    def transfer_erc20(self,addressFrom,addressTo,value,privtKey):
        '''
        erc20转账
        '''
        contract_instance = self.get_contract_instance(CONTRACT_ADDRESS, CONTRACT_ABI)
        tx = contract_instance.functions.transfer(
            checksum_encode(addressTo),
            int(value*(10**8))
        ).buildTransaction({
            'gasPrice': self.web3.eth.gasPrice,
            'nonce': self.web3.eth.getTransactionCount(checksum_encode(addressFrom)),
        })

        signed = self.web3.eth.account.signTransaction(tx, privtKey)
        tx_id=self.web3.eth.sendRawTransaction(signed.rawTransaction)

        return binascii.hexlify(tx_id).decode()


    def transfer_eth(self,addressFrom, addressTo, value, privtKey, data=b'', startgas=21000):
        '''
        eth转账
        '''
        tx = Transaction(
            nonce=self.web3.eth.getTransactionCount(addressFrom),
            gasprice=self.web3.eth.gasPrice,
            startgas=startgas,
            to=addressTo,
            value=value,
            data=data
        )

        tx.sign(privtKey)
        raw_tx = self.web3.toHex(rlp.encode(tx))
        tx_id = self.web3.eth.sendRawTransaction(raw_tx)
        return "0x" + binascii.hexlify(tx_id).decode()


    def construct_eth_tx(self, addressFrom, addressTo, value, gasLimit=21000,gasPrice=None):
        '''
        构造eth未签名交易
        '''
        tx = Transaction(
            nonce=self.web3.eth.getTransactionCount(addressFrom),
            gasprice=self.web3.eth.gasPrice if not gasPrice else gasPrice,
            startgas=gasLimit,
            to=addressTo,
            value=int(value*(10**18)),
            data=b''
        )
        UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])
        unsigned_tx = rlp.encode(tx, UnsignedTransaction)
        before_hash = utils.sha3(unsigned_tx)
        return binascii.hexlify(unsigned_tx).decode(),binascii.hexlify(before_hash).decode()

    def construct_erc20_tx(self,addressFrom,addressTo,value,gasPrice=None):
        '''
        构造eth未签名交易
        '''
        contract_instance=self.get_contract_instance(CONTRACT_ADDRESS, CONTRACT_ABI)
        tx_dict = contract_instance.functions.transfer(
            checksum_encode(addressTo),
            int(value*(10**8))
        ).buildTransaction({
            'from': addressFrom,
            'nonce': self.web3.eth.getTransactionCount(addressFrom),
        })

        tx = Transaction(
            nonce=tx_dict.get("nonce"),
            gasprice=tx_dict.get("gasPrice") if not gasPrice else gasPrice,
            startgas=tx_dict.get("gas"),
            to=tx_dict.get("to"),
            value=tx_dict.get("value"),
            data=binascii.unhexlify(tx_dict.get("data")[2:]))

        UnsignedTransaction = Transaction.exclude(['v', 'r', 's'])
        unsigned_tx = rlp.encode(tx, UnsignedTransaction)
        before_hash = utils.sha3(unsigned_tx)
        return binascii.hexlify(unsigned_tx).decode(),binascii.hexlify(before_hash).decode()


    def sign(self, unsigned_tx, privtKey):
        '''
        对交易签名
        '''
        before_hash = utils.sha3(binascii.unhexlify(unsigned_tx.encode()))
        v,r,s=ecsign(before_hash,normalize_key(privtKey))
        signature = binascii.hexlify(int_to_big_endian(r) + int_to_big_endian(s) +
                                     bytes(chr(v).encode())).decode()
        return signature




    def broadcast(self, unsigned_tx,signature):
        '''
        将未签名的交易和签名组装在一起广播出去
        '''
        signature=binascii.unhexlify(signature.encode())
        unsigned_tx=binascii.unhexlify(unsigned_tx.encode())
        r = signature[0:32]
        s = signature[32:64]
        v = bytes(chr(signature[64]).encode())

        unsigned_items = rlp.decode(unsigned_tx)
        unsigned_items.extend([v, r, s])
        signed_items = unsigned_items

        signed_tx_data = rlp.encode(signed_items)
        print(binascii.hexlify(signed_tx_data))
        tx_id = self.web3.eth.sendRawTransaction(signed_tx_data)
        return "0x"+binascii.hexlify(tx_id).decode()

    def sendTransaction(self,addressFrom, addressTo, value,startgas,data,privtKey):
        tx = Transaction(
            nonce=self.web3.eth.getTransactionCount(addressFrom),
            gasprice=self.web3.eth.gasPrice,
            startgas=startgas,
            to=addressTo,
            value=value,
            data=data
        )

        tx.sign(privtKey)
        raw_tx = self.web3.toHex(rlp.encode(tx))
        tx_id = self.web3.eth.sendRawTransaction(raw_tx)

        return tx_id.hex()


    def deploy_contract(self,contract_file_name, contract_name,addressFrom, privtKey,contract_args=None,import_remappings=[]):
        '''
        部署合约
        '''
        # compiled_sol = compile_source(solidity_code)
        compiled_sol = compile_files([contract_file_name],import_remappings=import_remappings)
        contract_interface = compiled_sol.get("{}:{}".format(contract_file_name, contract_name))
        bytecode = contract_interface['bin']
        if contract_args:
            bytecode += hander_contract_args(contract_args)
        data = binascii.unhexlify(bytecode.encode())
        gas_limit = self.web3.eth.estimateGas({"from": addressFrom, "value": "0x0", "data": bytecode})
        tx_id = self.sendTransaction(
                                addressFrom=addressFrom,
                                addressTo="",
                                value=0,
                                startgas=gas_limit,
                                data=data,
                                privtKey=privtKey
        )

        # tx_receipt = w3.eth.waitForTransactionReceipt(reszult)
        # contract_address = tx_receipt['contractAddress']

        return tx_id


    def get_contract_instance(self, contract_address, abi):
        '''
        获取合约实例
        '''
        contract = self.web3.eth.contract(address=checksum_encode(contract_address), abi=abi)
        return contract

    def invoke_contract(self, invoker, contract, method, args,gasPrice=None):
        '''
        调用合约里实现的方法
        '''
        tx_dict = contract.functions[method](*args).buildTransaction({
            'gasPrice': self.web3.eth.gasPrice if not gasPrice else gasPrice,
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
        return contract.functions.balanceOf(checksum_encode(address)).call()/(10**8)

    def get_transaction_by_hash(self,txId):
        res=self.web3.eth.getTransaction(txId)
        return res

    def get_transaction_receipt_by_hash(self,txId):
        res=self.web3.eth.getTransactionReceipt(txId)
        return res


    def get_gas_price(self):
        gas_price=self.web3.eth.gasPrice
        return gas_price

if __name__ == "__main__":

    myclient = Client("https://ropsten.infura.io/pZc5ZTRYM8wYfRPtoQal")
    contract = myclient.get_contract_instance(CONTRACT_ADDRESS, CONTRACT_ABI)


    a=myclient.sign_args(typeList=['bytes32', 'bytes32', 'uint256', 'uint256',"uint256"],
                         valueList=["0x3ae88fe370c39384fc16da2c9e768cf5d2495b48","0x537C8f3d3E18dF5517a58B3fB9D9143697996802",20,20,0],
                         privtKey="095e53c9c20e23fd01eaad953c01da9e9d3ed9bebcfed8e5b2c2fce94037d963")


    # TXID = myclient.deploy_contract("Rating.sol","RatingToken",
    #                "0x3aE88fe370c39384FC16dA2C9e768Cf5d2495b48","095e53c9c20e23fd01eaad953c01da9e9d3ed9bebcfed8e5b2c2fce94037d963",[])
    # print(TXID)
    pass
