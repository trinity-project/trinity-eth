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
from enum import IntEnum

# self modules import
from wallet.utils import get_magic
from log.log import LOG


class EnumResponseStatus(IntEnum):
    RESPONSE_OK     = 0x0

    # Fonder Message
    RESPONSE_FONDER_DEPOSIT_NOT_ENOUGH = 0x10

    # Common response error
    RESPONSE_EXCEPTION_HAPPENED = 0xF0
    RESPONSE_FAIL   = 0XFF


class MessageHeaderBase(object):
    """
        Message header is used for channel transaction.
    """
    def __init__(self, message_type:str, sender:str, receiver:str, channel_name:str, nonce:int, comments = None, **kwargs):
        assert sender.__contains__('@'), 'Invalid sender<{}>.'.format(sender)
        assert sender.__contains__('@'), 'Invalid receiver<{}>.'.format(receiver)

        self.message_header = {
            "MessageType":message_type,
            "Sender": sender,
            "Receiver": receiver,
            "TxNonce": nonce,
            "ChannelName":channel_name,
            "NetMagic": get_magic()
        }

        if comments:
            self.message_header.update({'Comments': comments})

        if kwargs:
            self.message_header.update(kwargs)


class Message(object):
    """

    """

    def __init__(self, message):
        self.message = message
        self.receiver = message.get("Receiver")
        self.sender = message.get("Sender")
        assert self.sender != self.receiver, 'Sender should be different from receiver.'

        self.message_type = message.get("MessageType")
        self.message_body = message.get("MessageBody")
        self.error = message.get("Error")
        # self.network_magic = get_magic()

    @property
    def network_magic(self):
        return get_magic()

    @staticmethod
    def get_magic():
        return get_magic()



    @staticmethod
    def send(message):
        send_message(message)

    def handle(self):
        LOG.info('Received Message<{}>'.format(self.message_type))

