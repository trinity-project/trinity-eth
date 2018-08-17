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

# self modules import
from wallet.utils import get_magic
from common.common import uri_parser
from common.log import LOG
from wallet.channel import Channel
from wallet.Interface.gate_way import send_message
from .response import EnumResponseStatus
from trinity import IS_SUPPORTED_ASSET


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
    _FOUNDER_NONCE = 0
    _SETTLE_NONCE = 0xFFFFFFFF

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

    def verify(self):
        """

        :return:
        """
        # to validate the parameters
        try:
            if not IS_SUPPORTED_ASSET(self.asset_type):
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

    def verify_channel_balance(self, balance, peer_balance):
        try:
            channel = Channel(self.channel_name)
            sender_balance = channel.balance.get(self.sender_address)
            receiver_balance = channel.balance.get(self.receiver_address)

            if sender_balance != balance or receiver_balance != peer_balance:
                return False, 'Balances of peers DO NOT matched'
            pass
        except Exception as error:
            return False, 'Error to verify balance. Exception{}'.format(error)
        finally:
            return True, None

    @classmethod
    def float_calculate(cls, balance, payment, add=True):
        trinity_coef = 100000000 # pow(10, 8)

        if add:
            result = int(trinity_coef*float(balance)) + int(trinity_coef*float(payment))
        else:
            result = int(trinity_coef*float(balance)) - int(trinity_coef*float(payment))

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

