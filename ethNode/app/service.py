import time

import requests
from decimal import Decimal

from config import setting

from .ethClient import Client
from .model import Erc20Tx

eth_client=Client(eth_url=setting.ETH_URL)







def construct_tx(addressFrom,addressTo,value,coinType=None):

    unsigned_tx_data,txHash=eth_client.construct_common_tx(addressFrom,addressTo,value)
    return {
        "txData":unsigned_tx_data,
        "txHash":txHash
    }


def construct_erc20_tx(addressFrom,addressTo,value):

    unsigned_tx_data,txHash=eth_client.construct_erc20_tx(addressFrom,addressTo,value)
    return {
        "txData":unsigned_tx_data,
        "txHash": txHash
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

    if erc20=="ETH":
        eth_balance=eth_client.get_balance_of_eth(address)
        return {
            "ETH":eth_balance
        }
    if erc20:
        exist_contract=setting.SmartContract.get(erc20)
        if exist_contract:
            contract_instance=eth_client.get_contract_instance(exist_contract[0],exist_contract[1])
            erc20_balance=eth_client.get_balance_of_erc20(contract_instance,address)
            return {
                "ERC20TNC":erc20_balance
            }
        else:
            return {}

    return {}



def get_transaction_by_hash(txId):
    res=eth_client.get_transaction_by_hash(txId)
    if res:
        return {"onChain":True}
    return {"onChain":False}

def get_transaction_receipt_by_hash(txId):
    res=eth_client.get_transaction_receipt_by_hash(txId)
    return res

def invoke_contract(invoker,contractAddress,method,args):
    exist_abi=setting.ABI_MAPPING.get(contractAddress)
    if exist_abi:

        contract_instance=eth_client.get_contract_instance(contractAddress,exist_abi)
        res=eth_client.invoke_contract(invoker, contract_instance, method, args)
        return {
            "txData":res
        }


def verify_transfer(addressFrom,addressTo,value):
    item = Erc20Tx.query.filter_by(address_from=addressFrom,
                                     address_to=addressTo,
                                     value=Decimal(str(value)),
                                     ).first()

    if item:
        return {"txId":item.tx_id}

    return {}

def transfer_erc20tnc(addressTo,value):
    address_from=setting.ADDRESS_FROM
    privt_key=setting.PRIVTKEY
    tx_id= eth_client.transfer_erc20tnc(address_from, addressTo, value,privt_key)
    return {
        "txId":"0x"+tx_id
    }