import time

import requests

from config import setting

from .ethClient import Client
from . import erc20_token

eth_client=Client(eth_url=setting.ETH_URL)







def construct_tx(addressFrom,addressTo,value,coinType=None):

    unsigned_tx_data=eth_client.construct_common_tx(addressFrom,addressTo,value)
    return {
        "unsignedTxData":unsigned_tx_data
    }


def construct_erc20_tx(addressFrom,addressTo,value,coinType=None):

    unsigned_tx_data=eth_client.construct_erc20_tx(addressFrom,addressTo,value)
    return {
        "unsignedTxData":unsigned_tx_data
    }

def sign(unsignedTxData,privtKey):
    signature=eth_client.sign(unsignedTxData,privtKey)

    return {
        "signature":signature
    }



def broadcast(unsignedTxData,signature):
    res=eth_client.broadcast(unsignedTxData,signature)
    return {
        "txId":res
    }


def get_balance(address,erc20=None):
    if erc20:
        exist_contract=erc20_token.SmartContract.get(erc20)
        if exist_contract:
            contract_instance=eth_client.get_contract_instance(exist_contract[0],exist_contract[1])
            erc20_balance=eth_client.get_balance_of_erc20(contract_instance,address)
            return {
                "ERC20TNC":erc20_balance
            }
    eth_balance=eth_client.get_balance_of_eth(address)
    return {
        "ETH":eth_balance
    }


def invoke_contract(invoker,contractAddress,method,args):
    exist_abi=erc20_token.ABI_MAPPING.get(contractAddress)
    if exist_abi:

        contract_instance=eth_client.get_contract_instance(contractAddress,exist_abi)
        res=eth_client.invoke_contract(invoker, contract_instance, method, args)
        return {
            "unsignedTx":res
        }