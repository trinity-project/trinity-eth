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
# system and 3rd party libs
import math

# self modules import
from wallet.utils import get_magic
from common.common import uri_parser
from common.log import LOG
from common.exceptions import GoTo
from wallet.channel import Channel
from wallet.Interface.gate_way import send_message
from .response import EnumResponseStatus
from trinity import IS_SUPPORTED_ASSET_TYPE
from wallet.event import event_machine
from wallet.event.contract_event import ContractEventInterface

class MessageHeader(object):
    """
        Message header is used for event transaction.
    """
    def __init__(self, sender:str, receiver:str, message_type:str, channel_name:str, asset_type:str, nonce:int):
        # here we could use the regex expression to judge the ip format accurately.
        assert sender.__contains__('@'), 'Invalid sender<{}>.'.format(sender)
        assert receiver.__contains__('@'), 'Invalid receiver<{}>.'.format(receiver)
        assert sender != receiver, 'Sender should be different from receiver.'

        self.message_header = {
            'MessageType':message_type,
            'Sender': sender,
            'Receiver': receiver,
            'TxNonce': str(nonce),
            'ChannelName': channel_name,
            'AssetType': asset_type.upper(),
            'NetMagic': get_magic()
        }


class Message(object):
    """
    {
        'MessageType': 'MessageType',
        'Sender': sender,
        'Receiver': receiver,
        'TxNonce': '0',
        'ChannelName': channel_name,
        'AssetType': 'TNC',
        'NetMagic': magic,
    }

    """
    _SETTLE_NONCE = 0
    _FOUNDER_NONCE = 1
    _message_name = None
    _contract_event_api = None

    def __init__(self, message):
        self.message = message

        self.sender = message.get('Sender')
        self.sender_address, _, _ = uri_parser(self.sender)
        self.receiver = message.get('Receiver')
        self.receiver_address, _, _, = uri_parser(self.receiver)

        self.message_type = message.get('MessageType')
        self.message_body = message.get('MessageBody')
        self.channel_name = message.get('ChannelName')
        self.asset_type = message.get('AssetType','INVALID_ASSET').upper()
        self.nonce = int(message.get('TxNonce'))
        self.net_magic = message.get('NetMagic')
        self.status = message.get('Status')
        self.comments = self.message.get('Comments')

    @property
    def network_magic(self):
        return get_magic()

    @staticmethod
    def send(message):
        send_message(message)

    @staticmethod
    def create_message_header(sender:str, receiver:str, message_type:str, channel_name:str, asset_type:str, nonce:int):
        return MessageHeader(sender, receiver, message_type, channel_name, asset_type, nonce)

    def handle(self):
        LOG.info('Received Message<{}>'.format(self.message_type))
        pass

    @classmethod
    def check_nonce(cls, channel_name, nonce):
        """

        :param channel_name:
        :param nonce:
        :return:
        """
        new_nonce = Channel.new_nonce(channel_name)
        return Message._FOUNDER_NONCE < int(nonce) == new_nonce, new_nonce

    @classmethod
    def contract_event_api(cls):
        if not cls._contract_event_api:
            cls._contract_event_api = ContractEventInterface()

        return cls._contract_event_api

    @classmethod
    def sign_content(cls, start=3, *args, **kwargs):
        return cls.contract_event_api().sign_content(start, *args, **kwargs)

    @classmethod
    def check_balance(cls, channel_name, asset_type, address, balance, peer_address, peer_balance):
        """

        :param address:
        :param balance:
        :param peer_address:
        :param peer_balance:
        :return:
        """
        try:
            # get channel if trade has already existed
            channel_set = Channel.query_channel(channel_name)[0]

            expected_balance = channel_set.balance.get(address).get(asset_type)
            expected_peer_balance = channel_set.balance.get(peer_address).get(asset_type)

            return float(balance) == float(expected_balance) and float(peer_balance) == float(expected_peer_balance)
        except Exception as error:
            LOG.error('Channel<{}> was not found. Exception: {}'.format(channel_name, error))
            return False

    def verify(self):
        """

        :return:
        """
        # to validate the parameters
        try:
            if not IS_SUPPORTED_ASSET_TYPE(self.asset_type):
                return False, 'Unsupported Asset type: \'{}\''.format(self.asset_type)

            # check whether the sender and receiver are correct url or not
            # TODO: it's better to use regex expression to check the url's validity
            if not(self.sender.__contains__('@') and self.receiver.__contains__('@')):
                return False, 'Invalid format of sender or receiver. Should be like 0xYYYY@ip:port'

            if self.network_magic != self.net_magic:
                return False, 'Invalid network ID. {} != {}'.format(self.network_magic, self.net_magic)

        except Exception as error:
            return False, error
        else:
            return True, None

    def verify_response_status(self):
        if self.status is not None \
                and (self.status != EnumResponseStatus.RESPONSE_OK.name
                     or self.status != EnumResponseStatus.RESPONSE_OK.value):
            return False, '{}'.format(self.status)

        return True, None

    def verify_channel_balance(self, balance, peer_balance, payment):
        try:
            channel = Channel(self.channel_name)
            sender_balance = float(channel.balance.get(self.sender_address)) - float(payment)
            receiver_balance = float(channel.balance.get(self.receiver_address)) + float(payment)

            if sender_balance != float(balance) or receiver_balance != float(peer_balance):
                return False, 'Balances of peers DO NOT matched. sender<self: {}, peer {}>, receiver<self: {}, peer {}>'\
                    .format(sender_balance, balance, receiver_balance, peer_balance)
            pass
        except Exception as error:
            return False, 'Error to verify balance. Exception{}'.format(error)
        finally:
            return True, None

    @classmethod
    def float_to_int(cls, number:str):
        coef = 8
        if number.__contains__('e'):
            number_list = number.split('e')
            return math.ceil(float(number_list[0]) * pow(10, int(number_list[1])+coef))
        elif number.__contains__('.'):
            number_list = number.split('.')
            integer = int(number_list[0]) * pow(10, coef)
            fragment = int(number_list[1]) * pow(10, 8 - len(number_list[1]))
            return integer + fragment
        else:
            return int(number) * pow(10, 8)

    @classmethod
    def float_calculate(cls, balance, payment, add=True):
        trinity_coef = 100000000   # pow(10, 8)
        balance = cls.float_to_int(balance.__str__())
        payment = cls.float_to_int(payment.__str__())

        # calculate
        if add:
            result = balance + payment
        else:
            result = balance - payment

        return result/trinity_coef

    @classmethod
    def hashr_is_valid_format(cls, hashcode):
        return isinstance(hashcode, str) and hashcode.startswith('TN')

    @classmethod
    def get_peer(cls, channel_set, source):
        if not channel_set:
            return None
        peer = channel_set.src_addr

        return peer if peer != source else channel_set.dest_addr

    @classmethod
    def check_payment(cls, channel_name, address, asset_type, payment):
        try:
            channel_balance = Channel(channel_name).balance
            balance = channel_balance.get(address).get(asset_type.upper())

            if not 0 < float(payment) <= float(balance):
                raise GoTo('Invalid payment')

            return True, float(balance)
        except Exception as error:
            LOG.error('check payment error: {}.'.format(error))
            LOG.error('Parameters: channel<{}>, address<{}>, asset_type<{}>, payment<{}>'.format(channel_name,
                                                                                                 address,
                                                                                                 asset_type,
                                                                                                 payment))
            return False, None

    @classmethod
    def send_error_response(cls, sender:str, receiver:str, channel_name:str, asset_type:str,
                       nonce:int, status=EnumResponseStatus.RESPONSE_FAIL):
        message = cls.create_message_header(receiver, sender, cls._message_name, channel_name, asset_type, nonce)
        message = message.message_header
        message.update({'MessageBody': {}})

        if status:
            message.update({'Status': status.name})

        cls.send(message)

    @classmethod
    def rollback_resource(cls, channel_name, nonce, payment=None, status=None):
        """

        :param channel_name:
        :param nonce:
        :param payment:
        :return:
        """
        # failure action
        if status == EnumResponseStatus.RESPONSE_TRADE_INCOMPATIBLE_NONCE.name:
            Channel.delete_trade(channel_name, int(nonce))

        if status is not None and status != EnumResponseStatus.RESPONSE_OK.name:
            event_machine.unregister_event(channel_name)

    @classmethod
    def check_channel_state(cls, channel_name):
        channel = Channel(channel_name)
        assert channel.is_opened, 'Channel is not OPENED. State<{}>'.format(channel.state)
        return channel.is_opened

    @classmethod
    def update_balance_for_channel(cls, channel_name, payer_address, payee_address, asset_type, payment):
        channel = Channel(channel_name)

        try:
            asset_type = asset_type.upper()
            payment = float(payment)
            channel_balance = channel.balance
            payer_balance = channel_balance.get(payer_address).get(asset_type)
            payee_balance = channel_balance.get(payee_address).get(asset_type)

            payer_balance = cls.float_calculate(payer_balance, payment, False)
            payee_balance = cls.float_calculate(payee_balance, payment)

            if payer_balance >= 0 and payee_balance >= 0:
                Channel.update_channel(channel_name,
                                       balance={payer_address: {asset_type: payer_balance},
                                                payee_address: {asset_type: payee_balance}})
            else:
                raise Exception('Payer has not enough balance for this payment<{}>'.format(payment))

        except Exception as error:
            LOG.error('Update channel<{}> balance error. payment<{}>. Exception: {}'.format(channel_name, payment, error))
