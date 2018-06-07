from __future__ import unicode_literals
import csv
import sys
import config
import binascii
from web3 import Web3, HTTPProvider

web3 = Web3(HTTPProvider(config.eth_rpc))
web3.eth.defaultAccount = config.account_address

print("isConnected:", web3.isConnected())

token_Contract = web3.eth.contract(abi=config.BATCH_ABI)

batch_contract = token_Contract(address=config.batch_contract_address)

addressFrom = config.account_address
privateKey = config.account_private_key

def approveToken():
    token_Contract = web3.eth.contract(abi=config.TOKEN_ABI)
    token_contract = token_Contract(address=config.token_address)
    
    gasLimit = 60000
    tx = token_contract.functions.approve(config.batch_contract_address, 1000000).buildTransaction({
            "gas": gasLimit,
            'gasPrice': web3.eth.gasPrice*2,
            'nonce': web3.eth.getTransactionCount(addressFrom),
        })
    signed = web3.eth.account.signTransaction(tx, privateKey)
    tx_id = web3.eth.sendRawTransaction(signed.rawTransaction)
    print("setTokenAddress tx:", binascii.hexlify(tx_id))

def setTokenAddress():
    gasLimit = 60000
    tx = batch_contract.functions.setTokenAddress(config.token_address).buildTransaction({
            "gas": gasLimit,
            'gasPrice': web3.eth.gasPrice*2,
            'nonce': web3.eth.getTransactionCount(addressFrom),
        })
    signed = web3.eth.account.signTransaction(tx, privateKey)
    tx_id = web3.eth.sendRawTransaction(signed.rawTransaction)
    print("setTokenAddress tx:", binascii.hexlify(tx_id))

def batchTransfer(rows):
    addr = []
    amounts = []
    gasLimit = 8000000000
    
    for row in rows:
        addr.append(row["address"])
        amounts.append(int(row["value"]))

    tx = batch_contract.functions.sendTransaction(addr, amounts, addressFrom).buildTransaction({
            "gas": gasLimit,
            'gasPrice': web3.eth.gasPrice*2,
            'nonce': web3.eth.getTransactionCount(addressFrom),
        })

    signed = web3.eth.account.signTransaction(tx, privateKey)
    tx_id = web3.eth.sendRawTransaction(signed.rawTransaction)
    
    for i in range(len(addr)):
        print("account:", addr[i], amounts[i])
    print("batchTransfer tx:", binascii.hexlify(tx_id))


def main(argv):
    if len(argv) < 2:
        print("parameters number wrong")
        return False;
    if sys.argv[1] == "approve":
        approveToken();
        
    if sys.argv[1] == "token":
            setTokenAddress();
            
    if sys.argv[1] == "batch":
        with open(config.csv_file) as f:
               batchTransfer([row for row in csv.DictReader(f)])
            
    return True;

if __name__ == '__main__':
    sys.exit(main(sys.argv))
