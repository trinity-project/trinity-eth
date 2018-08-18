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
from model.channel_model import EnumChannelState
from wallet.channel import Channel
from wallet.channel import EnumTradeType, EnumTradeRole, EnumTradeState
from wallet.event.contract_event import contract_event_api
from wallet.event.channel_event import ChannelQuickSettleEvent
from wallet.event.event import EnumEventAction, event_machine


class SettleMessage(Message):
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

    def __init__(self, message, wallet):
        super(SettleMessage, self).__init__(message)

        self.channel = Channel(self.channel_name)

        self.commitment = self.message_body.get('Commitment')
        self.sender_balance = self.message_body.get('SenderBalance')
        self.receiver_balance = self.message_body.get("ReceiverBalance")

        self.wallet = wallet

    def handle_message(self):
        self.handle()

    def handle(self):
        super(SettleMessage, self).handle()
        verified, status = self.verify()

        try:
            if not verified:
                raise GoTo('Channel<{}> is not found or not in OPENED state'.format(self.channel_name))

            balance = self.channel.balance
            sender_balance = balance.get(self.sender_address, {}).get(self.asset_type)
            receiver_balance = balance.get(self.receiver_address, {}).get(self.asset_type)

            negotiated, nonce = SettleMessage.negotiate_nonce(self.channel_name, self.nonce, self.sender_address,
                                                              self.sender_balance, self.receiver_address,
                                                              self.receiver_balance)
            if not negotiated:
                status = EnumResponseStatus.RESPONSE_TRADE_INCOMPATIBLE_NONCE
                raise GoTo('Incompatible nonce between peers.')

            # To create settle response message
            SettleResponseMessage.create(self.wallet, self.channel_name, nonce,
                                         self.asset_type, self.sender, self.receiver,
                                         float(sender_balance), float(receiver_balance), self.commitment)

        except GoTo as error:
            LOG.error(error)
            SettleResponseMessage.send_error_response(self.sender, self.receiver, self.channel_name, self.asset_type,
                                                      self.nonce, status)
        except Exception as error:
            LOG.error('Failed to handle FounderMessage. Exception: {}'.format(error))
            SettleResponseMessage.send_error_response(self.sender, self.receiver, self.channel_name, self.asset_type,
                                                      self.nonce, status)
        else:
            # trigger channel event
            self.channel.update_channel(self.channel_name, state=EnumChannelState.SETTLING.name)

            # TODO: monitor event to set channel closed state
            channel_event = ChannelQuickSettleEvent(self.channel_name, False)
            channel_event.register_args(EnumEventAction.EVENT_EXECUTE)
            channel_event.register_args(EnumEventAction.EVENT_TERMINATE, state=EnumChannelState.CLOSED.name,
                                        asset_type=self.asset_type)
            event_machine.register_event(self.channel_name, channel_event)
            event_machine.trigger_start_event(self.channel_name)

    @staticmethod
    def create(wallet, channel_name, sender, receiver, asset_type):
        """

        :param channel_name:
        :param wallet:
        :param sender:
        :param receiver:
        :param asset_type:
        :return:
        """
        # assert wallet.url == sender, 'Wallet url<{}> is not equal to founder<{}>'.format(wallet.url, sender)
        if wallet.url != sender:
            receiver = sender
            sender = wallet.url

        try:
            channel = Channel(channel_name)
            nonce = SettleMessage._SETTLE_NONCE
            asset_type = asset_type.upper()
            message = SettleMessage.create_message_header(sender, receiver, SettleMessage._message_name,
                                                          channel_name, asset_type, nonce)
            message = message.message_header

            sender_address, _, _, = uri_parser(sender)
            receiver_address, _, _, = uri_parser(receiver)

            balance = channel.balance
            sender_balance = balance.get(sender_address, {}).get(asset_type)
            receiver_balance = balance.get(receiver_address, {}).get(asset_type)

            commitment = contract_event_api.sign_content(
                typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                valueList=[channel_name, nonce, sender_address, sender_balance, receiver_address, receiver_balance],
                privtKey = wallet._key.private_key_string)

            message_body = {
                "Commitment": commitment,
                "SenderBalance": sender_balance,
                "ReceiverBalance": receiver_balance
            }

            message.update({'MessageBody': message_body})

            # update channel
            channel.update_channel(channel_name, state=EnumChannelState.SETTLING.name)

            # add trade to database
            settle_trade = Channel.founder_or_rsmc_trade(
                role=EnumTradeRole.TRADE_ROLE_FOUNDER, asset_type=asset_type, payment=0, balance=sender_balance,
                peer_balance=receiver_balance, commitment=commitment, state=EnumTradeState.confirming
            )
            Channel.add_trade(channel_name, nonce=nonce, settle=settle_trade)

            # register channel event
            channel_event = ChannelQuickSettleEvent(channel_name)
            event_machine.register_event(channel_name, channel_event)

            Message.send(message)
        except Exception as error:
            LOG.error('Failed to create Settle message. Exception: {}'.format(error))

    def verify(self):
        if not Channel(self.channel_name).channel_set:
            return False, EnumResponseStatus.RESPONSE_CHANNEL_NOT_FOUND

        return True, EnumResponseStatus.RESPONSE_OK


