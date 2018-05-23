import time

import requests

from config import setting

from .ethClient import Client

eth_client=Client(eth_url=setting.ETH_URL)







def construct_tx(addressFrom,addressTo,value,coinType=None):
    if coinType=="ERC20TNC":
        unsigned_tx_data = eth_client.construct_common_tx(addressFrom, addressTo, value)
    unsigned_tx_data=eth_client.construct_common_tx(addressFrom,addressTo,value)
    return {
        "unsignedTxData":unsigned_tx_data
    }


def sign(unsignedTxData,privtKey):
    signed_data=eth_client.sign(unsignedTxData,privtKey)

    return signed_data



def broadcast(unsignedTxData,signature):
    res=eth_client.broadcast(unsignedTxData,signature)
    print(res)
    return {
        "txId":res
    }


def get_balance(address):
    eth_balance=eth_client.get_balance_of_eth(address)
    return {
        "ETH":eth_balance
    }



def get_raw_transaction(txid):
    data = {
        "jsonrpc": "2.0",
        "method": "getrawtransaction",
        "params": [txid,1],
        "id": 1
    }
    res = requests.post(setting.NEOCLIURL,json=data).json()
    try:
        return res["result"]
    except:

        return None

