from flask import request

from config import setting
from . import jsonrpc
from . import service

from .utils import response_wrap, verify_password


@response_wrap
@jsonrpc.method("constructTx")
def construct_tx(addressFrom,addressTo,value):
    return service.construct_tx(addressFrom,addressTo,value)

@response_wrap
@jsonrpc.method("constructERC20Tx")
def construct_erc20_tx(addressFrom,addressTo,value):
    return service.construct_erc20_tx(addressFrom,addressTo,value)

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
def get_balance(address,erc20):
    return service.get_balance(address,erc20)


@response_wrap
@jsonrpc.method("getTransactionByHash")
def get_transaction_by_hash(txId):
    return service.get_transaction_by_hash(txId)

@response_wrap
@jsonrpc.method("getTransactionReceiptByHash")
def get_transaction_receipt_by_hash(txId):
    return service.get_transaction_receipt_by_hash(txId)


@response_wrap
@jsonrpc.method("invokeContract")
def invoke_contract(invoker,contractAddress,method,args):
    return service.invoke_contract(invoker,contractAddress,method,args)

@jsonrpc.method("verifyTransfer")
def verify_transfer(addressFrom,addressTo,value):
    return service.verify_transfer(addressFrom,addressTo,value)

@jsonrpc.method("autoTransferTNC")
def transfer_erc20tnc(addressTo,value):
    passwd=request.headers.get("Password")
    remote_ip=request.remote_addr
    passwd_hash=setting.PASSWD_HASH
    res = verify_password(passwd, passwd_hash)
    if remote_ip== setting.REMOTE_ADDR and res:
        return service.transfer_erc20tnc(addressTo,value)
    return {}