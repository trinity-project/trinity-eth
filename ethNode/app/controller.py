

from app import jsonrpc
from app import service








@jsonrpc.method("constructTx")
def construct_tx(addressFrom,addressTo,value):
    return service.construct_tx(addressFrom,addressTo,value)


@jsonrpc.method("sign")
def sign(txData,privtKey):
    return service.sign(txData,privtKey)

@jsonrpc.method("sendRawTx")
def send_raw_tx(rawTx,signature):
    return service.broadcast(rawTx,signature)

@jsonrpc.method("getRawTransaction")
def get_raw_transaction(txid):
    return service.get_raw_transaction(txid)


@jsonrpc.method("getBalance")
def get_balance(address):
    return service.get_balance(address)


