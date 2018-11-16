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
from .message import Message
from .response import EnumResponseStatus

from common.log import LOG
from common.common import uri_parser
from common.exceptions import GoTo
from wallet.channel import Channel
from wallet.channel import EnumTradeType, EnumTradeRole
from wallet.event.channel_event import ChannelQuickSettleEvent
from wallet.event.event import EnumEventAction, event_machine


class SettleBase(Message):
    """
    Descriptions: for quick-closing channels
    """
    _sign_type_list = ['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256']

    def __init__(self, message, wallet):
        super(SettleBase, self).__init__(message)

        self.sender_balance = self.message_body.get('SenderBalance')
        self.receiver_balance = self.message_body.get("ReceiverBalance")
        self.commitment = self.message_body.get('Commitment')

        self.wallet = wallet

    @classmethod
    def check_nonce(cls, nonce, **kwargs):
        """

        :param nonce:
        :param kwargs:
        :return:
        """
        if SettleBase._SETTLE_NONCE != int(nonce):
            raise GoTo(EnumResponseStatus.RESPONSE_QUICK_CLOSE_CHANNEL_WITH_ILLEGAL_NONCE,
                       'Quick close channel with invalid nonce<{}>. Must be zero'.format(nonce))

        return True

    def register_quick_close_event(self, is_founder=True):
        """

        :param is_founder:
        :return:
        """
        try:
            channel_event = ChannelQuickSettleEvent(self.channel_name, self.wallet.address, is_founder)

            if is_founder:
                settle_trade = Channel.query_trade(self.channel_name, SettleBase._SETTLE_NONCE)

                # register arguments for execution action
                channel_event.register_args(
                    EnumEventAction.EVENT_EXECUTE, self.receiver_address, self.channel_name, self.nonce,
                    self.receiver_address, settle_trade.balance,
                    self.sender_address, settle_trade.peer_balance,
                    settle_trade.commitment, self.commitment,
                    self.wallet._key.private_key_string
                )

            # register arguments for termination action
            channel_event.register_args(EnumEventAction.EVENT_TERMINATE, asset_type=self.asset_type)
        except Exception as error:
            LOG.exception('Failed to regiser quick close channel event since {}'.format(error))
        else:
            # register and trigger the event
            event_machine.register_event(self.channel_name, channel_event)
            event_machine.trigger_start_event(self.channel_name)

    @classmethod
    def add_or_update_quick_settle_trade(cls, channel_name, expected_role, **kwargs):
        """

        :param channel_name:
        :param expected_role:
        :param kwargs:
        :return:
        """
        nonce = cls._SETTLE_NONCE
        try:
            settle_trade_db = Channel.query_trade(channel_name, nonce)[0]
        except Exception as error:
            LOG.debug('No quick settle is created before. Exception: {}'.format(error))
            Channel.add_trade(channel_name, nonce=nonce, **kwargs)
        else:
            # check the role of the database:
            if settle_trade_db.role != expected_role.name:
                # update the settle database
                Channel.update_trade(channel_name, nonce, **kwargs)


class SettleMessage(SettleBase):
    """
    {
    "MessageType":"Settle",
    "Sender": "0x9090909090909090909090909@127.0.0.1:20553",
    "Receiver":"0x101010101001001010100101@127.0.0.1:20552",
    "TxNonce": -1,   # int type
    "ChannelName":"902ae9090232048575",
    "AssetType": "TNC",
    "MessageBody": {
            "Commitment":"",
            "SenderBalance": int(),
            "ReceiverBalance": int()
        }
    }
    """
    _message_name = 'Settle'

    def handle_message(self):
        self.handle()

    def handle(self):
        super(SettleMessage, self).handle()
        status = EnumResponseStatus.RESPONSE_OK
        nonce = self.nonce

        try:
            # common check arguments
            self.verify()
            self.check_nonce(self.nonce)
            self.check_balance(self.channel_name, self.asset_type, self.sender_address, self.sender_balance,
                               self.receiver_address, self.receiver_balance)
            self.check_signature(
                self.wallet, self.sender_address,
                type_list=self._sign_type_list,
                value_list=[self.channel_name, self.nonce, self.sender_address, int(self.sender_balance),
                            self.receiver_address, int(self.receiver_balance)],
                signature=self.commitment
            )

            # To create settle response message
            SettleResponseMessage.create(self.wallet, self.channel_name, self.asset_type, self.nonce,
                                         self.sender, self.sender_balance, self.receiver, self.receiver_balance,
                                         self.commitment)
        except GoTo as error:
            LOG.exception(error)
            status = error.reason
        except Exception as error:
            LOG.exception(error)
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
        finally:
            if EnumResponseStatus.RESPONSE_OK != status:
                SettleResponseMessage.send_error_response(self.sender, self.receiver, self.channel_name, self.asset_type,
                                                          nonce, status)
            else:
                # register the settle event
                self.register_quick_close_event(False)

            return

    @staticmethod
    def create(wallet, receiver, channel_name, asset_type):
        """

        :param channel_name:
        :param wallet:
        :param sender:
        :param receiver:
        :param asset_type:
        :return:
        """
        sender = wallet.url
        channel = Channel(channel_name)
        nonce = SettleMessage._SETTLE_NONCE
        asset_type = asset_type.upper()

        sender_address, _, _, = uri_parser(sender)
        receiver_address, _, _, = uri_parser(receiver)

        balance = channel.balance
        sender_balance = balance.get(sender_address, {}).get(asset_type)
        receiver_balance = balance.get(receiver_address, {}).get(asset_type)

        commitment = SettleMessage.sign_content(
            wallet, SettleMessage._sign_type_list,
            [channel_name, nonce, sender_address, int(sender_balance), receiver_address, int(receiver_balance)]
        )

        # add trade to database
        settle_trade = Channel.settle_trade(
            type = EnumTradeType.TRADE_TYPE_QIUCK_SETTLE, role=EnumTradeRole.TRADE_ROLE_FOUNDER,
            asset_type=asset_type, balance=sender_balance, peer_balance=receiver_balance, commitment=commitment)
        SettleMessage.add_or_update_quick_settle_trade(channel_name, EnumTradeRole.TRADE_ROLE_FOUNDER, **settle_trade)


        # create settle request message
        message = SettleMessage.create_message_header(sender, receiver, SettleMessage._message_name,
                                                      channel_name, asset_type, nonce)
        message_body = {
            "Commitment": commitment,
            "SenderBalance": sender_balance,
            "ReceiverBalance": receiver_balance
        }
        message.update({'MessageBody': message_body})

        Message.send(message)

        return


