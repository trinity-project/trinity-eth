import binascii
import requests
from ethereum.utils import ecsign, normalize_key, int_to_big_endian, checksum_encode
from web3 import Web3, HTTPProvider
from ethereum.utils import sha3, is_string, encode_hex, checksum_encode
from trinity import GWEI_COEFFICIENT
from common.log import LOG
from random import randint


def get_privtKey_from_keystore(filename,password):
    with open(filename) as keyfile:
        encrypted_key = keyfile.read()
        private_key = Web3.eth.account.decrypt(encrypted_key, password)
        print(private_key)
        return binascii.hexlify(private_key).decode()

from enum import Enum
class ASSET_TYPE(Enum):
    TNC=2443
    ETH=1027

def get_price_from_coincapmarket(asset_type):
    coincapmarket_api="https://api.coinmarketcap.com/v2/ticker/{0}/?convert=CNY".format(asset_type)
    print(coincapmarket_api)
    res=requests.get(coincapmarket_api).json()
    return res.get("data").get("quotes").get("CNY").get("price")


class Client(object):

    _gwei_coeficient = GWEI_COEFFICIENT

    def __init__(self, eth_url):
        self.web3 = Web3(HTTPProvider(eth_url))

    def construct_common_tx(self, addressFrom, addressTo, value, gasLimit=None):
        tx = {
            'gas': gasLimit if gasLimit else 4500000,
            'to': addressTo,
            'value': int(value*10**18),
            'gasPrice': self.web3.eth.gasPrice,
            'nonce': self.web3.eth.getTransactionCount(addressFrom),
        }
        return tx



    def get_contract_instance(self, contract_address, abi):
        """

        :param contract_address:
        :param abi:
        :return:
        """
        return self.web3.eth.contract(address=checksum_encode(contract_address), abi=abi)


    def construct_erc20_tx(self, contract,addressFrom, addressTo,value, gasLimit=None, gasprice=None):
        tx_d = {

            'gasPrice': self.web3.eth.gasPrice * 2 if not gasprice  else gasprice,
            'nonce': self.web3.eth.getTransactionCount(checksum_encode(addressFrom)),
        }
        if gasLimit:
            tx_d.update({"gas": gasLimit})

        tx = contract.functions.transfer(
            checksum_encode(addressTo),
            int(value)
        ).buildTransaction(tx_d)
        return tx

    def invoke_contract(self, invoker, contract, method, args):
        tx = contract.functions[method](*args
                                        ).buildTransaction({
            "gas": 2560000,
            'gasPrice': self.web3.eth.gasPrice,
            'nonce': self.web3.eth.getTransactionCount(invoker),
        })

        return tx

    def sign(self, tx, privtKey):
        signed = self.web3.eth.account.signTransaction(tx, privtKey)
        raw_data = signed.rawTransaction

        return raw_data

    def broadcast(self, raw_data):
        return self.web3.eth.sendRawTransaction(raw_data)

    def int_to_big_endian(self, value):
        return value.to_bytes(32, 'big')

    def sign_args(self,typeList, valueList, privtKey):
        '''
        :param typeList: ['bytes32', 'bytes32', 'uint256', 'uint256']
        :param valueList: ["0x3ae88fe370c39384fc16da2c9e768cf5d2495b48", "0x9da26fc2e1d6ad9fdd46138906b0104ae68a65d8", 1, 1]
        :param privtKey: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        :return:
        '''
        data_hash = self.solidity_hash(typeList, valueList)
        v, r, s = ecsign(data_hash, normalize_key(privtKey))
        signature = self.int_to_big_endian(r) + self.int_to_big_endian(s) + bytes(chr(v - 27).encode())
        return signature.hex()

    def solidity_hash(self, typeList, valueList):
        """

        :param typeList:
        :param valueList:
        :param privtkey:
        :return:
        """
        return Web3.soliditySha3(typeList, valueList)


    def get_balance_of_eth(self,address):
        """

        :param address:
        :return:
        """
        return self.web3.eth.getBalance(checksum_encode(address))/(10**18)

    def get_balance_of_erc20(self,contract_address, abi, address):
        """

        :param contract_address:
        :param abi:
        :param address:
        :return:
        """
        contract = self.get_contract_instance(checksum_encode(contract_address), abi)
        return contract.functions.balanceOf(checksum_encode(address)).call()/(10**8)

    def get_approved_asset(self, contract_address, abi, approver, spender):
        """
        :param contract_address:
        :param abi:
        :param approver: the owner address of asset
        :param spender: the address be authorized to spend
        :return:
        """
        contract = self.get_contract_instance(checksum_encode(contract_address), abi)
        return contract.functions.allowance(approver, spender).call()/(10**8)

    def get_block_count(self):
        """

        :return:
        """
        return self.web3.eth.blockNumber

    def get_block(self,block_identifier, full_transactions=False):
        """

        :param block_identifier:
        :param full_transactions:
        :return:
        """
        return self.web3.eth.getBlock(block_identifier,full_transactions)

    def get_fitler_log(self, filter_id):
        """

        :param filter_id:
        :return:
        """
        return self.web3.eth.getFilterLogs(filter_id)


    def call_contract(self,contract, method, args):
        return contract.functions[method](*args).call()

    def contruct_transaction(self, invoker, contract, method, args, key, gwei_coef=None, gasLimit=4500000):
        """"""
        try:
            # pre-check the transaction
            estimate_gas = contract.functions[method](*args).estimateGas({'from': checksum_encode(invoker)})
            gasLimit = estimate_gas + 5000 + randint(1, 10000)
        except Exception as error:
            LOG.debug('Failed to execute {}. Exception: {}'.format(method, error))
            LOG.info('the parameters are : {}'.format(args))
        finally:
            LOG.debug('Estimated to spend {} gas'.format(gasLimit))
            tx_dict = contract.functions[method](*args).buildTransaction({
                'gas': gasLimit,
                'gasPrice': pow(10, 9) * gwei_coef,
                'nonce': self.web3.eth.getTransactionCount(checksum_encode(invoker)),
            })
            signed = self.web3.eth.account.signTransaction(tx_dict, key)
            tx_id = self.web3.eth.sendRawTransaction(signed.rawTransaction)

            return binascii.hexlify(tx_id).decode()

    def get_transaction_receipt(self, hashString):
        return self.web3.eth.getTransactionReceipt(hashString)

    @classmethod
    def set_gas_price(cls, coef=1):
        cls._gwei_coeficient = coef

    @classmethod
    def get_gas_price(cls):
        return cls._gwei_coeficient

    # @staticmethod
    # def get_estimate_gas(invoker, contract, method, args):
    #     return  contract.functions[method](*args).estimateGas({'from': invoker})
