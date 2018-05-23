

from . import jsonrpc
from . import service

from .utils import response_wrap

@response_wrap
@jsonrpc.method("constructTx")
def construct_tx(addressFrom,addressTo,value):
    return service.construct_tx(addressFrom,addressTo,value)

@response_wrap
@jsonrpc.method("sign")
def sign(txData,privtKey):
    return service.sign(txData,privtKey)

@response_wrap
@jsonrpc.method("broadcast")
def broadcast(rawTx,signature):
    return service.broadcast(rawTx,signature)



@response_wrap
@jsonrpc.method("getBalance")
def get_balance(address):
    return service.get_balance(address)