class SettleResponseMessage(SettleBase):
    """
    {
        "MessageType":"SettleSign",
        "Sender": "0x9090909090909090909090909@127.0.0.1:20553",
        "Receiver":"0x101010101001001010100101@127.0.0.1:20552",
        "TxNonce": -1,   # int type
        "ChannelName":"902ae9090232048575",
        "AssetType": "TNC",
        "MessageBody": {
                "Commitment":"",
            }
        "Status": RESPONSE_OK
    }
    """
    _message_name = 'SettleSign'

    def handle_message(self):
        self.handle()

    def handle(self):
        super(SettleResponseMessage, self).handle()

        # check response status
        if not self.check_response_status(self.status):
            return

        try:
            # common check arguments
            self.verify()
            self.check_nonce(self.nonce)
            settle_trade = Channel.query_trade(self.channel_name, self.nonce)
            self.check_signature(
                self.wallet, self.sender_address,
                type_list=self._sign_type_list,
                value_list=[self.channel_name, self.nonce, self.receiver_address, int(settle_trade.balance),
                            self.sender_address, int(settle_trade.peer_balance)],
                signature=self.commitment
            )

            # update the trade
            Channel.update_trade(self.channel_name, SettleResponseMessage._SETTLE_NONCE, peer_commitment=self.commitment)
        except GoTo as error:
            LOG.exception(error)
        except Exception as error:
            LOG.exception('Handle Settle Response error. Exception: {}'.format(error))
        else:
            # register the event to quick close channel
            self.register_quick_close_event()

            return

    @staticmethod
    def create(wallet, channel_name, asset_type, nonce, sender, sender_balance, receiver, receiver_balance,
               peer_commitment, comments=None):
        """

        :param wallet:
        :param channel_name:
        :param asset_type:
        :param sender:
        :param receiver:
        :param sender_balance:
        :param receiver_balance:
        :param peer_commitment:
        :param status:
        :return:
        """
        sender_address, _, _ = uri_parser(sender)
        receiver_address, _, _ = uri_parser(receiver)
        asset_type = asset_type.upper()

        # sign the contents
        commitment = SettleResponseMessage.sign_content(
            wallet, SettleResponseMessage._sign_type_list,
            [channel_name, nonce, sender_address, int(sender_balance), receiver_address, int(receiver_balance)]
        )

        # finally, add the transaction information to database
        settle_trade = Channel.settle_trade(
            type = EnumTradeType.TRADE_TYPE_QIUCK_SETTLE, role=EnumTradeRole.TRADE_ROLE_PARTNER,
            asset_type=asset_type, balance=receiver_balance, peer_balance=sender_balance,
            commitment=commitment, peer_commitment=peer_commitment)
        SettleResponseMessage.add_or_update_quick_settle_trade(channel_name, EnumTradeRole.TRADE_ROLE_PARTNER, **settle_trade)

        message = SettleResponseMessage.create_message_header(receiver, sender, SettleResponseMessage._message_name,
                                                              channel_name, asset_type, nonce)

        message.update({"MessageBody": {"Commitment": commitment}})

        if not comments:
            message.update({'Comments': comments})

        # send response OK message
        message.update({'Status': EnumResponseStatus.RESPONSE_OK.name})
        Message.send(message)
