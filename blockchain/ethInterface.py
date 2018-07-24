import time
import requests
import sys

from ethereum.utils import checksum_encode, ecrecover_to_pub,safe_ord
from eth_hash.backends.pysha3 import keccak256
import binascii
from web3 import Web3
from web3client import Client

class Interface(object):

    def __init__(self, url, contract_address, contract_abi, asset_address, asset_abi):
        self.eth_client=Client(eth_url=url)

        self.contract=self.eth_client.get_contract_instance(contract_address,contract_abi)
        self.asset_contract=self.eth_client.get_contract_instance(asset_address,asset_abi)

    def approve(self, invoker, ethContractAddress, assetAmount, key):
        ethContractAddress = checksum_encode(ethContractAddress)
        txId = self.eth_client.contruct_Transaction(invoker, self.asset_contract, "approve",[ethContractAddress,assetAmount], key)
        return {
            "txData":txId
        }

    def setSettleTimeout(self, invoker, timeoutValue, key):
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "setSettleTimeout",[timeoutValue], key)
        return {
            "txData":txId
        }

    def setToken(self, invoker, tokenAddress, key):
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "setToken",[tokenAddress], key)
        return {
            "txData":txId
        }     
    
    def deposit(self, invoker,channelId, nonce, funder, funderAmount, partner, partnerAmount, funderSignature, partnerSignature, key):  
        funderAddress=checksum_encode(funder)
        partnerAddress=checksum_encode(partner)
        txId=self.eth_client.contruct_Transaction(invoker,self.contract,"deposit",[channelId, nonce, funder, funderAmount, partner, partnerAmount, funderSignature, partnerSignature],key)
        return {
            "txData":txId
        }

    
    def updateDeposit(self,invoker,channelId,nonce,funder, funderAmount, partner, partnerAmount, funderSignature, partnerSignature,key):
        funder = checksum_encode(funder)
        partner = checksum_encode(partner)    
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "updateDeposit", [channelId,nonce,funder,funderAmount,partner,partnerAmount,funderSignature,partnerSignature],key)
        return {
            "txData":txId
        }

    def quickCloseChannel(self,invoker,channelId,nonce,closer,closerBalance,partner,partnerBalance,closerSignature,partnerSignature,key):
        closer = checksum_encode(closer)
        partner = checksum_encode(partner)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "quickCloseChannel", [channelId,nonce,closer,closerBalance,partner,partnerBalance,closerSignature,partnerSignature],key)
        return {
            "txData":txId
        }

    def closeChannel(self, invoker,channelId,nonce,partnerA,closeBalanceA,partnerB,closeBalanceB,signedStringA,signedStringB,key):
        partnerA = checksum_encode(partnerA)
        partnerB = checksum_encode(partnerB)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "closeChannel", [channelId,nonce,partnerA,closeBalanceA,partnerB,closeBalanceB,signedStringA,signedStringB],key)
        return {
            "txData":txId
        }

    def updateTransaction(self, invoker,channelId, nonce, partnerA, updateBalanceA, partnerB, updateBalanceB, signedStringA, signedStringB,key):
        partnerA = checksum_encode(partnerA)
        partnerB = checksum_encode(partnerB)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "updateTransaction", [channelId, nonce, partnerA, updateBalanceA, partnerB, updateBalanceB, signedStringA, signedStringB],key)
        return {
            "txData":txId
        }

    def settleTransaction(self,invoker,channelId,key):
        txId=self.eth_client.contruct_Transaction(invoker,self.contract,"settleTransaction",[channelId],key)
        return {
            "txData":txId
        }

    def withdraw(self, invoker, channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature, secret, key):
        partnerA = checksum_encode(sender)
        partnerB = checksum_encode(receiver)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "withdraw", [channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature, secret],key)
        return {
            "txData":txId
        }

    def withdrawUpdate(self, invoker, channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature, key):
        partnerA = checksum_encode(sender)
        partnerB = checksum_encode(receiver)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "withdrawUpdate", [channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature],key)
        return {
            "txData":txId
        }

    def withdrawSettle(self, invoker, channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature, secret, key):
        partnerA = checksum_encode(sender)
        partnerB = checksum_encode(receiver)
        txId = self.eth_client.contruct_Transaction(invoker, self.contract, "withdrawSettle", [channelId, nonce, sender, receiver, lockPeriod, lockAmount, lockHash, senderSignature, receiverSignature, secret],key)
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



        
