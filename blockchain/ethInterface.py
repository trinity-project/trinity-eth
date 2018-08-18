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

        :param url: eth contract running location
        :param contract_address: eth contract address
        :param contract_abi: eth contract abi
        :param asset_address: erc20 contract address
        :param asset_abi: erc20 contract abi
        """
        if self.__first_init:
            self.__class__.__first_init = False
            self.eth_client = Client(eth_url=url)
            self.contract_address = checksum_encode(contract_address)

            self.contract=self.eth_client.get_contract_instance(contract_address,contract_abi)
            self.asset_contract=self.eth_client.get_contract_instance(asset_address,asset_abi)

    def approve(self, invoker, asset_amount, invoker_key, gwei_coef=1):
        """
        Description: the sender authorizes eth contract to spend the specified amount of assets on behalf of sender
        :param invoker: sender that trigger the transaction
        :param asset_amount: sender want to authorize asset number for spender
        :param invoker_key: sender's key
        :return: transaction id
        """
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.asset_contract, "approve",
                                                         [self.contract_address, asset_amount],
                                                         invoker_key, gwei_coef=gwei_coef)
            tx_msg = 'success'
        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }

    def get_approved_asset(self, contract_address, abi, approver, spender):
        """
        Description: get asset number that eth contract can spending
        :param contract_address: erc20 assets contract address
        :param abi: erc20 assets contract abi
        :param approver: asset owner address
        :param spender:  address that be authorized to spend the assets
        :return: have authorized assets number
        """
        return self.eth_client.get_approved_asset(contract_address, abi, approver, spender)

    def set_settle_timeout(self, invoker, timeout, invoker_key):
        """
        Description: set RSMC timeout block number, the number is relative blocks
        :param invoker: sender that trigger the transaction
        :param timeout: relative blocks number
        :param invoker_key: sender's key
        :return: transaction id
        """
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "setSettleTimeout", [timeout], invoker_key)
            tx_msg = 'success'

        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }

    def set_token(self, invoker, token_address, invoker_key):
        """
        Description: set erc20 token address, eth contract will interface with erc20 contract using the erc20 token address
        :param invoker: sender that trigger the transaction
        :param token_address: erc20 token address
        :param invoker_key: sender's key
        :return: transaction id
        """
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "setToken", [token_address], invoker_key)
            tx_msg = 'success'

        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }     
    
    def deposit(self, invoker, channel_id, nonce, founder, founder_amount,
                partner, partner_amount, founder_signature, partner_signature, invoker_key, gwei_coef=1):
        """
        Description: channel partners all transfer assets to eth contracts, the asset will be used as a credit endorsement.
        :param invoker: sender that trigger the transaction
        :param channel_id: channel identification code
        :param nonce: transaction nonce
        :param founder: the initiator of the channel creation
        :param founder_amount: founder will lock assets amount
        :param partner: the channel partner
        :param partner_amount: partner will lock assets amount
        :param founder_signature: funder's signature for above information
        :param partner_signature: funder's signature for above same information
        :param invoker_key: sender's key
        :return: transaction id
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.contract,"deposit",
                                                         [channel_id, nonce,
                                                         founder, founder_amount,
                                                         partner, partner_amount,
                                                         founder_signature, partner_signature], invoker_key,
                                                         gwei_coef=gwei_coef)
            tx_msg = 'success'
        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }

    def update_deposit(self, invoker, channel_id, nonce, founder, founder_amount,
                       partner, partner_amount, founder_signature, partner_signature, invoker_key):
        """
        Description: add lock assets amount
        :param meaning reference "deposit"
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "updateDeposit",
                                                         [channel_id, nonce,
                                                         founder, founder_amount,
                                                         partner, partner_amount,
                                                         founder_signature, partner_signature], invoker_key)
            tx_msg = 'success'
        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }

    def quick_close_channel(self, invoker, channel_id, nonce, founder, founder_balance,
                            partner, partner_balance, founder_signature, partner_signature, invoker_key, gwei_coef=1):
        """
        Description: channel partners have agreed to dismantle the channel
        :param invoker: sender that trigger the transaction
        :param channel_id: channel identification code
        :param nonce: transaction nonce
        :param founder: closer that close the channel
        :param founder_balance: founder remaining assets amount
        :param partner: another partner address
        :param partner_balance: the partner remaining assets amount
        :param founder_signature: founder signature for above information
        :param partner_signature: partner signature for above information
        :param invoker_key: sender's key
        :return: transaction id
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "quickCloseChannel",
                                                         [channel_id, nonce,
                                                         founder, founder_balance,
                                                         partner, partner_balance,
                                                         founder_signature, partner_signature], invoker_key,
                                                         gwei_coef=gwei_coef)
            tx_msg = 'success'
        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }

    def close_channel(self, invoker, channel_id, nonce, founder, founder_balance,
                      partner, partner_balance, founder_signature, partner_signature, invoker_key):
        """
        Description: one side of the channel dismantle the channel unilaterally
        :param meaning reference "quick_close_channel"
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "closeChannel",
                                                         [channel_id, nonce,
                                                         founder, founder_balance,
                                                         partner, partner_balance,
                                                         founder_signature, partner_signature],invoker_key)
            tx_msg = 'success'
        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }

    def update_transaction(self, invoker, channel_id, nonce, founder, founder_balance,
                           partner, partner_balance, founder_signature, partner_signature, invoker_key):
        """
        Description: the partner will confirm shutter transaction whether it is valid
        :param meaning reference "quick_close_channel"
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "updateTransaction",
                                                        [channel_id, nonce,
                                                         founder, founder_balance,
                                                         partner, partner_balance,
                                                         founder_signature, partner_signature],invoker_key)
            tx_msg = 'success'
        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }

    def settle_transaction(self, invoker, channel_id, invoker_key):
        """
        Description: channel shutter will apply for withdraw channel asset belong to shutter after arbitration period timeout
        :param invoker: shutter address
        :param channel_id: channel identification code
        :param invoker_key: shutter's key
        :return: transaction id
        """
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.contract,"settleTransaction",
                                                         [channel_id], invoker_key)
            tx_msg = 'success'
        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }

    def withdraw(self, invoker, channel_id, nonce, founder, partner, lockPeriod, lock_amount, lock_hash,
                 founder_signature, partner_signature, secret, invoker_key):
        """
        Description: it's for HLTC tranction, partner that have secret apply for withdraw asset
        :param invoker: applicant address
        :param channel_id: channel identification code
        :param nonce: transaction nonce
        :param founder: the transaction sender
        :param partner: the transaction receiver
        :param lockPeriod: absolute block height of the lock
        :param lock_amount: transfer asset amount
        :param lock_hash: secret's hash
        :param founder_signature: sender signature
        :param partner_signature: receiver signature
        :param secret:
        :param invoker_key: applicant's key
        :return:
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "withdraw",
                                                          [channel_id, nonce, founder, partner,
                                                          lockPeriod, lock_amount, lock_hash,
                                                          founder_signature, partner_signature, secret],invoker_key)
            tx_msg = 'success'
        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }

    def withdraw_update(self, invoker, channel_id, nonce, founder, partner, lock_period, lock_amount, lock_hash,
                        founder_signature, partner_signature, invoker_key):
        """
        Description: the partner will confirm whether the HLTC transaction is valid
        :param meaning reference "withdraw"
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "withdrawUpdate",
                                                          [channel_id, nonce, founder, partner,
                                                          lock_period, lock_amount, lock_hash,
                                                          founder_signature, partner_signature], invoker_key)
            tx_msg = 'success'
        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }

    def withdraw_settle(self, invoker, channel_id, nonce, founder, partner, lock_period, lock_amount, lock_hash,
                        founder_signature, partner_signature, secret, invoker_key):
        """
        Description: HTLC receiver can apply for withdraw the lock assets after lock period timeout
        :param meaning reference "withdraw"
        """
        founder = checksum_encode(founder)
        partner = checksum_encode(partner)
        try:
            tx_id = self.eth_client.contruct_Transaction(invoker, self.contract, "withdrawSettle",
                                                          [channel_id, nonce, founder, partner,
                                                          lock_period, lock_amount, lock_hash,
                                                          founder_signature, partner_signature, secret], invoker_key)
            tx_msg = 'success'
        except Exception as e:
            tx_id = 'none'
            tx_msg = e

        return {
            "txData":tx_id,
            "txMessage":tx_msg
        }    

    def get_channel_total(self):
        """
        Description: get all channel number
        :return:
        """
        all_channels = self.eth_client.call_contract(self.contract,"getChannelCount",[])
        return {
            "totalChannels": all_channels
        }

    def get_channel_info_by_id(self, channel_id):
        """
        Description: get the specified channel information by channel ID
        :param channel_id: channel identification code
        :return: channel information
        """
        channel_info = self.eth_client.call_contract(self.contract,"getChannelById",[channel_id])
        return {
            "channelInfo": channel_info
        }

    def get_transaction_receipt(self, hashString):
        """
        :param hashString: transaction tx id, the id must is string begin with '0x'
        :return: None -- if the transaction is pending status
                 Object - if the transaction have been confirmed.
                 example:
                        {
                        'blockHash': HexBytes('0xxx'),
                        'blockNumber': 3756035,
                        'contractAddress': None,
                        'cumulativeGasUsed': 1901159,
                        'from': '0xxx',
                        'gasUsed': 51240,
                        'logs': [],
                        'logsBloom': HexBytes('0xxx'),
                        'status': 0,
                        'to': '0xxx',
                        'transactionHash': HexBytes('0xxxx'),
                        'transactionIndex': 9
                        }
        """
        return self.eth_client.get_transaction_receipt(hashString)

    def get_channel_total_balance(self,channel_id):
        """
        Description: get specified channel total balance
        :return: channel total balance
        """
        total_balance = self.eth_client.call_contract(self.contract, "getChannelBalance",[channel_id])
        return {
            "totalChannelBalance": total_balance
        }