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
from common.console import console_log
from common.common import uri_parser
from common.exceptions import GoTo
from model.channel_model import EnumChannelState
from wallet.channel import Channel
from wallet.channel import EnumTradeType, EnumTradeRole, EnumTradeState
from wallet.event.channel_event import ChannelDepositEvent
from wallet.event.event import EnumEventAction, event_machine
from wallet.utils import get_magic


class FounderMessage(Message):
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

    def __init__(self, message, wallet=None):
        super(FounderMessage, self).__init__(message)

        self.founder_deposit = self.message_body.get("FounderDeposit")
        self.partner_deposit = self.message_body.get("PartnerDeposit")
        self.commitment = self.message_body.get('Commitment')

        self.wallet = wallet

    def handle_message(self):
        self.handle()

    def handle(self):
        super().handle()
        verified, error = self.verify()
        status = EnumResponseStatus.RESPONSE_FAIL

        try:
            # check verified result
            if not verified:
                status = EnumResponseStatus.RESPONSE_TRADE_VERIFIED_ERROR
                raise GoTo('Founder message verified error: {}'.format(error))

            # ToDo: verify the signarture in future
            ##

            # send response
            FounderResponsesMessage.create(self.channel_name, self.asset_type,
                                           self.sender, self.founder_deposit, self.commitment,
                                           self.receiver, self.partner_deposit, self.wallet)
            status = EnumResponseStatus.RESPONSE_OK
        except GoTo as error:
            LOG.error(error)
        except Exception as error:
            LOG.error('Error to handle FounderMessage. Exception: {}'.format(error))
            status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED
            pass

        if status != EnumResponseStatus.RESPONSE_OK:
            FounderResponsesMessage.send_error_response(self.sender, self.receiver, self.channel_name,
                                                        self.asset_type, self.nonce, status)

        return

    @staticmethod
    def create(channel_name, founder, partner, asset_type, founder_deposit, partner_deposit=None, wallet=None, comments=None):
        """

        :param channel_name:
        :param founder:
        :param partner:
        :param asset_type:
        :param founder_deposit:
        :param receiver_deposit:
        :param wallet:
        :param comments:
        :return:
        """
        # nonce of founder must be zero
        nonce = FounderMessage._FOUNDER_NONCE
        message = FounderMessage.create_message_header(founder, partner, FounderMessage._message_name,
                                                       channel_name, asset_type, nonce)
        message = message.message_header

        founder_deposit = float(founder_deposit)
        if partner_deposit:
            partner_deposit = founder_deposit

        # check the deposit
        if not 0 <= partner_deposit <= founder_deposit:
            raise GoTo('Founder deposit<{}> should not be less than partner\'s deposit<{}>'.format(founder_deposit,
                                                                                                   partner_deposit))

        founder_address, _, _ = uri_parser(founder)
        partner_address, _, _ = uri_parser(partner)

        # Sign this data to the
        commitment = FounderMessage.sign_content(
            typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
            valueList=[channel_name, nonce, founder_address, founder_deposit, partner_address, partner_deposit],
            privtKey = wallet._key.private_key_string )

        message_body = {
            "FounderDeposit": founder_deposit,
            "PartnerDeposit": partner_deposit,
            "Commitment": commitment,
            "AssetType": asset_type.upper(),
        }
        message.update({'MessageBody': message_body})

        # Add comments in the messages
        if comments:
            message.update({"Comments": comments})

        # add channel
        deposit = {founder_address: {asset_type.upper(): founder_deposit},
                   partner_address: {asset_type.upper(): partner_deposit}}
        Channel.add_channel(channel=channel_name, src_addr=founder, dest_addr=partner,
                            state=EnumChannelState.INIT.name, deposit=deposit, balance=deposit, magic=get_magic())

        # TODO: currently, register event
        channel_event = ChannelDepositEvent(channel_name)
        channel_event.register_args(EnumEventAction.EVENT_PREPARE, founder_address, founder_deposit,
                                    wallet._key.private_key_string)

        event_machine.register_event(channel_name, channel_event)

        # add trade to database
        founder_trade = Channel.founder_or_rsmc_trade(
            role=EnumTradeRole.TRADE_ROLE_FOUNDER, asset_type=asset_type, payment=0, balance=founder_deposit,
            peer_balance=partner_deposit, commitment=commitment, state=EnumTradeState.confirming
        )
        Channel.add_trade(channel_name, nonce=nonce, founder=founder_trade)

        FounderMessage.send(message)
        return

    def verify(self):
        verified, error = super(FounderMessage, self).verify()
        if not verified:
            return verified, error

        if FounderMessage._FOUNDER_NONCE != int(self.nonce):
            return False, 'Invalid nonce<{}>. Must be one'.format(self.nonce)

        return True, None


