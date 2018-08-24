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
from common.singleton import SingletonClass
from common.log import LOG
from blockchain.ethInterface import Interface as EthInterface
from blockchain.web3client import Client as EthWebClient
from lightwallet.Settings import settings


class ContractEventInterface(metaclass=SingletonClass):
    """

    """
    _trinity_coef = pow(10, 8)
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

        for idx in range(start, len(typeList)):
            if typeList[idx] in ['uint256']:
                valueList[idx] = cls.multiply(valueList[idx])

        content = cls._eth_client.sign_args(typeList, valueList, privtKey).decode()
        return '0x' + content

    @classmethod
    def approve(cls, address, deposit, private_key, gwei_coef=1):
        approved_asset = cls.get_approved_asset(address)

        if float(approved_asset) >= float(deposit):
            LOG.info('Has been approved asset count: {}'.format(approved_asset))
            return True

        try:
            # return tx_id
            return cls._eth_interface.approve(address, cls.multiply(deposit), private_key, gwei_coef=gwei_coef)
        except Exception as error:
            LOG.error('authorized deposit error: {}'.format(error))

        return None

    @classmethod
    def get_approved_asset(cls, address):
        try:
            result = cls._eth_interface.get_approved_asset(settings.TNC, settings.TNC_abi,
                                                           address, settings.ETH_Data_Contract_address)
            return float(result) if result else 0
        except Exception as error:
            LOG.error('get_approved_asset error: {}'.format(error))
            return 0

    @classmethod
    def get_transaction_receipt(cls, tx_id):
        try:
            result = cls._eth_interface.get_transaction_receipt(tx_id)
            if result:
                print(result)
            return
        except Exception as error:
            LOG.error('get_approved_asset error: {}'.format(error))
            return None

    @classmethod
    def approve_deposit(cls, address, channel_id, nonce, founder, founder_amount, partner, partner_amount,
                        founder_sign, partner_sign, private_key, gwei_coef=1):
        try:
            return cls._eth_interface.deposit(address,channel_id, nonce,
                                       founder, cls.multiply(founder_amount),
                                       partner, cls.multiply(partner_amount),
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
                                                   founder, cls.multiply(founder_balance),
                                                   partner, cls.multiply(partner_balance),
                                                   founder_signature, partner_signature, invoker_key,
                                                          gwei_coef=gwei_coef)
        except Exception as error:
            LOG.error('quick_settle error: {}'.format(error))
            return None

    @classmethod
    def sign_content(cls, start=3, *args, **kwargs):
        """

        :return:
        """
        typeList = args[0] if 0 < len(args) else kwargs.get('typeList')
        valueList = args[1] if 1 < len(args) else kwargs.get('valueList')
        privtKey = args[2] if 2 < len(args) else kwargs.get('privtKey')

        for idx in range(start, len(typeList)):
            if typeList[idx] in ['uint256']:
                valueList[idx] = cls.multiply(valueList[idx])

        content = cls._eth_client.sign_args(typeList, valueList, privtKey).decode()
        return '0x' + content

    @classmethod
    def multiply(cls, asset_count):
        return int(float(asset_count) * cls._trinity_coef)

    @classmethod
    def divide(cls, asset_count):
        return float(asset_count) / cls._trinity_coef
