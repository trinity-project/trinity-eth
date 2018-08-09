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
from common.log import LOG
from wallet.Interface.gate_way import send_message


class MessageHeader(object):
    """
        Message header is used for event transaction.
    """
    def __init__(self, sender:str, receiver:str, message_type:str, channel_name:str, nonce:int):
        # here we could use the regex expression to judge the ip format accurately.
        assert sender.__contains__('@'), 'Invalid sender<{}>.'.format(sender)
        assert receiver.__contains__('@'), 'Invalid receiver<{}>.'.format(receiver)
        assert self.sender != self.receiver, 'Sender should be different from receiver.'

        self.message_header = {
            'MessageType':message_type,
            'Sender': sender,
            'Receiver': receiver,
            'TxNonce': str(nonce),
            'ChannelName':channel_name,
            'NetMagic': get_magic()
        }


class Message(object):
    """
    {
        'MessageType': 'Founder',
        'Sender': sender,
        'Receiver': receiver,
        'TxNonce': '0',
        'ChannelName': channel_name,
        'NetMagic': magic,
    }

    """

    def __init__(self, message):
        self.message = message

        self.sender = message.get('Sender')
        self.receiver = message.get('Receiver')
        self.message_type = message.get('MessageType')
        self.message_body = message.get('MessageBody')
        self.channel_name = message.get('ChannelName')
        self.status = message.get('Status')

    @property
    def network_magic(self):
        return get_magic()

    @staticmethod
    def send(message):
        send_message(message)

    @staticmethod
    def create(sender, receiver, message_type, channel_name, nonce):
        return MessageHeader(sender, receiver, message_type, channel_name, nonce)

    def handle(self):
        LOG.info('Received Message<{}>'.format(self.message_type))