class SettleResponseMessage(Message):
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

    def __init__(self, message, wallet):
        super(SettleResponseMessage, self).__init__(message)

        self.channel = Channel(self.channel_name)
        self.peer_commitment = self.message_body.get('Commitment')

        self.wallet = wallet

    def handle_message(self):
        self.handle()

    def handle(self):
        super(SettleResponseMessage, self).handle()

        trade_state = EnumTradeState.confirmed
        try:
            verified, status = self.verify()
            if not verified:
                raise GoTo('Verify settle response message error: {}'.format(status))

            SettleResponseMessage.update_trade_after_negotiated(self.channel_name, self.nonce)

            settle_trade = self.channel.query_trade(self.channel_name, nonce=str(self.nonce))[0].settle
        except GoTo as error:
            trade_state = EnumTradeState.failed
            LOG.error(error)
        except Exception as error:
            trade_state = EnumTradeState.failed
            LOG.error('Transaction with none<0xFFFFFFFF> not found. Error: {}'.format(error))
        else:
            # call web3 interface to trigger transaction to on-chain
            # TODO: register monitor event to set channel closed
            channel_event = event_machine.get_registered_event(self.channel_name)
            if channel_event:
                channel_event.register_args(
                    EnumEventAction.EVENT_EXECUTE,
                    self.receiver_address, self.channel_name, self.nonce,
                    self.receiver_address, settle_trade.get('balance'),
                    self.sender_address, settle_trade.get('peer_balance'),
                    settle_trade.get('commitment'), self.peer_commitment,
                    self.wallet._key.private_key_string
                )

                channel_event.register_args(EnumEventAction.EVENT_TERMINATE, state=EnumChannelState.CLOSED.name,
                                            asset_type=self.asset_type)
                event_machine.trigger_start_event(self.channel_name)
        finally:
            # update transaction
            settle_trade.update({'state': trade_state.name, 'peer_commitment': self.peer_commitment})
            self.channel.update_trade(self.channel_name, self.nonce, settle=settle_trade)

    def verify(self):
        if self.status not in EnumResponseStatus.RESPONSE_OK.__dict__.values():
            return False, self.status

        return True, None

    @staticmethod
    def create(wallet, channel_name, nonce, asset_type, sender, receiver, sender_balance, receiver_balance, commitment):
        """

        :param wallet:
        :param channel_name:
        :param asset_type:
        :param sender:
        :param receiver:
        :param sender_balance:
        :param receiver_balance:
        :param commitment:
        :param status:
        :return:
        """
        status = EnumResponseStatus.RESPONSE_OK
        sender_addr = sender.split("@")[0].strip()
        receiver_addr = receiver.split("@")[0].strip()
        trade_state = EnumTradeState.confirmed
        asset_type = asset_type.upper()

        message = SettleResponseMessage.create_message_header(receiver, sender, SettleResponseMessage._message_name,
                                                              channel_name, asset_type, nonce)
        message = message.message_header
        self_commitment = None

        try:
            self_commitment = contract_event_api.sign_content(
                typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                valueList=[channel_name, nonce, sender_addr, sender_balance, receiver_addr, receiver_balance],
                privtKey = wallet._key.private_key_string)
            message.update({"MessageBody": {"Commitment": self_commitment}})
        except Exception as error:
            LOG.error('Error occurred during create Settle response. Error: {}'.format(error))
            status = EnumResponseStatus.RESPONSE_FAIL

        if EnumResponseStatus.RESPONSE_OK != status:
            trade_state = EnumTradeState.confirming

        # add trade to database
        settle_trade = Channel.founder_or_rsmc_trade(
            role=EnumTradeRole.TRADE_ROLE_PARTNER, asset_type=asset_type, payment=0, balance=receiver_balance,
            peer_balance=sender_balance, commitment=self_commitment, peer_commitment=commitment,
            state=trade_state
        )
        Channel.update_trade(channel_name, nonce=nonce, settle=settle_trade)

        message.update({'Status': status.name})
        Message.send(message)

        # TODO: register monitor event to set channel closed
        pass
