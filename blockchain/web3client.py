import binascii
import requests
from ethereum.utils import ecsign, normalize_key, int_to_big_endian, checksum_encode
from web3 import Web3, HTTPProvider

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
        return self.web3.eth.contract(address=contract_address, abi=abi)


    def construct_erc20_tx(self, contract,addressFrom, addressTo,value, gasLimit=None, gasprice=None):
        tx_d = {

            'gasPrice': self.web3.eth.gasPrice * 2 if not gasprice  else gasprice,
            'nonce': self.web3.eth.getTransactionCount(addressFrom),
        }
        if gasLimit:
            tx_d.update({"gas": gasLimit})

        tx = contract.functions.transfer(
            addressTo,
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


    def sign_args(self,typeList, valueList, privtKey):
        '''
        :param typeList: ['bytes32', 'bytes32', 'uint256', 'uint256']
        :param valueList: ["0x3ae88fe370c39384fc16da2c9e768cf5d2495b48", "0x9da26fc2e1d6ad9fdd46138906b0104ae68a65d8", 1, 1]
        :param privtKey: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        :return:
        '''
        data_hash = self.solidity_hash(typeList, valueList)
        v, r, s = ecsign(data_hash, normalize_key(privtKey))
        signature = binascii.hexlify(int_to_big_endian(r) + int_to_big_endian(s) + bytes(chr(v - 27).encode()))
        return signature

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
        return self.web3.eth.getBalance(address)/(10**18)

    def get_balance_of_erc20(self,contract_address, abi, address):
        """

        :param contract_address:
        :param abi:
        :param address:
        :return:
        """
        contract = self.get_contract_instance(contract_address, abi)
        return contract.functions.balanceOf(address).call()/(10**8)

    def get_approved_asset(self, contract_address, abi, approver, spender):
        """
        :param contract_address:
        :param abi:
        :param approver: the owner address of asset
        :param spender: the address be authorized to spend
        :return:
        """
        contract = self.get_contract_instance(contract_address, abi)
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


    def call_contract(self,contract,method,args):
        return contract.functions[method](*args).call()


    def contruct_Transaction(self, invoker, contract, method, args, key, gwei_coef = 1):
        gas_price = self.web3.eth.gasPrice*10
        print('gas price: {}'.format(gas_price))
        tx_dict = contract.functions[method](*args).buildTransaction({
            'gasPrice': pow(10, 9) * gwei_coef,
            'nonce': self.web3.eth.getTransactionCount(checksum_encode(invoker)),
        })
        signed = self.web3.eth.account.signTransaction(tx_dict, key)
        tx_id = self.web3.eth.sendRawTransaction(signed.rawTransaction)

        return binascii.hexlify(tx_id).decode()

    def get_transaction_receipt(self, hashString):
        return self.web3.eth.getTransactionReceipt(hashString)


'''
if __name__ == "__main__":
    myclient = Client("https://ropsten.infura.io")
    print(myclient.get_block_count())
    abi = [{"constant":True,"inputs":[],
            "name":"name","outputs":[{"name":"","type":"string"}],
            "payable":False,"stateMutability":"view","type":"function"},
           {"constant":False,"inputs":[{"name":"_spender","type":"address"},
                                     {"name":"_value","type":"uint256"}],
          "name":"approve","outputs":[{"name":"success","type":"bool"}],
          "payable":False,"stateMutability":"nonpayable","type":"function"},
           {"constant":True,"inputs":[],"name":"totalSupply",
            "outputs":[{"name":"","type":"uint256"}],
            "payable":False,"stateMutability":"view","type":"function"},
           {"constant":True,"inputs":[],"name":"fundsWallet",
            "outputs":[{"name":"","type":"address"}],
            "payable":False,"stateMutability":"view","type":"function"},
           {"constant":False,"inputs":[{"name":"_from","type":"address"},
                                       {"name":"_to","type":"address"},
                                       {"name":"_value","type":"uint256"}],
            "name":"transferFrom","outputs":[{"name":"success","type":"bool"}],
            "payable":False,"stateMutability":"nonpayable","type":"function"},
           {"constant":True,"inputs":[],"name":"decimals",
            "outputs":[{"name":"","type":"uint8"}],
            "payable":False,"stateMutability":"view","type":"function"},
           {"constant":True,"inputs":[],"name":"version",
            "outputs":[{"name":"","type":"string"}],
            "payable":False,"stateMutability":"view","type":"function"},
           {"constant":True,"inputs":[],"name":"unitsOneEthCanBuy",
            "outputs":[{"name":"","type":"uint256"}],"payable":False,
            "stateMutability":"view","type":"function"},
           {"constant":True,"inputs":[{"name":"_owner","type":"address"}],
            "name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],
            "payable":False,"stateMutability":"view","type":"function"},
           {"constant":True,"inputs":[],"name":"totalEthInWei",
            "outputs":[{"name":"","type":"uint256"}],
            "payable":False,"stateMutability":"view","type":"function"},
           {"constant":True,"inputs":[],"name":"symbol",
            "outputs":[{"name":"","type":"string"}],
            "payable":False,"stateMutability":"view","type":"function"},
           {"constant":False,"inputs":[{"name":"_to","type":"address"},
                                       {"name":"_value","type":"uint256"}],
            "name":"transfer","outputs":[{"name":"success","type":"bool"}],
            "payable":False,"stateMutability":"nonpayable","type":"function"},
           {"constant":False,"inputs":[{"name":"_spender","type":"address"},
                                       {"name":"_value","type":"uint256"},
                                       {"name":"_extraData","type":"bytes"}],
            "name":"approveAndCall","outputs":[{"name":"success","type":"bool"}],
            "payable":False,"stateMutability":"nonpayable","type":"function"},
           {"constant":True,"inputs":[{"name":"_owner","type":"address"},
                                      {"name":"_spender","type":"address"}],
            "name":"allowance","outputs":[{"name":"remaining","type":"uint256"}],
            "payable":False,"stateMutability":"view","type":"function"},
           {"inputs":[],"payable":False,"stateMutability":"nonpayable","type":"constructor"},
           {"payable":True,"stateMutability":"payable","type":"fallback"},
           {"anonymous":False,"inputs":[{"indexed":True,"name":"_from","type":"address"},
                                        {"indexed":True,"name":"_to","type":"address"},
                                        {"indexed":False,"name":"_value","type":"uint256"}],
           "name":"Transfer","type":"event"},{"anonymous":False,
                                               "inputs":[{"indexed":True,"name":"_owner","type":"address"},
                                                         {"indexed":True,"name":"_spender","type":"address"},
                                                         {"indexed":False,"name":"_value","type":"uint256"}],
                                               "name":"Approval","type":"event"}]
    c = myclient.get_contract_instance("0x4c7A0D54ec5CbFFE4Ebe263F1F25aa53611521cB",abi=abi)

    balance = myclient.get_balance_of_erc20(c,"0xed630C05336D07787B1DAbC5dA1aD963cE47FC50")
    print(balance)




    # contract = myclient.get_contract_instance(contract_address="0x8AB0FC62b95AA25EE0FBd80eDc1252DDa670Aa6C",
    #                                           abi=[{"constant": True, "inputs": [], "name": "name",
    #                                                 "outputs": [{"name": "", "type": "string", "value": "TNC1"}],
    #                                                 "payable": False, "stateMutability": "view", "type": "function"},
    #                                                {"constant": False,
    #                                                 "inputs": [{"name": "_spender", "type": "address"},
    #                                                            {"name": "_value", "type": "uint256"}],
    #                                                 "name": "approve", "outputs": [{"name": "success", "type": "bool"}],
    #                                                 "payable": False, "stateMutability": "nonpayable",
    #                                                 "type": "function"},
    #                                                {"constant": True, "inputs": [], "name": "totalSupply",
    #                                                 "outputs": [{"name": "", "type": "uint256", "value": "1e+36"}],
    #                                                 "payable": False, "stateMutability": "view", "type": "function"},
    #                                                {"constant": False, "inputs": [{"name": "_from", "type": "address"},
    #                                                                               {"name": "_to", "type": "address"},
    #                                                                               {"name": "_value",
    #                                                                                "type": "uint256"}],
    #                                                 "name": "transferFrom",
    #                                                 "outputs": [{"name": "success", "type": "bool"}], "payable": False,
    #                                                 "stateMutability": "nonpayable", "type": "function"},
    #                                                {"constant": True, "inputs": [], "name": "decimals",
    #                                                 "outputs": [{"name": "", "type": "uint8", "value": "18"}],
    #                                                 "payable": False, "stateMutability": "view", "type": "function"},
    #                                                {"constant": False,
    #                                                 "inputs": [{"name": "_value", "type": "uint256"}], "name": "burn",
    #                                                 "outputs": [{"name": "success", "type": "bool"}], "payable": False,
    #                                                 "stateMutability": "nonpayable", "type": "function"},
    #                                                {"constant": True, "inputs": [{"name": "", "type": "address"}],
    #                                                 "name": "balanceOf",
    #                                                 "outputs": [{"name": "", "type": "uint256", "value": "0"}],
    #                                                 "payable": False, "stateMutability": "view", "type": "function"},
    #                                                {"constant": False, "inputs": [{"name": "_from", "type": "address"},
    #                                                                               {"name": "_value",
    #                                                                                "type": "uint256"}],
    #                                                 "name": "burnFrom",
    #                                                 "outputs": [{"name": "success", "type": "bool"}], "payable": False,
    #                                                 "stateMutability": "nonpayable", "type": "function"},
    #                                                {"constant": True, "inputs": [], "name": "symbol",
    #                                                 "outputs": [{"name": "", "type": "string", "value": "TNC1"}],
    #                                                 "payable": False, "stateMutability": "view", "type": "function"},
    #                                                {"constant": False, "inputs": [{"name": "_to", "type": "address"},
    #                                                                               {"name": "_value",
    #                                                                                "type": "uint256"}],
    #                                                 "name": "transfer", "outputs": [], "payable": False,
    #                                                 "stateMutability": "nonpayable", "type": "function"},
    #                                                {"constant": False,
    #                                                 "inputs": [{"name": "_spender", "type": "address"},
    #                                                            {"name": "_value", "type": "uint256"},
    #                                                            {"name": "_extraData", "type": "bytes"}],
    #                                                 "name": "approveAndCall",
    #                                                 "outputs": [{"name": "success", "type": "bool"}], "payable": False,
    #                                                 "stateMutability": "nonpayable", "type": "function"},
    #                                                {"constant": True, "inputs": [{"name": "", "type": "address"},
    #                                                                              {"name": "", "type": "address"}],
    #                                                 "name": "allowance",
    #                                                 "outputs": [{"name": "", "type": "uint256", "value": "0"}],
    #                                                 "payable": False, "stateMutability": "view", "type": "function"}, {
    #                                                    "inputs": [
    #                                                        {"name": "initialSupply", "type": "uint256", "index": 0,
    #                                                         "typeShort": "uint", "bits": "256",
    #                                                         "displayName": "initial Supply",
    #                                                         "template": "elements_input_uint",
    #                                                         "value": "1000000000000000000"},
    #                                                        {"name": "tokenName", "type": "string", "index": 1,
    #                                                         "typeShort": "string", "bits": "",
    #                                                         "displayName": "token Name",
    #                                                         "template": "elements_input_string", "value": "TNC1"},
    #                                                        {"name": "tokenSymbol", "type": "string", "index": 2,
    #                                                         "typeShort": "string", "bits": "",
    #                                                         "displayName": "token Symbol",
    #                                                         "template": "elements_input_string", "value": "TNC1"}],
    #                                                    "payable": False, "stateMutability": "nonpayable",
    #                                                    "type": "constructor"}, {"anonymous": False, "inputs": [
    #                                                   {"indexed": True, "name": "from", "type": "address"},
    #                                                   {"indexed": True, "name": "to", "type": "address"},
    #                                                   {"indexed": False, "name": "value", "type": "uint256"}],
    #                                                                             "name": "Transfer", "type": "event"},
    #                                                {"anonymous": False,
    #                                                 "inputs": [{"indexed": False, "name": "value", "type": "uint256"}],
    #                                                 "name": "Logger", "type": "event"}, {"anonymous": False, "inputs": [
    #                                                   {"indexed": True, "name": "from", "type": "address"},
    #                                                   {"indexed": False, "name": "value", "type": "uint256"}],
    #                                                                                      "name": "Burn",
    #                                                                                      "type": "event"}])
    #
    # # tx = myclient.invoke_contract(invoker="0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8", contract=contract,
    # #                               method="approve", args=("0x3aE88fe370c39384FC16dA2C9e768Cf5d2495b48", 300))
    # # rawdata = myclient.sign(tx, privtKey= "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    # # tx_id = myclient.broadcast(rawdata)
    #
    # a=myclient.sign_args(typeList=['bytes32', 'bytes32', 'uint256', 'uint256',"uint256"],
    #                      valueList=["0x3ae88fe370c39384fc16da2c9e768cf5d2495b48","0x537C8f3d3E18dF5517a58B3fB9D9143697996802",20,20,0],
    #                      privtKey="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    # b=myclient.sign_args(typeList=['bytes32', 'bytes32', 'uint256', 'uint256',"uint256"],
    #                      valueList=["0x3ae88fe370c39384fc16da2c9e768cf5d2495b48","0x537C8f3d3E18dF5517a58B3fB9D9143697996802",20,20,0],
    #                      privtKey="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    #
    # c=myclient.sign_args(typeList=['bytes32', 'bytes32', 'uint256', 'uint256',"uint256"],
    #                      valueList=["0x3ae88fe370c39384fc16da2c9e768cf5d2495b48","0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8",10,10,0],
    #                      privtKey="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    #
    # d=myclient.sign_args(typeList=['bytes32', 'bytes32', 'uint256', 'uint256',"uint256"],
    #                      valueList=["0x3ae88fe370c39384fc16da2c9e768cf5d2495b48","0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8",10,10,0],
    #                      privtKey="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    # print(a)
    # print(b)
    # # print(c)
    # # print(d)
    # pass
    '''
