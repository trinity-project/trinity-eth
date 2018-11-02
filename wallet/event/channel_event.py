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
from .event import EventBase, EnumEventType, EnumEventAction
from wallet.channel import Channel, sync_channel_info_to_gateway, EnumTradeState
from model.base_enum import EnumChannelState
from wallet.event.chain_event import event_monitor_settle, \
    event_monitor_close_channel, \
    event_test_state, \
    event_monitor_withdraw, \
    event_monitor_withdraw_update, \
    event_monitor_withdraw_settle
from common.log import LOG
from common.console import console_log
from common.number import TrinityNumber
from model.statistics_model import APIStatistics


class ChannelEventBase(EventBase):
    """

    """
    def __init__(self, channel_name, event_type, wallet_address, is_event_founder=True):
        super(ChannelEventBase, self).__init__(channel_name, event_type, is_event_founder)

        self.channel_name = channel_name
        self.channel = Channel(channel_name)
        self.wallet_address = wallet_address


class ChannelTestEvent(ChannelEventBase):
    def __init__(self):
        super(ChannelTestEvent, self).__init__('test_event', EnumEventType.EVENT_TYPE_TEST_STATE, wallet_address, True)
        self.event_stage_iterator = iter([EnumEventAction.EVENT_EXECUTE, EnumEventAction.EVENT_COMPLETE])

    def execute(self, *args, **kwargs):
        super(ChannelTestEvent, self).execute(*args, **kwargs)
        event_test_state()
        self.next_stage()


class ChannelDepositEvent(ChannelEventBase):
    """
    Descriptions: Creating Channel event.
    """
    def __init__(self, channel_name, wallet_address, is_event_founder=True):
        super(ChannelDepositEvent, self).__init__(channel_name, EnumEventType.EVENT_TYPE_DEPOSIT, wallet_address, is_event_founder)

        self.deposit = 0.0
        self.partner_deposit = 0.0

        self.nonce = 1  # thins must be equal to _founder_NONCE
        self.approved_tx_id = None
        self.deposit_tx_id = None

        pass

    def prepare(self, block_height, address='', deposit=0.0, key=''):
        super(ChannelDepositEvent, self).prepare(block_height)

        # if this transaction id is approved, it means successful by eth block chain
        if self.approved_tx_id:
            checked = self.check_transaction_success(self.approved_tx_id)
            if checked:
                # go to next stage
                self.next_stage()
                LOG.debug('Approved asset by address<{}:{}>'.format(address, deposit))
                Channel.update_channel(self.channel_name, state=EnumChannelState.OPENING.name)
                LOG.info('Start to create channel<{}>. State: OPENING.'.format(self.channel_name))
                console_log.info('Channel<{}> is opening'.format(self.channel_name))
                return True
            elif checked is False:
                return False
            else:
                # new transaction is pushed to chain
                self.approved_tx_id = None

        # make transaction to chain
        result = self.contract_event_api.approve(address, int(deposit), key, gwei_coef=self.gwei_coef)
        if result:
            self.approved_tx_id = '0x'+result.strip()

        return False

    def execute(self, block_height, address='', channel_id='', nonce='',
                founder='', deposit=0, partner='', partner_deposit=0,
                founder_sign='', partner_sign='', private_key=''):
        super(ChannelDepositEvent, self).execute(block_height)

        # update the founder and partner deposit
        self.deposit = int(deposit)
        self.partner_deposit = int(partner_deposit)
        
        # execute stage of channel event
        try:
            # if this wallet is not the event founder, go to next step directly.
            if not self.is_event_founder:
                self.next_stage()
                return True

            # below codes is just executed by the founder
            # check whether deposit is success or not
            if self.deposit_tx_id:
                checked = self.check_transaction_success(self.deposit_tx_id)
                if checked:
                    # go to next stage
                    self.next_stage()
                    return True
                elif checked is False:
                    return False
                else:
                    # new transaction is pushed to chain
                    self.deposit_tx_id = None

            # get approved asset of both partners
            peer_approved_deposit = self.contract_event_api.get_approved_asset(partner)
            approved_deposit = self.contract_event_api.get_approved_asset(founder)
            LOG.debug('Approved asset in wallet<{}>: founder<{}:{}>, partner<{}:{}>' \
                      .format(address, founder, approved_deposit, partner, peer_approved_deposit))
            # check approved asset of both side for event founder.
            if not (approved_deposit >= self.deposit and peer_approved_deposit >= self.partner_deposit):
                return False

            # Trigger deposit action if is_event_founder is True
            result = self.deposit_tx_id = self.contract_event_api.approve_deposit(
                    address, channel_id, nonce, founder, deposit, partner, partner_deposit,
                    founder_sign, partner_sign, private_key, gwei_coef=self.gwei_coef)
            if result:
                self.deposit_tx_id = '0x'+result.strip()

        except Exception as error:
            LOG.warning('Failed to approve deposit of Channel<{}>. Exception: {}'.format(self.channel_name, error))

        return False

    def terminate(self, block_height, *args, asset_type='TNC'):
        super(ChannelDepositEvent, self).terminate(block_height, *args)

        # check the deposit of the contract address
        total_deposit = self.contract_event_api.get_channel_total_balance(self.channel_name)
        if total_deposit >= self.deposit + self.partner_deposit > 0:
            Channel.update_channel(self.channel_name, state=EnumChannelState.OPENED.name)
            Channel.update_trade(self.channel_name, self.nonce, state=EnumTradeState.confirmed.name)
            APIStatistics.update_statistics(self.wallet_address, state=EnumChannelState.OPENED.name)
            sync_channel_info_to_gateway(self.channel_name, 'AddChannel', asset_type)
            console_log.info('Channel {} state is {}'.format(self.channel_name, EnumChannelState.OPENED.name))

            # to trigger monitor event for closing channel
            event_monitor_close_channel(self.channel_name)
            event_monitor_settle(self.channel_name)

            # to trigger monitor event for unlocking htlc locked payment
            event_monitor_withdraw(self.channel_name)
            event_monitor_withdraw_update(self.channel_name)
            event_monitor_withdraw_settle(self.channel_name)

            self.next_stage()

    def timeout_handler(self, block_height, *args, **kwargs):
        super(ChannelDepositEvent, self).timeout_handler(block_height, *args, **kwargs)

    def complete(self, block_height, *args, **kwargs):
        super(ChannelDepositEvent, self).complete(block_height, *args, **kwargs)

    def error_handler(self, block_height, *args, **kwargs):
        super(ChannelDepositEvent, self).error_handler(block_height, *args, **kwargs)


