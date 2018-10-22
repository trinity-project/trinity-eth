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
from common.log import LOG
from .message import Message
from .response import EnumResponseStatus
from wallet.channel import Channel, Payment
from wallet.channel.trade import EnumTradeState


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
        Channel.add_payment(channel_name, hashcode=hashcode, rcode=rcode, payment=payment)
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

