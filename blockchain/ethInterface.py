import time
import requests
import sys

from ethereum.utils import checksum_encode, ecrecover_to_pub,safe_ord
from eth_hash.backends.pysha3 import keccak256
import binascii
from web3 import Web3
from .web3client import Client


class Interface(object):
    """

    """
    __species = None
    __first_init = True

    def __new__(cls, *args, **kwargs):
        if not cls.__species:
            cls.__species = object.__new__(cls)
        return cls.__species

    def __init__(self, url, contract_address, contract_abi, asset_address, asset_abi):
        """

        :param url:
        :param contract_address:
        :param contract_abi:
        :param asset_address:
        :param asset_abi:
        """
        if self.__first_init:
            self.__class__.__first_init = False
            self.eth_client = Client(eth_url=url)
            self.contract_address = checksum_encode(contract_address)

            self.contract=self.eth_client.get_contract_instance(contract_address,contract_abi)
            self.asset_contract=self.eth_client.get_contract_instance(asset_address,asset_abi)

    def approve(self, invoker, asset_amount, invoker_key):
        """

        :param invoker:
        :param asset_amount:
        :param invoker_key:
        :return:
        """
        tx_id = self.eth_client.contruct_Transaction(invoker, self.asset_contract, "approve", [self.contract_address, asset_amount], invoker_key)
        return {
            "txData":tx_id
        }

    def get_approved_asset(self, contract_address, abi, approver, spender):
        """
        :parameters: refer to the member function of eth_client
        """
        return self.eth_client.get_approved_asset(contract_address, abi, approver, spender)

    def set_settle_timeout(self, invoker, timeout, invoker_key):
        """

        :param invoker:
        :param timeout:
        :param invoker_key:
        :return:
        """
        tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "setSettleTimeout", [timeout], invoker_key)
        return {
            "txData":tx_id
        }

    def set_token(self, invoker, token_address, invoker_key):
        """

        :param invoker:
        :param token_address:
        :param invoker_key:
        :return:
        """
        tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "setToken", [token_address], invoker_key)
        return {
            "txData":tx_id
        }     
    
    def deposit(self, invoker, channel_id, nonce, founder, founder_amount,
                partner, partner_amount, founder_signature, partner_signature, invoker_key):
        """

        :param invoker:
        :param channel_id:
        :param nonce:
        :param founder:
        :param founder_amount:
        :param partner:
        :param partner_amount:
        :param founder_signature:
        :param partner_signature:
        :param invoker_key:
        :return:
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        tx_id = self.eth_client.contruct_Transaction(invoker, self.contract,"deposit",
                                                     [channel_id, nonce,
                                                      founder, founder_amount,
                                                      partner, partner_amount,
                                                      founder_signature, partner_signature], invoker_key)
        return {
            "txData":tx_id
        }

    def update_deposit(self, invoker, channel_id, nonce, founder, founder_amount,
                       partner, partner_amount, founder_signature, partner_signature, invoker_key):
        """

        :param invoker:
        :param channel_id:
        :param nonce:
        :param founder:
        :param founder_amount:
        :param partner:
        :param partner_amount:
        :param founder_signature:
        :param partner_signature:
        :param invoker_key:
        :return:
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)    
        tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "updateDeposit",
                                                     [channel_id, nonce,
                                                      founder, founder_amount,
                                                      partner, partner_amount,
                                                      founder_signature, partner_signature], invoker_key)
        return {
            "txData":tx_id
        }

    def quick_close_channel(self, invoker, channel_id, nonce, founder, founder_balance,
                            partner, partner_balance, founder_signature, partner_signature, invoker_key):
        """

        :param invoker:
        :param channel_id:
        :param nonce:
        :param founder:
        :param founder_balance:
        :param partner:
        :param partner_balance:
        :param founder_signature:
        :param partner_signature:
        :param invoker_key:
        :return:
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "quickCloseChannel",
                                                     [channel_id, nonce,
                                                      founder, founder_balance,
                                                      partner, partner_balance,
                                                      founder_signature, partner_signature], invoker_key)
        return {
            "txData":tx_id
        }

    def close_channel(self, invoker, channel_id, nonce, founder, founder_balance,
                      partner, partner_balance, founder_signature, partner_signature, invoker_key):
        """

        :param invoker:
        :param channel_id:
        :param nonce:
        :param founder:
        :param founder_balance:
        :param partner:
        :param partner_balance:
        :param founder_signature:
        :param partner_signature:
        :param invoker_key:
        :return:
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "closeChannel",
                                                     [channel_id, nonce,
                                                      founder, founder_balance,
                                                      partner, partner_balance,
                                                      founder_signature, partner_signature],invoker_key)
        return {
            "txData":tx_id
        }

    def update_transaction(self, invoker, channel_id, nonce, founder, founder_balance,
                           partner, partner_balance, founder_signature, partner_signature, invoker_key):
        """
        
        :param invoker: 
        :param channel_id: 
        :param nonce: 
        :param founder: 
        :param founder_balance: 
        :param partner: 
        :param partner_balance: 
        :param founder_signature: 
        :param partner_signature: 
        :param invoker_key:
        :return: 
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "updateTransaction",
                                                    [channel_id, nonce,
                                                     founder, founder_balance,
                                                     partner, partner_balance,
                                                     founder_signature, partner_signature],invoker_key)
        return {
            "txData":tx_id
        }

    def settle_transaction(self, invoker, channel_id, invoker_key):
        """

        :param invoker:
        :param channel_id:
        :param invoker_key:
        :return:
        """
        tx_id = self.eth_client.contruct_Transaction(invoker, self.contract,"settleTransaction",
                                                     [channel_id], invoker_key)
        return {
            "txData":tx_id
        }

    def withdraw(self, invoker, channel_id, nonce, founder, partner, lockPeriod, lock_amount, lock_hash,
                 founder_signature, partner_signature, secret, invoker_key):
        """

        :param invoker:
        :param channel_id:
        :param nonce:
        :param founder:
        :param partner:
        :param lockPeriod:
        :param lock_amount:
        :param lock_hash:
        :param founder_signature:
        :param partner_signature:
        :param secret:
        :param invoker_key:
        :return:
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "withdraw",
                                                     [channel_id, nonce, founder, partner,
                                                      lockPeriod, lock_amount, lock_hash,
                                                      founder_signature, partner_signature, secret],invoker_key)
        return {
            "txData":tx_id
        }

    def withdraw_update(self, invoker, channel_id, nonce, founder, partner, lock_period, lock_amount, lock_hash,
                        founder_signature, partner_signature, invoker_key):
        """

        :param invoker:
        :param channel_id:
        :param nonce:
        :param founder:
        :param partner:
        :param lock_period:
        :param lock_amount:
        :param lock_hash:
        :param founder_signature:
        :param partner_signature:
        :param invoker_key:
        :return:
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "withdrawUpdate",
                                                     [channel_id, nonce, founder, partner,
                                                      lock_period, lock_amount, lock_hash,
                                                      founder_signature, partner_signature], invoker_key)
        return {
            "txData":tx_id
        }

    def withdraw_settle(self, invoker, channel_id, nonce, founder, partner, lock_period, lock_amount, lock_hash,
                        founder_signature, partner_signature, secret, invoker_key):
        """

        :param invoker:
        :param channel_id:
        :param nonce:
        :param founder:
        :param partner:
        :param lock_period:
        :param lock_amount:
        :param lock_hash:
        :param founder_signature:
        :param partner_signature:
        :param secret:
        :param invoker_key:
        :return:
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "withdrawSettle",
                                                     [channel_id, nonce, founder, partner,
                                                      lock_period, lock_amount, lock_hash,
                                                      founder_signature, partner_signature, secret], invoker_key)
        return {
            "txData":tx_id
        }    

    def get_channel_total(self):
        """

        :return:
        """
        all_channels = self.eth_client.call_contract(self.contract,"getChannelCount",[])
        return {
            "totalChannels": all_channels
        }

    def get_channel_info_by_id(self, channel_id):
        """

        :param channel_id:
        :return:
        """
        channel_info = self.eth_client.call_contract(self.contract,"getChannelById",[channel_id])
        return {
            "channelInfo": channel_info
        }        

