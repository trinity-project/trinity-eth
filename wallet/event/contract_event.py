# --*-- coding : utf-8 --*--
"""Author: Trinity Core Team

MIT License

Copyright (c) 2018 Trinity

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
from enum import IntEnum
from common.singleton import SingletonClass
from common.log import LOG
from common.number import TrinityNumber
from common.exceptions import ContractEventException
from blockchain.ethInterface import Interface as EthInterface
from blockchain.web3client import Client as EthWebClient
from lightwallet.Settings import settings


class EnumContractEventStatus(IntEnum):
    """"""
    # signature related status
    CONTRACT_SOLIDITY_HASH_EXCEPTION = 0x0


class ContractEventInterface(metaclass=SingletonClass):
    """

    """
    _eth_interface = None
    _eth_client = None

    def __init__(self):
        ContractEventInterface._eth_interface = EthInterface(settings.NODEURL,
                                                             settings.ETH_Data_Contract_address,
                                                             settings.Eth_Contract_address,
                                                             settings.Eth_Contract_abi,
                                                             settings.TNC,
                                                             settings.TNC_abi)
        ContractEventInterface._eth_client = EthWebClient(settings.NODEURL)

    @property
    def gwei_coefficient(self):
        return EthWebClient.get_gas_price()

    @classmethod
    def sign_content(cls, start=3, *args, **kwargs):
        """

        :return:
        """
        typeList = args[0] if 0 < len(args) else kwargs.get('typeList')
        valueList = args[1] if 1 < len(args) else kwargs.get('valueList')
        privtKey = args[2] if 2 < len(args) else kwargs.get('privtKey')

        content = cls._eth_client.sign_args(typeList, valueList, privtKey)
        return '0x' + content

    @classmethod
    def solidity_hash(cls, type_list, value_list):
        try:
            return cls._eth_client.solidity_hash(type_list, value_list)
        except Exception as error:
            raise ContractEventException(
                EnumContractEventStatus.CONTRACT_SOLIDITY_HASH_EXCEPTION,
                'Solidity Hash error with type_list<{}>, value_list<{}>. Exception: {}' \
                    .format(type_list, value_list, error)
            )

    @classmethod
    def approve(cls, address, deposit, private_key, gwei_coef=1):
        approved_asset = cls.get_approved_asset(address)

        deposit = int(deposit)
        if approved_asset >= deposit:
            LOG.info('Has been approved asset count: {}'.format(approved_asset))
            return True

        try:
            # return tx_id
            tx_id = cls._eth_interface.approve(address, deposit, private_key, gwei_coef=gwei_coef)
            LOG.debug('ContractEventInterface::approve: txId: {}'.format(tx_id))
            return tx_id
        except Exception as error:
            LOG.error('authorized deposit error: {}'.format(error))

        return False

    @classmethod
    def get_approved_asset(cls, address):
        try:
            result = cls._eth_interface.get_approved_asset(settings.TNC, settings.TNC_abi,
                                                           address, settings.ETH_Data_Contract_address)

            if result:
                result = TrinityNumber(str(result)).number

            return result
        except Exception as error:
            LOG.error('get_approved_asset error: {}'.format(error))
            return 0

    @classmethod
    def get_transaction_receipt(cls, tx_id):
        try:
            result = cls._eth_interface.get_transaction_receipt(tx_id)
            if result:
                print(result)
            return result
        except Exception as error:
            LOG.error('get_approved_asset error: {}'.format(error))
            return None

    @classmethod
    def approve_deposit(cls, address, channel_id, nonce, founder, founder_amount, partner, partner_amount,
                        founder_sign, partner_sign, private_key, gwei_coef=1):
        try:
            return cls._eth_interface.deposit(address,channel_id, nonce,
                                       founder, int(founder_amount),
                                       partner, int(partner_amount),
                                       founder_sign, partner_sign, private_key, gwei_coef=gwei_coef)
        except Exception as error:
            LOG.error('approve_deposit error: {}'.format(error))
            return None

    @classmethod
    def get_channel_total_balance(cls, channel_id):
        return cls._eth_interface.get_channel_total_balance(channel_id).get('totalChannelBalance', 0)

    @classmethod
    def quick_settle(cls, invoker, channel_id, nonce, founder, founder_balance,
                     partner, partner_balance, founder_signature, partner_signature, invoker_key, gwei_coef=1):
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
        try:
            return cls._eth_interface.quick_close_channel(invoker, channel_id, nonce,
                                                   founder, int(founder_balance),
                                                   partner, int(partner_balance),
                                                   founder_signature, partner_signature, invoker_key,
                                                          gwei_coef=gwei_coef)
        except Exception as error:
            LOG.error('quick_settle error: {}'.format(error))
            LOG.error('quick_settle parameters: '
                      'channel<{}>, nonce<{}>, '
                      'founder<{}>, founder_balance<{}>, founder_signature<{}>, '
                      'partner<{}>, partner_balance<{}>, partner_signature<{}>' \
                      .format(channel_id, nonce, founder, founder_balance, founder_signature,
                              partner, partner_balance, partner_signature))
            return None

    @classmethod
    def close_channel(cls, invoker, channel_id, nonce, founder, founder_balance, partner, partner_balance,
                      lock_hash, lock_secret, founder_signature, partner_signature, invoker_key, gwei_coef=1):
        try:
            result = cls._eth_interface.close_channel(invoker, channel_id, nonce,
                                                      founder, int(founder_balance),
                                                      partner, int(partner_balance),
                                                      lock_hash, lock_secret,
                                                      founder_signature, partner_signature, invoker_key,
                                                      gwei_coef=gwei_coef)
            LOG.debug('close_channel result: {}'.format(result))
            return result
        except Exception as error:
            LOG.error('force_settle error: {}'.format(error))
            return None

    @classmethod
    def update_close_channel(cls, invoker, channel_id, nonce, founder, founder_balance, partner, partner_balance,
                             lock_hash, lock_secret, founder_signature, partner_signature, invoker_key, gwei_coef=1):
        try:
            result = cls._eth_interface.update_transaction(invoker, channel_id, nonce,
                                                           founder, int(founder_balance),
                                                           partner, int(partner_balance),
                                                           lock_hash, lock_secret,
                                                           founder_signature, partner_signature, invoker_key,
                                                           gwei_coef= gwei_coef)
            LOG.debug('update_close_channel result: {}'.format(result))
            return result
        except Exception as error:
            LOG.error('update_close_channel error: {}'.format(error))
            return None

    @classmethod
    def end_close_channel(cls, invoker, channel_id, invoker_key, gwei_coef=1):
        try:
            result =  cls._eth_interface.settle_transaction(invoker, channel_id, invoker_key, gwei_coef=gwei_coef)
            LOG.debug('end_close_channel result: {}'.format(result))
            return result
        except Exception as error:
            LOG.error('end force_settle error: {}'.format(error))
            return None

    @classmethod
    def htlc_unlock_payment(cls, invoker, channel_id, founder, partner, lock_period, lock_amount, lock_hash,
                            founder_signature, partner_signature, secret, invoker_key):
        try:
            result =  cls._eth_interface.withdraw(invoker, channel_id, founder, partner, lock_period, lock_amount,
                                                  lock_hash, founder_signature, partner_signature, secret, invoker_key)
            LOG.debug('htlc_unlock_payment result: {}'.format(result))
            return result
        except Exception as error:
            LOG.error('htlc_unlock_payment error: {}'.format(error))
            return None

    @classmethod
    def punish_when_htlc_unlock_payment(cls):
        pass

    @classmethod
    def settle_after_htlc_unlock_payment(cls):
        pass
