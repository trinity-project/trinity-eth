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
from common.exceptions import GoTo, TrinityException
from model.channel_model import EnumChannelState
from wallet.channel import Channel
from wallet.channel import EnumTradeType, EnumTradeRole, EnumTradeState
from wallet.event.channel_event import ChannelDepositEvent
from wallet.event.event import EnumEventAction, event_machine
from wallet.utils import get_magic, DepositAuth
from model.statistics_model import APIStatistics


class FounderBase(Message):
    """
    Descriptions: for creating channels
    """
    _sign_type_list = ['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256']

    def __init__(self, message, wallet):
        super(FounderBase, self).__init__(message)

        self.founder_deposit = self.message_body.get("FounderDeposit")
        self.partner_deposit = self.message_body.get("PartnerDeposit")
        self.commitment = self.message_body.get('Commitment')

        self.wallet = wallet

    @classmethod
    def check_nonce(cls, nonce, **kwargs):
        """

        :param nonce:
        :param kwargs:
        :return:
        """
        if FounderBase._FOUNDER_NONCE != int(nonce):
            raise GoTo(EnumResponseStatus.RESPONSE_FOUNDER_WITH_ILLEGAL_NONCE,
                       'Founder with invalid nonce<{}>. Must be one'.format(nonce))

        return True

    @classmethod
    def check_deposit(cls, founder_deposit:int, partner_deposit:int):
        if not (0 <= partner_deposit <= founder_deposit and 0 < founder_deposit):
            raise  GoTo(EnumResponseStatus.RESPONSE_FOUNDER_DEPOSIT_LESS_THAN_PARTNER,
                        'Founder deposit<{}> should not be less than partner\'s deposit<{}>'. \
                        format(founder_deposit,partner_deposit))

        return True

    def register_deposit_event(self, is_founder=True):
        """

        :param is_founder:
        :return:
        """
        try:
            channel_event = ChannelDepositEvent(self.channel_name, self.wallet.address, is_founder)

            # get the transaction record of founder message
            founder_trade = Channel.query_trade(self.channel_name, FounderBase._FOUNDER_NONCE)

            # set some arguments by the role type
            self_address = self.receiver_address
            self_deposit = founder_trade.balance
            if is_founder:
                founder_address = self.receiver_address
                founder_deposit = founder_trade.balance
                founder_commitment = founder_trade.commitment
                partner_address = self.sender_address
                partner_deposit = founder_trade.peer_balance
                partner_commitment = founder_trade.peer_commitment
            else:
                founder_address = self.sender_address
                founder_deposit = founder_trade.peer_balance
                founder_commitment = founder_trade.peer_commitment
                partner_address = self.receiver_address
                partner_deposit = founder_trade.balance
                partner_commitment = founder_trade.commitment

            # register the preparation action for deposit event
            channel_event.register_args(EnumEventAction.EVENT_PREPARE, self_address, self_deposit,
                                        self.wallet._key.private_key_string)

            # add execution action for deposit event
            channel_event.register_args(
                EnumEventAction.EVENT_EXECUTE, self_address, self.channel_name, FounderBase._FOUNDER_NONCE,
                founder_address, founder_deposit,
                partner_address, partner_deposit,
                founder_commitment, partner_commitment,
                self.wallet._key.private_key_string
            )
            channel_event.register_args(EnumEventAction.EVENT_TERMINATE, asset_type=self.asset_type)
        except Exception as error:
            LOG.exception('Failed to register deposit event since {}'.format(error))
        else:
            # register and trigger event
            event_machine.register_event(self.channel_name, channel_event)
            event_machine.trigger_start_event(self.channel_name)

        return


