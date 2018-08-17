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
from wallet.event.channel_event import ChannelDepositEvent
from wallet.event.event import EnumEventAction, event_machine


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

        status = EnumResponseStatus.RESPONSE_OK
        if not verified:
            LOG.error('Verified error: {}'.format(error))
            status = EnumResponseStatus.RESPONSE_FAIL
        else:
            # TODO: currently, here wait for result with 60 seconds.
            # TODO: need trigger later by async mode
            # FounderMessage.sync_timer(FounderMessage.get_approved_asset, '', 60, self.receiver.strip().split('@')[0])

            # add channel to dbs
            deposit = {self.sender_address: {self.asset_type: self.founder_deposit},
                       self.receiver_address: {self.asset_type: self.partner_deposit}}
            Channel.add_channel(channel = self.channel_name, src_addr = self.sender,
                                dest_addr = self.receiver,
                                state = EnumChannelState.INIT.name,
                                deposit = deposit,
                                balance = deposit)

        # send response
        FounderResponsesMessage.create(self.channel_name, self.asset_type,
                                       self.sender, self.founder_deposit, self.commitment,
                                       self.receiver, self.partner_deposit,
                                       self.network_magic, status, self.wallet)

    @staticmethod
    def create(channel_name, founder, partner, asset_type, founder_deposit, partner_deposit, wallet=None, comments=None):
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
        assert 0 < float(founder_deposit), 'Deposit Must be lager than zero.'

        if partner_deposit:
            assert float(partner_deposit) <= float(founder_deposit), 'Deposit Must be lager than zero.'
            partner_deposit = float(partner_deposit)
        else:
            partner_deposit = founder_deposit

        founder_address, _, _ = uri_parser(founder)
        partner_address, _, _ = uri_parser(partner)

        # Sign this data to the
        commitment = contract_event_api.sign_content(
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

        # authorized the deposit to the contract
        try:
            # contract_event_api.approve(founder_address, founder_deposit, wallet._key.private_key_string)
            pass
        except Exception as error:
            LOG.error('Error occurred during approve asset to contract. Exception: {}'.format(error))
            print(error)
        else:
            # add channel
            deposit = {founder_address: {asset_type.upper(): founder_deposit},
                       partner_address: {asset_type.upper(): partner_deposit}}
            Channel.add_channel(channel=channel_name, src_addr=founder, dest_addr=partner,
                                state=EnumChannelState.INIT.name, deposit=deposit, balance=deposit)

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

    def verify(self):
        verified, error = super(FounderMessage, self).verify()
        if not verified:
            return verified, error

        if 0 != int(self.nonce):
            return False, 'Invalid nonce<{}>. Must be zero'.format(self.nonce)

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
        # if 0 != self.nonce:
        #     return False, 'Invalid nonce<{}>. Must be zero'.format(self.nonce)
        #
        # if self.sender == self.receiver:
        #     return False, "Not Support Sender is Receiver"
        #
        # if self.receiver != self.wallet.url:
        #     return False, "The Endpoint is Not Me"
        return True, None

    @staticmethod
    def create(channel_name, asset_type, founder, founder_deposit, founder_commitment, partner,  partner_deposit,
               magic, response_status, wallet=None, comments=None):
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
        assert founder.__contains__('@'), 'Invalid founder URL format.'
        assert partner.__contains__('@'), 'Invalid founder URL format.'

        asset_type = asset_type.upper()
        commitment = None
        message = {
            "MessageType": "FounderSign",
            "Sender": partner,
            "Receiver": founder,
            "TxNonce": 0,
            "ChannelName": channel_name,
            "NetMagic": magic
        }
        trade_state = EnumTradeState.confirming

        if response_status == EnumResponseStatus.RESPONSE_OK:
            try:
                founder_deposit = float(founder_deposit)
                partner_deposit = float(partner_deposit)

                if not (0 < partner_deposit <= founder_deposit):
                    response_status = EnumResponseStatus.RESPONSE_FOUNDER_DEPOSIT_LESS_THAN_PARTNER
                    LOG.error('Invalid deposit. founder<{}> MUST be not less than partner<{}>.'.format(founder_deposit,
                                                                                                       partner_deposit))
                    trade_state = EnumTradeState.stuck_by_error_deposit
                    raise Exception(response_status.name)

                founder_addr = founder.strip().split('@')[0]
                partner_addr = partner.strip().split('@')[0]

                # Sign this data to the
                commitment = contract_event_api.sign_content(
                    typeList=['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256'],
                    valueList=[channel_name, 0, founder_addr, founder_deposit, partner_addr, partner_deposit],
                    privtKey = wallet._key.private_key_string )

                message.update({
                    "MessageBody": {
                        "Commitment": commitment,
                        "AssetType": asset_type
                    }
                })

                channel_event = ChannelDepositEvent(channel_name, False)
                channel_event.register_args(EnumEventAction.EVENT_PREPARE,
                                            partner_addr, partner_deposit,
                                            wallet._key.private_key_string)

                event_machine.register_event(channel_name, channel_event)
                channel_event.register_args(
                    EnumEventAction.EVENT_EXECUTE,
                    partner_addr, channel_name, 0,
                    founder_addr, founder_deposit,
                    partner_addr, partner_deposit,
                    founder_deposit, commitment,
                    wallet._key.private_key_string)

                channel_event.register_args(EnumEventAction.EVENT_TERMINATE, state=EnumChannelState.OPENED.name,
                                            asset_type=asset_type)

                # after send the response message, to trigger execute the event machine
                event_machine.trigger_start_event(channel_name)

                # update channel state
                Channel.update_channel(channel_name, state=EnumChannelState.OPENING.name)
                LOG.info('Channel<{}> in opening state.'.format(channel_name))
            except Exception as error:
                if response_status == EnumResponseStatus.RESPONSE_OK:
                    response_status = EnumResponseStatus.RESPONSE_EXCEPTION_HAPPENED

                if EnumTradeState.confirmed == trade_state:
                    trade_state = EnumTradeState.failed

                LOG.error('Exception occurred. {}'.format(error))

        # fill message status
        message.update({'Status': response_status.name})

        if EnumResponseStatus.RESPONSE_OK == response_status:
            trade_state = EnumTradeState.confirmed
        else:
            trade_state = EnumTradeState.confirming

        # add trade to database
        founder_trade = Channel.founder_or_rsmc_trade(
            role=EnumTradeRole.TRADE_ROLE_PARTNER, asset_type=asset_type, payment=0, balance=partner_deposit,
            peer_balance=founder_deposit, commitment=commitment, peer_commitment=founder_commitment,
            state=trade_state
        )
        Channel.add_trade(channel_name, nonce=0, founder=founder_trade)

        # Add comments in the messages
        if comments:
            message.update({"Comments": comments})

        FounderResponsesMessage.send(message)
