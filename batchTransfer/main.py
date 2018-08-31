from __future__ import unicode_literals
import time
import csv
import sys
import config
import binascii
from web3 import Web3, HTTPProvider
from ethereum.utils import checksum_encode

from web3.gas_strategies.time_based import construct_time_based_gas_price_strategy
from web3.gas_strategies.time_based import medium_gas_price_strategy  #Transaction mined within 10 minutes
from web3.gas_strategies.time_based import fast_gas_price_strategy    #Transaction mined within 1 minutes
from web3 import middleware

web3 = Web3(HTTPProvider(config.eth_rpc))
web3.eth.defaultAccount = config.account_address

print("isConnected:", web3.isConnected())

token_Contract = web3.eth.contract(abi=config.BATCH_ABI)
batch_contract = token_Contract(address=config.batch_contract_address)

addressFrom = config.account_address
privateKey = config.account_private_key

blockConfirmPeriod = 300 # after waited a special secondes, if the trasaction didn't be confirmed, then increase gas price, rebuild the trasaction
transferNumberOfTransaction = 3      # expected transferring account number in a transaction

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
    print("setTokenAddress")
    gasLimit = 600000
    tx = batch_contract.functions.setTokenAddress(config.token_address).buildTransaction({
            "gas": gasLimit,
            'gasPrice': web3.eth.gasPrice*5,
            'nonce': web3.eth.getTransactionCount(addressFrom),
        })
    signed = web3.eth.account.signTransaction(tx, privateKey)
    tx_id = web3.eth.sendRawTransaction(signed.rawTransaction)
    print("setTokenAddress tx:", binascii.hexlify(tx_id))

def sendPatchTransaction(rows):
    addr = []
    amounts = []
    gasLimit = 7000000

    for row in rows:
        addr.append(checksum_encode(row["address"]))
        amounts.append(int(row["value"])*pow(10,8))

    tx = batch_contract.functions.sendTransaction(addr, amounts, addressFrom).buildTransaction({
            "gas": gasLimit,
            'gasPrice': web3.eth.gasPrice*5,
            'nonce': web3.eth.getTransactionCount(addressFrom),
        })

    signed = web3.eth.account.signTransaction(tx, privateKey)
    tx_id = web3.eth.sendRawTransaction(signed.rawTransaction)
    #print("signed:", binascii.hexlify(signed.rawTransaction))
    
    for i in range(len(addr)):
        print("account:", addr[i], amounts[i])
    print("batchTransfer tx:", binascii.hexlify(tx_id))

def getGasPrice():
    print("current gasPrice:", web3.eth.gasPrice)

def contructTransaction(accounts, amounts):
    preGasPrice = 0
    currentGasPrice = 0
    Blockconfirmed = False
    gasLimit = 7000000
    gasBasePrice = 2000000000  #2 Gwei
    gasDeltaPrice = 1000000000 #1 Gwei 
    resendNumber = 0

    while (not Blockconfirmed):
        try:
            print("canculating gas ......")
            '''
            web3.eth.setGasPriceStrategy(construct_time_based_gas_price_strategy(120, 5, 100))
            currentGasPrice = web3.eth.generateGasPrice()
            '''
            currentGasPrice = web3.eth.gasPrice
            if(currentGasPrice <= gasBasePrice):
                currentGasPrice = gasBasePrice
            if (currentGasPrice <= preGasPrice):
                currentGasPrice = preGasPrice + gasDeltaPrice
            preGasPrice = currentGasPrice             

            print("expect gas and current gas: ", currentGasPrice, web3.eth.gasPrice)
            tx = batch_contract.functions.sendTransaction(accounts, amounts, config.account_address).buildTransaction({
                'gas': gasLimit,
                'gasPrice': currentGasPrice,
                'nonce': web3.eth.getTransactionCount(addressFrom),
                })
            print("cteate transaction")
            signed = web3.eth.account.signTransaction(tx, privateKey)
            tx_id = web3.eth.sendRawTransaction(signed.rawTransaction)
            print("boradcast")
            time.sleep(10)
            print("waiting for block confirm ....")
            web3.eth.waitForTransactionReceipt(tx_id, 300)
        except Exception as e:
            print(e)
            resendNumber += 1
            print("block confirmed timeout")
            if (resendNumber == 3):
                return "0000000000000000000000000000000000000000000000000000000000000000"
            
            if (None != web3.eth.getTransactionReceipt(tx_id)):
                Blockconfirmed = True
                return binascii.hexlify(tx_id)
            
        else:
            Blockconfirmed = True
            print("block have confirmed")

    for i in range(len(accounts)):
        print("account:", accounts[i], amounts[i])
    print("txid:", binascii.hexlify(tx_id))
    
    return binascii.hexlify(tx_id)

def batchTransfer(rows):
    transferNumber = transferNumberOfTransaction
    beginRow = 0
    endRow = transferNumber

    transferCounts = len(rows) // transferNumber
    remainCounts = len(rows) % transferNumber
    if remainCounts > 0:
        transferCounts += 1

    print("total accounts = %d, total transaction numbers = %d" %(len(rows), transferCounts))

    now = time.strftime("%Y-%m-%d-%H_%M_%S",time.localtime(time.time()))
    out = open(now+"_patchTransfer.csv", 'w', newline='')
    csv_writer = csv.writer(out, dialect='excel')

    for sendCount in range(transferCounts):
        accounts = []
        amounts = []
        print("transaction NO:", sendCount)
        for row in rows[beginRow:endRow]:
            accounts.append(checksum_encode(row["address"]))
            amounts.append(int(row["value"])*pow(10,8))
            csv_writer.writerow([row["address"], row["value"]])
            
        txId = contructTransaction(accounts, amounts)
        csv_writer.writerow([txId])
        if(txId == "0000000000000000000000000000000000000000000000000000000000000000"):
            return
        
        beginRow += transferNumber
        endRow += transferNumber

def checkTransferAddress():
    with open(config.csv_file) as f:
        for row in [row for row in csv.DictReader(f)]:
            try:
                checksum_encode(row["address"])
            except Exception as e:
                print(e)
                return
    print("all address is valid")

def testGas():
    gasLimit = 60000

    print("canculating gas ......")
    #web3.eth.setGasPriceStrategy(construct_time_based_gas_price_strategy(120, 5, 100))
    #web3.middleware_stack.add(middleware.time_based_cache_middleware)
    #web3.middleware_stack.add(middleware.latest_block_based_cache_middleware)
    #web3.middleware_stack.add(middleware.simple_cache_middleware)  
    #print("expect gas and current gas: ", web3.eth.generateGasPrice(), web3.eth.gasPrice)
    print("current gas: ",web3.eth.gasPrice)

def main(argv):
    if len(argv) < 2:
        print("parameters number wrong")
        return False;

    if sys.argv[1] == "approve":
        approveToken();
        
    if sys.argv[1] == "setTokenAddress":
            setTokenAddress();
            
    if sys.argv[1] == "sendTransaction":
        with open(config.csv_file) as f:
            sendPatchTransaction([row for row in csv.DictReader(f)])

    if sys.argv[1] == "getGasPrice":
        getGasPrice()

    # the two functions support auto patch transfer
    if argv[1] == "batchTransfer":
        with open(config.csv_file) as f:
            batchTransfer([row for row in csv.DictReader(f)])
        return True

    if argv[1] == "checkTransferAddress":
        checkTransferAddress()
        return True

    if argv[1] == "testGas":
        testGas()
        return True    
            
    return True;

if __name__ == '__main__':
    sys.exit(main(sys.argv))