class FounderMessage(FounderBase):
    """
    {
        "MessageType": "Founder",
        "Sender": founder,
        "Receiver": partner,
        "TxNonce": 0,
        "ChannelName": channel_name,
        "NetMagic": magic,
        "AssetType": asset_type.upper(),
        "MessageBody": {
            "FounderDeposit": founder_deposit,
            "PartnerDeposit": partner_deposit,
            "Commitment": commitment,
        }
    }
    """
    _message_name = 'Founder'

    def handle_message(self):
        self.handle()

    def handle(self):
        super(FounderMessage, self).handle()
        status = EnumResponseStatus.RESPONSE_OK

        try:
            # some checks and verification for founder message
            self.verify()
            self.check_nonce(self.nonce)
            self.check_signature(
                self.wallet, self.sender_address,
                type_list=self._sign_type_list,
                value_list=[self.channel_name, self.nonce, self.sender_address, int(self.founder_deposit),
                            self.receiver_address, int(self.partner_deposit)],
                signature=self.commitment
            )

            # send response
            FounderResponsesMessage.create(self.wallet, self.channel_name, self.asset_type,
                                           self.sender, self.founder_deposit,
                                           self.receiver, self.partner_deposit, self.commitment,)
        except TrinityException as error:
            LOG.error(error)
            status = error.reason
        except Exception as error:
            LOG.error('Error to handle FounderMessage. Exception: {}'.format(error))
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
            pass
        finally:
            if status != EnumResponseStatus.RESPONSE_OK:
                FounderResponsesMessage.send_error_response(self.sender, self.receiver, self.channel_name,
                                                            self.asset_type, self.nonce, status)
            else:
                # register the event and trigger the deposit event
                self.register_deposit_event(False)

        return

    @staticmethod
    def create(wallet, channel_name, asset_type, founder, founder_deposit, partner, partner_deposit=None,
               comments=None):
        """

        :param wallet:
        :param channel_name:
        :param asset_type:
        :param founder:
        :param founder_deposit:
        :param partner:
        :param partner_deposit:
        :param comments:
        :return:
        """
        founder_deposit = int(founder_deposit)
        if partner_deposit is None:
            partner_deposit = founder_deposit
        partner_deposit = int(partner_deposit)

        # check the deposit
        FounderMessage.check_deposit(founder_deposit, partner_deposit)

        # get addresses of peers
        nonce = FounderMessage._FOUNDER_NONCE
        founder_address, _, _ = uri_parser(founder)
        partner_address, _, _ = uri_parser(partner)

        # Sign this data to hash value
        commitment = FounderMessage.sign_content(
            wallet, FounderMessage._sign_type_list,
            [channel_name, nonce, founder_address, founder_deposit, partner_address, partner_deposit]
        )

        # add channel
        asset_type = asset_type.upper()
        deposit = {founder_address: {asset_type: str(founder_deposit)},
                   partner_address: {asset_type: str(partner_deposit)}}
        hlock = {founder_address: {asset_type: '0'},
                 partner_address: {asset_type: '0'}}
        Channel.add_channel(channel=channel_name, src_addr=founder, dest_addr=partner, state=EnumChannelState.INIT.name,
                            deposit=deposit, magic=get_magic(), hlock=hlock)

        APIStatistics.update_statistics(wallet.address, state=EnumChannelState.INIT.name)

        # record the transaction
        founder_trade = Channel.founder_trade(
            type=EnumTradeType.TRADE_TYPE_FOUNDER, role=EnumTradeRole.TRADE_ROLE_FOUNDER, asset_type=asset_type,
            balance=founder_deposit, peer_balance=partner_deposit, commitment=commitment)
        Channel.add_trade(channel_name, nonce=nonce, **founder_trade)

        # create founder request message
        message = FounderMessage.create_message_header(founder, partner, FounderMessage._message_name,
                                                       channel_name, asset_type, nonce)
        message_body = {
            "FounderDeposit": str(founder_deposit),
            "PartnerDeposit": str(partner_deposit),
            "Commitment": commitment,
        }
        message.update({'MessageBody': message_body})

        # Add comments in the messages
        if comments:
            message.update({"Comments": comments})

        FounderMessage.send(message)
        return