class FounderResponsesMessage(Message):
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

    def __init__(self, message, wallet):
        super(FounderResponsesMessage, self).__init__(message)

        self.founder_deposit = self.message_body.get("FounderDeposit")
        self.partner_deposit = self.message_body.get("PartnerDeposit")
        self.commitment = self.message_body.get('Commitment')

        self.wallet = wallet

    def handle_message(self):
        self.handle()

    def handle(self):
        super(FounderResponsesMessage, self).handle()

        trade_state = EnumTradeState.confirmed
        try:

            if not (EnumResponseStatus.RESPONSE_OK.name == self.status):
                raise GoTo('Founder failed to create channels. Status<{}>'.format(self.status))

            verified, error = self.verify()
            if not verified:
                raise GoTo('Handle FounderSign failed: {}'.format(error))

            # get trade from transaction history
            founder_trade = Channel.query_trade(self.channel_name, self.nonce)[0]
            if not (founder_trade and founder_trade.founder):
                raise GoTo('Could find FOUNDER trade record for nonce<{}>.'.format(self.nonce))

            # to get channel event to update some actions and trigger it start
            channel_event = event_machine.get_registered_event(self.channel_name)
            if not channel_event:
                raise GoTo('Could not find channel event for creating channel<{}>'.format(self.channel_name))

            # add execute action for deposit event
            channel_event.register_args(
                EnumEventAction.EVENT_EXECUTE, self.receiver_address,
                self.channel_name, self.nonce, self.receiver_address, founder_trade.founder.get('balance'),
                self.sender_address, founder_trade.founder.get('peer_balance'),
                founder_trade.founder.get('commitment'), self.commitment,
                self.wallet._key.private_key_string
            )

            # ToDo: need monitor event to trigger confirmed transaction
            # change channel state to OPENING
            Channel.update_channel(self.channel_name, state=EnumChannelState.OPENING.name)
            LOG.info('Channel<{}> in opening state.'.format(self.channel_name))
            console_log.info('Channel<{}> is opening'.format(self.channel_name))

            channel_event.register_args(EnumEventAction.EVENT_TERMINATE, state=EnumChannelState.OPENED.name,
                                        asset_type=self.asset_type)
            event_machine.trigger_start_event(self.channel_name)
        except GoTo as error:
            trade_state = EnumTradeState.confirming
            LOG.error(error)
        except Exception as error:
            LOG.error('Exception occurred during creating channel<{}>. Exception: {}'.format(self.channel_name, error))
        finally:
            founder_trade_founder = founder_trade.founder
            founder_trade_founder.update({'state': trade_state.name, 'peer_commitment': self.commitment})
            # update transaction
            Channel.update_trade(self.channel_name, self.nonce, founder=founder_trade_founder)


    def verify(self):
        # verified, error = super(FounderResponsesMessage, self).verify()
        # if not verified:
        #     return verified, error
        #
        if FounderResponsesMessage._FOUNDER_NONCE != self.nonce:
            return False, 'Invalid nonce<{}>. Must be one'.format(self.nonce)
        #
        # if self.sender == self.receiver:
        #     return False, "Not Support Sender is Receiver"
        #
        # if self.receiver != self.wallet.url:
        #     return False, "The Endpoint is Not Me"
        return True, None

    @staticmethod
    def create(channel_name, asset_type, founder, founder_deposit, founder_commitment, partner,  partner_deposit,
               wallet=None, comments=None):
        """

        :param channel_name:
        :param asset_type:
        :param founder:
        :param founder_deposit:
        :param founder_commitment:
        :param partner:
        :param partner_deposit:
        :param magic:
        :param response_status:
        :param wallet:
        :param comments:
        :return:
        """
        # assert founder.__contains__('@'), 'Invalid founder URL format.'
        # assert partner.__contains__('@'), 'Invalid founder URL format.'
        asset_type = asset_type.upper()
        nonce = FounderResponsesMessage._FOUNDER_NONCE

        # create messages
        message = FounderResponsesMessage.create_message_header(partner, founder, FounderResponsesMessage._message_name,
                                                                channel_name, asset_type, nonce)
        message = message.message_header

        # check the deposit
        founder_deposit = float(founder_deposit)
        partner_deposit = float(partner_deposit)
        if not 0 <= partner_deposit <= founder_deposit:
            raise GoTo('Invalid deposit. founder<{}> should not be less than partner<{}>.'.format(founder_deposit,
                                                                                                  partner_deposit))

        # start to sign content
        founder_address, _, _ = uri_parser(founder)
        partner_address, _, _ = uri_parser(partner)
        # Sign this data to the
        commitment = FounderResponsesMessage.sign_content(
            typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
            valueList=[channel_name, nonce, founder_address, founder_deposit, partner_address, partner_deposit],
            privtKey = wallet._key.private_key_string )

        message.update(
            {
                "MessageBody": {
                    "Commitment": commitment,
                    "AssetType": asset_type
                }
            })

        # register channel event
        channel_event = ChannelDepositEvent(channel_name, False)
        channel_event.register_args(EnumEventAction.EVENT_PREPARE,
                                    partner_address, partner_deposit,
                                    wallet._key.private_key_string)

        event_machine.register_event(channel_name, channel_event)
        channel_event.register_args(
            EnumEventAction.EVENT_EXECUTE,
            partner_address, channel_name, nonce,
            founder_address, founder_deposit,
            partner_address, partner_deposit,
            founder_deposit, commitment,
            wallet._key.private_key_string)

        channel_event.register_args(EnumEventAction.EVENT_TERMINATE, state=EnumChannelState.OPENED.name,
                                    asset_type=asset_type)

        # start add channel
        deposit = {founder_address: {asset_type: founder_deposit},
                   partner_address: {asset_type: partner_deposit}}
        Channel.add_channel(
            channel=channel_name, src_addr=founder, dest_addr=partner, state=EnumChannelState.OPENING.name,
            deposit=deposit, balance=deposit, magic=get_magic()
        )
        LOG.info('Channel<{}> in opening state.'.format(channel_name))
        console_log.info('Channel<{}> is opening'.format(channel_name))

        # add trade to database
        founder_trade = Channel.founder_or_rsmc_trade(
            role=EnumTradeRole.TRADE_ROLE_PARTNER, asset_type=asset_type, payment=0, balance=partner_deposit,
            peer_balance=founder_deposit, commitment=commitment, peer_commitment=founder_commitment,
            state=EnumTradeState.confirmed
        )
        Channel.add_trade(channel_name, nonce=nonce, founder=founder_trade)

        # Add comments in the messages
        if comments:
            message.update({"Comments": comments})

        # fill message status
        message.update({'Status': EnumResponseStatus.RESPONSE_OK.name})
        FounderResponsesMessage.send(message)

        # Finally, to trigger execute the event machine
        event_machine.trigger_start_event(channel_name)

        return
