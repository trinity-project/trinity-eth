import time
import requests

# from config import setting
from ethereum.utils import checksum_encode, ecrecover_to_pub,safe_ord
from eth_hash.backends.pysha3 import keccak256
import binascii
from web3 import Web3
from .config import setting
from .client import Client

import sys

class Interface(object):

    def __init__(self):
        self.eth_client=Client(eth_url=setting.ETH_URL)

        self.contract=self.eth_client.get_contract_instance(setting.ETH_CONTRACT_ADDRESS,setting.ETH_CONTRACT_ABI)
        self.asset_contract=self.eth_client.get_contract_instance(setting.ASSET_CONTRACT_ADDRESS,setting.ASSET_CONTRACT_ABI)

    def approve_default(self, invoker, assetAmount, privateKey):
        self.__approve(invoker, setting.ASSET_CONTRACT_ADDRESS, assetAmount, privateKey)

    def approve(self, invoker, ethContractAddress, assetAmount, privateKey):
        ethContractAddress = checksum_encode(ethContractAddress)
        txId = self.eth_client.contruct_Transaction(invoker, self.asset_contract, "approve",[ethContractAddress,assetAmount], privateKey)
        return {
            "txData":txId
        }

    def setSettleTimeout(self, invoker, timeoutValue, privateKey):
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "setSettleTimeout",[timeoutValue], privateKey)
        return {
            "txData":txId
        }

    def setToken(self, invoker, tokenAddress, privateKey):
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "setToken",[tokenAddress], privateKey)
        return {
            "txData":txId
        }     
    
    def deposit(self, invoker,channelId, nonce, funder, funderAmount, partner, partnerAmount, funderSignature, partnerSignature, privateKey):  
        funderAddress=checksum_encode(funder)
        partnerAddress=checksum_encode(partner)
        txId=self.eth_client.contruct_Transaction(invoker,self.contract,"deposit",[channelId, nonce, funder, funderAmount, partner, partnerAmount, funderSignature, partnerSignature],privateKey)
        return {
            "txData":txId
        }

    
    def updateDeposit(self,invoker,channelId,nonce,funder, funderAmount, partner, partnerAmount, funderSignature, partnerSignature,privateKey):
        funder = checksum_encode(funder)
        partner = checksum_encode(partner)    
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "updateDeposit", [channelId,nonce,funder,funderAmount,partner,partnerAmount,funderSignature,partnerSignature],privateKey)
        return {
            "txData":txId
        }

    def quickCloseChannel(self,invoker,channelId,nonce,closer,closerBalance,partner,partnerBalance,closerSignature,partnerSignature,privateKey):
        closer = checksum_encode(closer)
        partner = checksum_encode(partner)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "quickCloseChannel", [channelId,nonce,closer,closerBalance,partner,partnerBalance,closerSignature,partnerSignature],privateKey)
        return {
            "txData":txId
        }

    def closeChannel(self, invoker,channelId,nonce,partnerA,closeBalanceA,partnerB,closeBalanceB,signedStringA,signedStringB,privateKey):
        partnerA = checksum_encode(partnerA)
        partnerB = checksum_encode(partnerB)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "closeChannel", [channelId,nonce,partnerA,closeBalanceA,partnerB,closeBalanceB,signedStringA,signedStringB],privateKey)
        return {
            "txData":txId
        }

    def updateTransaction(self, invoker,channelId, nonce, partnerA, updateBalanceA, partnerB, updateBalanceB, signedStringA, signedStringB,privateKey):
        partnerA = checksum_encode(partnerA)
        partnerB = checksum_encode(partnerB)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "updateTransaction", [channelId, nonce, partnerA, updateBalanceA, partnerB, updateBalanceB, signedStringA, signedStringB],privateKey)
        return {
            "txData":txId
        }

    def settleTransaction(self,invoker,channelId,privateKey):
        txId=self.eth_client.contruct_Transaction(invoker,self.contract,"settleTransaction",[channelId],privateKey)
        return {
            "txData":txId
        }

    def withdraw(self, invoker, channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature, secret, privateKey):
        partnerA = checksum_encode(sender)
        partnerB = checksum_encode(receiver)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "withdraw", [channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature, secret],privateKey)
        return {
            "txData":txId
        }

    def withdrawUpdate(self, invoker, channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature, privateKey):
        partnerA = checksum_encode(sender)
        partnerB = checksum_encode(receiver)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "withdrawUpdate", [channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature],privateKey)
        return {
            "txData":txId
        }

    def withdrawSettle(self, invoker, channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature, secret, privateKey):
        partnerA = checksum_encode(sender)
        partnerB = checksum_encode(receiver)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "withdrawSettle", [channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature, secret],privateKey)
        return {
            "txData":txId
        }    

    def getChannelTotal(self):
        allChannels=self.eth_client.call_contract(self.contract,"getChannelCount",[])
        return {
            "totalChannels":allChannels
        }

    def getChannelInfoById(self,channelId):
        channelInfo=self.eth_client.call_contract(self.contract,"getChannelById",[channelId])
        return {
            "channelInfo":channelInfo
        }        

    def sign(self, unsignedTxData,privtKey):
        signature=self.eth_client.sign(unsignedTxData,privtKey)
        return {
            "signature":signature
        }

    def broadcast(self, unsignedTxData,signature):
        res=self.eth_client.broadcast(unsignedTxData,signature)
        return {
            "txId":res
        }

    def sign_args(self,typeList, valueList, privtKey):
        signature = self.eth_client.sign_args(typeList, valueList, privtKey)
        return signature

    def createChannelId(self,partnerA, partnerB):
        id = keccak256((partnerA+partnerB).encode())
        id = bytearray(id)
        channelId = '0x'+binascii.hexlify(id).decode()
        return channelId

    def createLockHash(self, secret):
        lockHash = keccak256(bytes.fromhex(secret))
        #lockHash = bytearray(lockHash)
        #lockHash = '0x'+binascii.hexlify(lockHash).decode()
        return lockHash.hex()        



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("parameters number wrong")
        exit(0)

    interface = Interface()
    publiceKey1 = "0x3aE88fe370c39384FC16dA2C9e768Cf5d2495b48"
    publiceKey2 = "0x9dA26FC2E1D6Ad9FDD46138906b0104ae68a65D8"
    publiceKey3 = "0x537C8f3d3E18dF5517a58B3fB9D9143697996802"
    #publiceKey4 = "0x81063419F13cAB5Ac090Cd8329d8FFF9fEeAd4A0"

    privateKey1 = "095e53c9c20e23fd01eaad953c01da9e9d3ed9bebcfed8e5b2c2fce94037d963"
    privateKey2 = "b6a03207128827eaae0d31d97a7a6243de31f2baf99eabd764e33389ecf436fc"
    privateKey3 = "34c50c398a4aad207e25eeca7d799b966805d48c8fd47a2a9dbc66d9224ff7c1"
    #privateKey4 = "5bc505a123a695176a9688ffe22798cfd40424c5b91c818e985574ea8ebda167"

    if sys.argv[1] == "lockHash":
        secret = "f2ee7b0466feb5d6c50d655885c8387ddcf1739929c17bbda3977e330eca895c"
        #print(secret.encode())
        lockHash = interface.createLockHash(secret)
        print(lockHash)

    if sys.argv[1] == "getChannelTotal":
        result = interface.getChannelTotal()
        print(result)

    if sys.argv[1] == "getChannelInfoById":
        channelId = '0xf2ee7b0466feb5d6c50d655885c8387ddcf1739929c17bbda3977e330eca895c'
        result = interface.getChannelInfoById(channelId)
        print(result)

    if sys.argv[1] == "approve":
        
       publiceKeyList = [publiceKey1,publiceKey2]
       privateKyeList = [privateKey1,privateKey2]
       for i in range(len(publiceKeyList)):
           tx_id = interface.approve(publiceKeyList[i], setting.ETH_CONTRACT_ADDRESS, 5000, privateKyeList[i])
           print(tx_id)
           time.sleep(120)

    if sys.argv[1] == "setSettleTimeout":
        tx_id = interface.setSettleTimeout(publiceKey1, 10, privateKey1)
        print(tx_id)

    if sys.argv[1] == "setToken":
        tokenAddress = '0x593d4581b7c012bD62a2018883308759b40Bd50a'
        tx_id = interface.setToken(publiceKey1, tokenAddress, privateKey1)
        print(tx_id)         
        
    if sys.argv[1] == "deposit":
        nonce = 110
        funder = publiceKey1
        funderAmount = 100
        partner = publiceKey2
        partnerAmount = 100
        funderPrivateKey = privateKey1
        partnerPirvateKey = privateKey2
        channelId = interface.createChannelId(funder,partner)

        funderSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                        valueList=[channelId, nonce, funder, funderAmount, partner, partnerAmount],
                        privtKey = funderPrivateKey).decode()
        partnerSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                        valueList=[channelId, nonce, funder, funderAmount, partner, partnerAmount],
                        privtKey = partnerPirvateKey).decode()

        print(channelId, nonce, funder, funderAmount, partner, partnerAmount,funderSignature, partnerSignature)

        tx_id = interface.deposit(funder, channelId, nonce, funder, funderAmount, partner, partnerAmount, funderSignature, partnerSignature, funderPrivateKey)
        print(tx_id)

    if sys.argv[1] == "updateDeposit":
        nonce = 111
        funder = publiceKey1
        funderAmount = 20
        partner = publiceKey2
        partnerAmount = 10
        funderPrivateKey = privateKey1
        partnerPirvateKey = privateKey2
        channelId = interface.createChannelId(funder,partner)

        funderSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                        valueList=[channelId, nonce, funder, funderAmount, partner, partnerAmount],
                        privtKey = funderPrivateKey).decode()
        partnerSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                        valueList=[channelId, nonce, funder, funderAmount, partner, partnerAmount],
                        privtKey = partnerPirvateKey).decode()

        print(channelId, nonce, funder, funderAmount, partner, partnerAmount, funderSignature, partnerSignature)

        tx_id = interface.updateDeposit(partner, channelId, nonce, funder, funderAmount, partner, partnerAmount, funderSignature, partnerSignature, partnerPirvateKey)
        print(tx_id)        
    
    if sys.argv[1] == "quickCloseChannel":
        nonce = 112
        closer = publiceKey1
        closerAmount = 100
        partner = publiceKey2
        partnerAmount = 100
        closerPrivateKey = privateKey1
        partnerPirvateKey = privateKey2
        channelId = interface.createChannelId(publiceKey1,publiceKey2)

        closerSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                        valueList=[channelId, nonce, closer, closerAmount, partner, partnerAmount],
                        privtKey = closerPrivateKey).decode()
        partnerSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                        valueList=[channelId, nonce, closer, closerAmount, partner, partnerAmount],
                        privtKey = partnerPirvateKey).decode()        

        print(channelId, nonce, closer, closerAmount, partner, partnerAmount, closerSignature, partnerSignature)

        tx_id = interface.quickCloseChannel(closer, channelId, nonce, closer, closerAmount, partner, partnerAmount, closerSignature, partnerSignature, closerPrivateKey)
        print(tx_id)

    if sys.argv[1] == "closeChannel":
        nonce = 113
        closer = publiceKey1
        closerAmount = 100
        partner = publiceKey2
        partnerAmount = 100
        closerPrivateKey = privateKey1
        partnerPirvateKey = privateKey2
        channelId = interface.createChannelId(publiceKey1,publiceKey2)

        closerSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                        valueList=[channelId, nonce, closer, closerAmount, partner, partnerAmount],
                        privtKey = closerPrivateKey).decode()
        partnerSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                        valueList=[channelId, nonce, closer, closerAmount, partner, partnerAmount],
                        privtKey = partnerPirvateKey).decode()

        print(channelId, nonce, closer, closerAmount, partner, partnerAmount, closerSignature, partnerSignature)

        tx_id = interface.closeChannel(publiceKey1, channelId, nonce, closer, closerAmount, partner, partnerAmount, closerSignature, partnerSignature, privateKey1)
        print(tx_id)   

    if sys.argv[1] == "updateTransaction":
        nonce = 113
        updater = publiceKey2
        updaterAmount = 80
        partner = publiceKey1
        partnerAmount = 100
        updaterPrivateKey = privateKey2
        partnerPirvateKey = privateKey1
        channelId = interface.createChannelId(publiceKey1,publiceKey2)

        print(channelId)
        updateSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                        valueList=[channelId, nonce, updater, updaterAmount, partner, partnerAmount],
                        privtKey = updaterPrivateKey).decode()
        partnerSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                        valueList=[channelId, nonce, updater, updaterAmount, partner, partnerAmount],
                        privtKey = partnerPirvateKey).decode()        

        tx_id = interface.updateTransaction(updater, channelId, nonce, updater, updaterAmount, partner, partnerAmount, updateSignature, partnerSignature, updaterPrivateKey)
        print(tx_id) 

    if sys.argv[1] == "settleTransaction":
        nonce = 115
        settler = publiceKey1
        settlerPrivateKey = privateKey1
        channelId = interface.createChannelId(publiceKey1,publiceKey2)
        
        print(channelId)
        
        tx_id = interface.settleTransaction(settler, channelId, settlerPrivateKey)
        print(tx_id) 

    if sys.argv[1] == "withdraw":
        channelId = interface.createChannelId(publiceKey1,publiceKey2)
        nonce = 200
        sender = publiceKey1
        receiver = publiceKey2
        lockPeriod = 106400
        lockAmount = 10
        secret = "f2ee7b0466feb5d6c50d655885c8387ddcf1739929c17bbda3977e330eca895c"
        lockHash = interface.createLockHash(secret)

        secret_sign = '0x'+secret
        lockHash_sign = '0x'+lockHash

        senderPrivateKey = privateKey1
        receiverPrivateKey = privateKey2

        senderSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'address', 'uint256', 'uint256', 'bytes32'],
                        valueList=[channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign],
                        privtKey = senderPrivateKey).decode()
        receiverSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'address', 'uint256', 'uint256', 'bytes32'],
                        valueList=[channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign],
                        privtKey = receiverPrivateKey).decode()        

        print(channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign, senderSignature, receiverSignature, secret_sign)

        #tx_id = interface.withdraw(sender, channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign, senderSignature, receiverSignature, secret_sign, senderPrivateKey)
        #print(tx_id)

    if sys.argv[1] == "withdrawUpdate":
        channelId = interface.createChannelId(publiceKey1,publiceKey2)
        nonce = 200
        sender = publiceKey2
        receiver = publiceKey1
        lockPeriod = 3680250
        lockAmount = 10
        secret = "f2ee7b0466feb5d6c50d655885c8387ddcf1739929c17bbda3977e330eca895c"
        lockHash = interface.createLockHash(secret)

        lockHash_sign = '0x'+lockHash

        senderPrivateKey = privateKey2
        receiverPrivateKey = privateKey1

        senderSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'address', 'uint256', 'uint256', 'bytes32'],
                        valueList=[channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign],
                        privtKey = senderPrivateKey).decode()
        receiverSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'address', 'uint256', 'uint256', 'bytes32'],
                        valueList=[channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign],
                        privtKey = receiverPrivateKey).decode()        

        print(channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign, senderSignature, receiverSignature)

        tx_id = interface.withdrawUpdate(sender, channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign, senderSignature, receiverSignature, senderPrivateKey)
        print(tx_id)        

    if sys.argv[1] == "withdrawSettle":
        channelId = interface.createChannelId(publiceKey1,publiceKey2)
        nonce = 200
        sender = publiceKey1
        receiver = publiceKey2
        lockPeriod = 3680250
        lockAmount = 10
        secret = "f2ee7b0466feb5d6c50d655885c8387ddcf1739929c17bbda3977e330eca895c"
        lockHash = interface.createLockHash(secret)

        secret_sign = '0x'+secret
        lockHash_sign = '0x'+lockHash

        senderPrivateKey = privateKey1
        receiverPrivateKey = privateKey2

        senderSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'address', 'uint256', 'uint256', 'bytes32'],
                        valueList=[channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign],
                        privtKey = senderPrivateKey).decode()
        receiverSignature = '0x'+ interface.sign_args(typeList=['bytes32', 'uint256', 'address', 'address', 'uint256', 'uint256', 'bytes32'],
                        valueList=[channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign],
                        privtKey = receiverPrivateKey).decode()        

        print(channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign, senderSignature, receiverSignature, secret_sign)

        tx_id = interface.withdrawSettle(sender, channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash_sign, senderSignature, receiverSignature, secret_sign, senderPrivateKey)
        print(tx_id)







        
