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
from wallet.channel import Channel, sync_channel_info_to_gateway
from blockchain.event import event_test_state
from common.log import LOG
from common.console import console_log


class ChannelEventBase(EventBase):
    """

    """
    def __init__(self, channel_name, event_type, is_event_founder=True):
        super(ChannelEventBase, self).__init__(channel_name, event_type, is_event_founder)

        self.channel_name = channel_name
        self.channel = Channel(channel_name)


class ChannelTestEvent(ChannelEventBase):
    def __init__(self):
        super(ChannelTestEvent, self).__init__('test_event', EnumEventType.EVENT_TYPE_TEST_STATE, True)
        self.event_stage_iterator = iter([EnumEventAction.EVENT_EXECUTE, EnumEventAction.EVENT_COMPLETE])

    def execute(self, *args, **kwargs):
        super(ChannelTestEvent, self).execute(*args, **kwargs)
        event_test_state()
        self.next_stage()


class ChannelDepositEvent(ChannelEventBase):
    def __init__(self, channel_name, is_event_founder=True):
        super(ChannelDepositEvent, self).__init__(channel_name, EnumEventType.EVENT_TYPE_DEPOSIT, is_event_founder)

        self.deposit = 0.0
        self.partner_deposit = 0.0

        pass

    def prepare(self, block_height, address='', deposit=0.0, key=''):
        super(ChannelDepositEvent, self).prepare(block_height)

        result = self.contract_event_api.approve(address, deposit, key, gwei_coef=self.gwei_coef)
        if result:
            self.next_stage()
            return True

        return False

    def execute(self, block_height, address='', channel_id='', nonce='',
                founder='', deposit=0, partner='', partner_deposit=0,
                founder_sign='', partner_sign='', private_key=''):
        super(ChannelDepositEvent, self).execute(block_height)

        # execute stage of channel event
        try:

            approved_deposit = self.contract_event_api.get_approved_asset(founder)
            peer_approved_deposit = self.contract_event_api.get_approved_asset(partner)

            if approved_deposit >= float(deposit) and peer_approved_deposit >= float(partner_deposit):
                LOG.debug('Approved asset: self<{}:{}>, peer<{}:{}>'.format(address, approved_deposit,
                                                                            partner, peer_approved_deposit))

                # update the founder and partner deposit
                self.deposit = deposit
                self.partner_deposit = partner_deposit
            else:
                return False

            if self.is_event_founder:
                self.contract_event_api.approve_deposit(
                    address, channel_id, nonce, founder, deposit, partner, partner_deposit,
                    founder_sign, partner_sign, private_key, gwei_coef=self.gwei_coef)
        except Exception as error:
            LOG.warning('Failed to approve deposit of Channel<{}>. Exception: {}'.format(self.channel_name, error))
        else:
            self.next_stage()

        return False

    def terminate(self, block_height, state='', asset_type='TNC'):
        super(ChannelDepositEvent, self).terminate(block_height)

        # check the deposit of the contract address
        total_deposit = self.contract_event_api.get_channel_total_balance(self.channel_name)
        if total_deposit >= self.deposit + self.partner_deposit:
            Channel.update_channel(self.channel_name, state=state)
            sync_channel_info_to_gateway(self.channel_name, 'AddChannel', asset_type)
            console_log.info('Channel {} state is {}'.format(self.channel_name, state))
            self.next_stage()

    def timeout_handler(self, block_height, *args, **kwargs):
        super(ChannelDepositEvent, self).timeout_handler(block_height, *args, **kwargs)

    def complete(self, block_height, *args, **kwargs):
        super(ChannelDepositEvent, self).complete(block_height, *args, **kwargs)

    def error_handler(self, block_height, *args, **kwargs):
        super(ChannelDepositEvent, self).error_handler(block_height, *args, **kwargs)


class ChannelQuickSettleEvent(ChannelEventBase):
    def __init__(self, channel_name, is_event_founder=True):
        super(ChannelQuickSettleEvent, self).__init__(channel_name, EnumEventType.EVENT_TYPE_QUICK_SETTLE,
                                                      is_event_founder)

        # different event stage
        self.event_stage_list = [EnumEventAction.EVENT_PREPARE, EnumEventAction.EVENT_EXECUTE,
                                 EnumEventAction.EVENT_TERMINATE, EnumEventAction.EVENT_COMPLETE]
        self.event_stage_iterator = iter(self.event_stage_list)

    def prepare(self, block_height, *args, **kwargs):
        super(ChannelQuickSettleEvent, self).prepare(block_height, *args, **kwargs)
        self.next_stage()

    def execute(self, block_height, invoker='', channel_id='', nonce='', founder='', founder_balance=0.0,
                partner='', partner_balance=0.0, founder_signature='', partner_signature='', invoker_key=''):
        super(ChannelQuickSettleEvent, self).execute(block_height)

        if self.is_event_founder:
            self.contract_event_api.quick_settle(
                invoker, channel_id, nonce, founder, founder_balance, partner, partner_balance,
                founder_signature, partner_signature, invoker_key, gwei_coef=self.gwei_coef)

        # set next stage
        self.next_stage()

    def terminate(self, block_height, state='', asset_type='TNC'):
        super(ChannelQuickSettleEvent, self).terminate(block_height)

        # to check the total deposit of the channel
        total_deposit = self.contract_event_api.get_channel_total_balance(self.channel_name)
        if 0 >= total_deposit:
            Channel.update_channel(self.channel_name, state=state)
            sync_channel_info_to_gateway(self.channel_name, 'DeleteChannel', asset_type)
            console_log.info('Channel {} state is {}'.format(self.channel_name, state))
            self.next_stage()

