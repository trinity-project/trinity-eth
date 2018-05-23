import time

import requests

from config import setting

from .ethClient import Client

eth_client=Client(eth_url=setting.ETH_URL)







def construct_tx(addressFrom,addressTo,value):
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
    balance=Balance.query.filter_by(address=address).first()

    data = {
        "jsonrpc": "2.0",
        "method": "invokefunction",
        "params": [
            setting.CONTRACTHASH,
            "balanceOf",
            [
                {
                    "type":"Hash160",
                    "value":ToScriptHash(address).ToString()
                }
            ]
        ],
        "id": 1
    }
    res = requests.post(setting.NEOCLIURL, json=data).json()
    value=res["result"]["stack"][0]["value"]
    if balance:
        response={
            "gasBalance":float(balance.gas_balance),
            "neoBalance":float(balance.neo_balance),
            "tncBalance":int(hex_reverse(value),16)/100000000 if value else 0
        }
    else:
        if value:
            response={"tncBalance":int(hex_reverse(value),16)/100000000,"gasBalance":0,"neoBalance":0}
        else:
            response={"tncBalance":0,"gasBalance":0,"neoBalance":0}
    return response



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