class ChannelQuickSettleEvent(ChannelEventBase):
    """
        Descriptions: Quick close channel event
    """
    def __init__(self, channel_name, wallet_address, is_event_founder=True):
        super(ChannelQuickSettleEvent, self).__init__(channel_name, EnumEventType.EVENT_TYPE_QUICK_SETTLE,wallet_address,
                                                      is_event_founder)

        # different event stage
        self.event_stage_list = [EnumEventAction.EVENT_PREPARE, EnumEventAction.EVENT_EXECUTE,
                                 EnumEventAction.EVENT_TERMINATE, EnumEventAction.EVENT_COMPLETE]
        self.event_stage_iterator = iter(self.event_stage_list)

        # record the tx id for quick settle
        self.settle_tx_id = None

    def prepare(self, block_height, *args, **kwargs):
        super(ChannelQuickSettleEvent, self).prepare(block_height, *args, **kwargs)

        # update the channel OPENING State after trigger the deposit event, wait for OPENED
        if self.retry is False:
            Channel.update_channel(self.channel_name, state=EnumChannelState.CLOSING.name)
            LOG.info('Start to quick-close channel<{}>. State: CLOSING.'.format(self.channel_name))
            console_log.info('Channel<{}> is closing'.format(self.channel_name))

        # go to next stage
        self.next_stage()

    def execute(self, block_height, invoker='', channel_id='', nonce='', founder='', founder_balance=0,
                partner='', partner_balance=0, founder_signature='', partner_signature='', invoker_key=''):
        super(ChannelQuickSettleEvent, self).execute(block_height)

        # goto next stage directly for event partener
        if not self.is_event_founder:
            self.next_stage()
            return True

        # only executed by the event founder
        # to check settle ID firslty
        if self.settle_tx_id:
            checked = self.check_transaction_success(self.settle_tx_id)
            if checked:
                # go to next stage
                self.next_stage()
                return True
            elif checked is False:
                return False
            else:
                # new transaction is pushed to chain
                self.settle_tx_id = None

        result = self.contract_event_api.quick_settle(
            invoker, channel_id, nonce, founder, founder_balance, partner, partner_balance,
            founder_signature, partner_signature, invoker_key, gwei_coef=self.gwei_coef)

        # set the tx id
        if result:
            self.settle_tx_id = '0x' + result

        return False

    def terminate(self, block_height, *args, asset_type='TNC'):
        super(ChannelQuickSettleEvent, self).terminate(block_height)

        # to check the total deposit of the channel
        total_deposit = self.contract_event_api.get_channel_total_balance(self.channel_name)
        if 0 >= total_deposit:
            Channel.update_channel(self.channel_name, state=EnumChannelState.CLOSED.name)
            APIStatistics.update_statistics(self.wallet_address, state=EnumChannelState.CLOSED.name)
            sync_channel_info_to_gateway(self.channel_name, 'DeleteChannel', asset_type)
            console_log.info('Channel {} state is {}'.format(self.channel_name, EnumChannelState.CLOSED.name))
            self.next_stage()