class FounderResponsesMessage(FounderBase):
    """
    {
        "MessageType": "FounderSign",
        "Sender": partner,
        "Receiver": founder,
        "TxNonce": 0,
        "ChannelName": channel_name,
        "NetMagic": magic,
        "AssetType": asset_type,
        "MessageBody": {
                        "Commitment": commitment,
                    }
        "Status": status
    }
    """
    _message_name = 'FounderSign'

    def handle_message(self):
        self.handle()

    def handle(self):
        super(FounderResponsesMessage, self).handle()

        # check response status
        if not self.check_response_status(self.status):
            return

        try:
            # some checks and verification for founder message
            self.verify()
            self.check_nonce(self.nonce)
            founder_trade = Channel.query_trade(self.channel_name, self.nonce)
            self.check_signature(
                self.wallet, self.sender_address,
                type_list=self._sign_type_list,
                value_list=[self.channel_name, self.nonce, self.receiver_address, int(founder_trade.balance),
                            self.sender_address, int(founder_trade.peer_balance)],
                signature=self.commitment
            )

            # update the trade
            Channel.update_trade(self.channel_name, self.nonce, peer_commitment=self.commitment)
        except GoTo as error:
            LOG.error(error)
        except Exception as error:
            LOG.error('Exception occurred during creating channel<{}>. Exception: {}'.format(self.channel_name, error))
        else:
            self.register_deposit_event()

    @staticmethod
    def create(wallet, channel_name, asset_type, founder, founder_deposit, partner,  partner_deposit,
               founder_commitment, comments=None):
        """

        :param wallet:
        :param channel_name:
        :param asset_type:
        :param founder:
        :param founder_deposit:
        :param partner:
        :param partner_deposit:
        :param founder_commitment:
        :param comments:
        :return:
        """
        # check the deposit
        founder_deposit = int(founder_deposit)
        partner_deposit = int(partner_deposit)
        FounderResponsesMessage.check_deposit(founder_deposit, partner_deposit)

        nonce = FounderResponsesMessage._FOUNDER_NONCE
        # start to sign content
        founder_address, _, _ = uri_parser(founder)
        partner_address, _, _ = uri_parser(partner)
        # Sign this data to the
        commitment = FounderResponsesMessage.sign_content(
            wallet, FounderResponsesMessage._sign_type_list,
            [channel_name, nonce, founder_address, founder_deposit, partner_address, partner_deposit]
        )

        # start add channel
        deposit = {founder_address: {asset_type: str(founder_deposit)},
                   partner_address: {asset_type: str(partner_deposit)}}
        hlock = {founder_address: {asset_type: '0'},
                 partner_address: {asset_type: '0'}}
        Channel.add_channel(
            channel=channel_name, src_addr=founder, dest_addr=partner, state=EnumChannelState.INIT.name,
            deposit=deposit, hlock=hlock, magic=get_magic()
        )

        APIStatistics.update_statistics(wallet.address, state=EnumChannelState.INIT.name)

        # add trade to database
        founder_trade = Channel.founder_trade(
            type=EnumTradeType.TRADE_TYPE_FOUNDER, role=EnumTradeRole.TRADE_ROLE_PARTNER,
            asset_type=asset_type, balance=partner_deposit, peer_balance=founder_deposit,
            commitment=commitment, peer_commitment=founder_commitment, state=EnumTradeState.confirming
        )
        Channel.add_trade(channel_name, nonce=nonce, **founder_trade)

        # create messages
        asset_type = asset_type.upper()
        message = FounderResponsesMessage.create_message_header(partner, founder, FounderResponsesMessage._message_name,
                                                                channel_name, asset_type, nonce)
        message_body = {"Commitment": commitment}
        message.update( {"MessageBody": message_body})

        # Add comments in the messages
        if comments:
            message.update({"Comments": comments})

        # fill message status
        message.update({'Status': EnumResponseStatus.RESPONSE_OK.name})
        # send message to peer
        FounderResponsesMessage.send(message)

        return
