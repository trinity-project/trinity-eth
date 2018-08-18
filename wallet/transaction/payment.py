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
import base58
import binascii
from Crypto import Random
from eth_hash.backends.pysha3 import keccak256

from common.log import LOG
from common.console import console_log
from common.singleton import SingletonClass
from .message import Message
from .response import EnumResponseStatus
from wallet.utils import get_asset_type_id, get_magic
from trinity import IS_SUPPORTED_ASSET_TYPE, SUPPORTED_ASSET_TYPE
from wallet.channel import Channel
from wallet.channel.trade import EnumTradeState


class Payment(metaclass=SingletonClass):
    """

    """
    def __init__(self):
        pass

    @classmethod
    def generate_payment_code(cls, receiver, asset_type, value, hashcode, comments='', cli=False):
        """"""
        if 0 >= float(value):
            console_log.error('Not support negative number.')
            return

        if not IS_SUPPORTED_ASSET_TYPE(asset_type):
            text = 'AssetType: {} is not supported'.format(asset_type)
            LOG.error(text)
            if cli:
                console_log.error(text)

            return None

        asset_type = asset_type.replace('0x', '')
        if asset_type.upper() in SUPPORTED_ASSET_TYPE.keys():
            asset_type = asset_type.upper()

        hashcode = hashcode.strip()
        hashcode = hashcode.replace('0x', '')

        code = "{uri}&{net_magic}&{hashcode}&{asset_type}&{payment}&{comments}".format(uri=receiver,
                                                                                       net_magic=get_magic(),
                                                                                       hashcode=hashcode,
                                                                                       asset_type=asset_type,
                                                                                       payment=value,
                                                                                       comments=comments)
        base58_code = base58.b58encode(code.encode())
        try:
            return "TN{}".format(base58_code.decode())
        except:
            return "TN{}".format(base58_code)

    @classmethod
    def hash_r(cls, r):
        return '0x'+keccak256(bytes.fromhex(r)).hex()

    @classmethod
    def decode_payment_code(cls, payment_code):
        if not payment_code.startswith("TN"):
            LOG.error("Payment code MUST start with TN")
            return False, None

        base58_code = payment_code[2:]
        code = base58.b58decode(base58_code).decode()
        info = code.split("&",5)

        if 6 != len(info):
            return False, None

        keys=['uri', 'net_magic', 'hashcode', 'asset_type', 'payment', 'comments']

        result = dict(zip(keys, info))
        result['hashcode'] = '0x'+result['hashcode']

        return True, result

    @classmethod
    def create_hr(cls):
        rcode = binascii.b2a_hex(Random.get_random_bytes(32)).decode()
        hashcode = cls.hash_r(rcode)

        return hashcode, '0x'+rcode

    @classmethod
    def verify_hr(cls, hashcode, rcode):
        return hashcode.__contains__(cls.hash_r(rcode).__str__())

    @classmethod
    def is_valid_hash_r(cls, hashcode):
        return isinstance(hashcode, str) and hashcode.startswith('TN')

    @classmethod
    def confirm_payment(cls, channel_name, hashcode, payment=0):
        try:
            if cls.is_valid_hash_r(hashcode):
                payment_hash = Channel.query_payment(channel_name, hashcode=hashcode)[0]
                # Todo: verify the payment count
                #
                # update the payment to confirm
                Channel.update_payment(channel_name, hashcode, state=EnumTradeState.confirmed.name)
        except Exception as error:
            LOG.exception('Payment for channel<{}> with HashR<{}> Not found from the DB'.format(channel_name, hashcode),
                          'Exception: {}'.format(error))

        return



class PaymentAck(Message):
    """
        {
        "MessageType": "PaymentAck",
        "Receiver": "03dc2841ddfb8c2afef94296693315a234026fa8f058c3e4259a04f8be6d540049@106.15.91.150:8089",
        "MessageBody": {
            "HashR": "Hr"
        }
        "Status": 'status'
    }
    """
    _message_name = 'PaymentAck'

    def __init__(self,message, wallet):
        super().__init__(message)
        self.wallet = wallet

    @staticmethod
    def create(sender, receiver, channel_name, asset_type, nonce, hr):
        message = PaymentAck.create_message_header(sender, receiver, PaymentAck._message_name,
                                                   channel_name, asset_type, nonce)
        message = message.message_header
        message_body = {'HashR': hr}
        message.update({'MessageBody': message_body})
        message.update({'Status': EnumResponseStatus.RESPONSE_OK.name})

        Message.send(message)


class PaymentLink(Message):
    """
    {
        MessageHeader,
        "MessageBody":{
                "PaymentCount": 0,
                "Comments": "Description"
        }
    }"""
    _message_name = 'PaymentLink'

    def __init__(self, message):
        super(PaymentLink, self).__init__(message)

        self.payment = self.message_body.get('PaymentCount')
        self.comments = self.message_body.get('Comments')

    def handle_message(self):
        self.handle()

    def handle(self):
        super(PaymentLink, self).handle()

        PaymentLinkAck.create(self.receiver, self.sender, self.channel_name, self.asset_type,
                              self.payment, self.nonce, self.comments)

        return None


class PaymentLinkAck(Message):
    """
    {
        MessageHeader,
        "MessageBody":{
                "PaymentLink": XXXXX,
        }
        "Status":,
        "Comments": ,
    }"""
    _message_name = 'PaymentLinkAck'

    def __init__(self, message):
        super().__init__(message)

        self.payment = self.message_body.get('PaymentCount')
        self.comments = self.message_body.get('Comments')

    @staticmethod
    def create(sender, receiver, channel_name, asset_type, payment, nonce, comments=''):
        message = PaymentLinkAck.create_message_header(sender, receiver, PaymentLinkAck._message_name,
                                                       channel_name, asset_type, nonce)

        hashcode, rcode = Payment.create_hr()
        Channel.add_payment(channel_name, hashcode=hashcode, rcode=rcode, payment=payment, state=EnumTradeState.confirming)
        pycode = Payment.generate_payment_code(sender, asset_type, payment, hashcode, comments)

        message = message.message_header
        message_body = {'PaymentLink': pycode}
        message.update({'MessageBody': message_body})
        message.update({'Status': EnumResponseStatus.RESPONSE_OK.name})
        if comments:
            message.update({'Comments': comments})
        Message.send(message)
        pass

    def handle_message(self):
        super(PaymentLinkAck, self).handle()
        return None

