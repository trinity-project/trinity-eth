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
from .event import EventBase
from wallet.channel import Channel
from wallet.definition import EnumEventType, EnumEventAction
from blockchain.event import event_test_state
from common.log import LOG


class ChannelEventBase(EventBase):
    """

    """
    def __init__(self, channel_name, event_type, is_event_founder=True):
        super(ChannelEventBase, self).__init__(channel_name, event_type, is_event_founder)

        self.channel_name = channel_name
        self.channel = Channel.channel(channel_name)


class ChannelTestEvent(ChannelEventBase):
    def __init__(self):
        super(ChannelTestEvent, self).__init__('test_event', EnumEventType.EVENT_TYPE_TEST_STATE, True)

    def execute(self, *args, **kwargs):
        super(ChannelTestEvent, self).execute(*args, **kwargs)
        event_test_state()
        self.set_event_stage(EnumEventAction.EVENT_COMPLETE)


class ChannelDepositEvent(ChannelEventBase):
    def __init__(self, channel_name, is_event_founder=True):
        super(ChannelDepositEvent, self).__init__(channel_name, EnumEventType.EVENT_TYPE_DEPOSIT, is_event_founder)

    def prepare(self, *args, **kwargs):
        super(ChannelDepositEvent, self).prepare(*args, **kwargs)
        if hasattr(self, EnumEventAction.prepare_event.name):
            length_of_args = len(self.prepare_event.args)
            address = self.prepare_event.args[0] if 1 <= length_of_args else self.prepare_event.kwargs.get('address')
            balance = self.prepare_event.args[1] if 2 <= length_of_args else self.prepare_event.kwargs.get('balance')
            peer_address = self.prepare_event.args[2] if 3 <= length_of_args else self.prepare_event.kwargs.get('peer_address')
            peer_balance = self.prepare_event.args[3] if 4 <= length_of_args else self.prepare_event.kwargs.get('peer_balance')

            try:
                # approved balance
                approved_balance = float(self.channel.get_approved_asset(address))
                peer_approved_balance = float(self.channel.get_approved_asset(peer_address))
                if 0 == approved_balance or 0 == peer_approved_balance:
                    return None, None

                LOG.debug('Approved asset: self<{}:{}>, peer<{}:{}>'.format(address, approved_balance,
                                                                            peer_address, peer_approved_balance))
                return approved_balance >= float(balance), peer_approved_balance >= float(peer_balance)
            except Exception as error:
                LOG.error('Action prepare exception: {}'.format(error))
                pass
        else:
            return True, True

        return None, None

    def action(self):
        super(ChannelDepositEvent, self).action()
        self.finish_preparation = True
        if hasattr(self, EnumEventAction.action_event.name):
            try:
                if self.is_founder:
                    self.channel.approve_deposit(*self.action_event.args, **self.action_event.kwargs)
            except Exception as error:
                pass
            else:
                # register monitor deposit event
                event_monitor_deposit(self.channel_name, self.asset_type)

    def terminate(self):
        super(ChannelDepositEvent, self).terminate()
        if hasattr(self, EnumEventAction.terminate_event.name):
            return self.channel.update_channel(**self.terminate_event.kwargs)


class ChannelQuickSettleEvent(ChannelEventBase):
    def __init__(self, channel_name, asset_type):
        super(ChannelQuickSettleEvent, self).__init__(channel_name, asset_type, EnumEventType.EVENT_TYPE_QUICK_SETTLE)

    def action(self):
        super(ChannelQuickSettleEvent, self).action()
        self.finish_preparation = True
        if hasattr(self, EnumEventAction.action_event.name):
            if self.is_founder:
                self.channel.quick_settle(*self.action_event.args, **self.action_event.kwargs)

            # register monitor quick settle event
            event_monitor_quick_close_channel(self.channel_name, self.asset_type)

    def terminate(self):
        super(ChannelQuickSettleEvent, self).terminate()
        if hasattr(self, EnumEventAction.terminate_event.name):
            return self.channel.update_channel(**self.terminate_event.kwargs)