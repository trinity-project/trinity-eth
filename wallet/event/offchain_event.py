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
from .event import EventBase, EnumEventType
from wallet.channel import Channel
from model.base_enum import EnumChannelState

from common.log import LOG


class ChannelOfflineEventBase(EventBase):
    """

    """
    def __init__(self, channel_name, event_type, is_event_founder=True):
        super(ChannelOfflineEventBase, self).__init__(channel_name, event_type, is_event_founder)

        self.channel_name = channel_name
        self.channel = Channel(channel_name)


class ChannelForceSettleEvent(ChannelOfflineEventBase):
    def __init__(self, channel_name, is_event_founder=True):
        super(ChannelForceSettleEvent, self).__init__(channel_name, EnumEventType.EVENT_TYPE_SETTLE,
                                                      is_event_founder)

    def prepare(self, block_height, *args, **kwargs):
        super(ChannelForceSettleEvent, self).prepare(block_height, *args, **kwargs)
        self.next_stage()

    def execute(self, block_height, invoker_uri='', channel_name='', nonce=None, invoker_key='', is_debug=False):
        """

        :param block_height:
        :param invoker_uri:
        :param channel_name:
        :param trade:
        :param invoker_key:
        :param gwei:
        :return:
        """
        super(ChannelForceSettleEvent, self).execute(block_height)

        LOG.debug('parameter: {}, {}, {}, {}'.format(invoker_uri, channel_name, nonce, invoker_key))
        LOG.debug('event args: {}, kwargs'.format(self.event_arguments.args, self.event_arguments.kwargs))

        # close channel event
        result = Channel.force_release_rsmc(invoker_uri, channel_name, nonce, invoker_key, gwei_coef=self.gwei_coef,
                                            trigger=self.contract_event_api.close_channel, is_debug=is_debug)

        # set channel settling
        if result is not None and 'success' in result.values():
            Channel.update_channel(self.channel_name, state=EnumChannelState.SETTLED.name)
            self.next_stage()

    def terminate(self, block_height, *args, **kwargs):
        super(ChannelForceSettleEvent, self).terminate(block_height, *args, **kwargs)
        self.next_stage()


class ChannelUpdateSettleEvent(ChannelOfflineEventBase):
    def __init__(self, channel_name, is_event_founder=True):
        super(ChannelUpdateSettleEvent, self).__init__(channel_name, EnumEventType.EVENT_TYPE_UPDATE_SETTLE,
                                                       is_event_founder)

    def prepare(self, block_height, *args, **kwargs):
        super(ChannelUpdateSettleEvent, self).prepare(block_height, *args, **kwargs)
        self.next_stage()

    def execute(self, block_height, invoker_uri='', channel_name='', invoker_key='', nonce=None):
        """

        :param block_height:
        :param invoker_uri:
        :param channel_name:
        :param trade:
        :param invoker_key:
        :param gwei:
        :return:
        """
        super(ChannelUpdateSettleEvent, self).execute(block_height)

        # close channel event
        # ToDo uncomment below codes in future
        # latest_trade = Channel.latest_confirmed_trade()
        # if isinstance(nonce, int) and int(nonce) == latest_trade.nonce: # or check balance:
        #     self.next_stage()
        #     return

        result = Channel.force_release_rsmc(invoker_uri, channel_name, nonce, invoker_key, gwei_coef=self.gwei_coef,
                                            trigger=self.contract_event_api.update_close_channel)

        # set channel settling
        if result is not None and 'success' in result.values():
            Channel.update_channel(self.channel_name, state=EnumChannelState.SETTLED.name)

        self.next_stage()

    def terminate(self, block_height, *args, **kwargs):
        super(ChannelUpdateSettleEvent, self).terminate(block_height, *args, **kwargs)
        self.next_stage()


class ChannelEndSettleEvent(ChannelOfflineEventBase):
    def __init__(self, channel_name, is_event_founder=True):
        super(ChannelEndSettleEvent, self).__init__(channel_name, EnumEventType.EVENT_TYPE_END_SETTLE,
                                                    is_event_founder)

    def prepare(self, block_height, *args, **kwargs):
        super(ChannelEndSettleEvent, self).prepare(block_height, *args, **kwargs)
        self.next_stage()

    def execute(self, block_height, invoker='', channel_name='', invoker_key=''):
        """

        :param block_height:
        :param invoker_uri:
        :param channel_name:
        :param trade:
        :param invoker_key:
        :param gwei:
        :return:
        """
        super(ChannelEndSettleEvent, self).execute(block_height)

        # close channel event
        result = self.contract_event_api.end_close_channel(invoker, channel_name, invoker_key, gwei_coef=self.gwei_coef)

        # set channel settling
        if result is not None and 'success' in result.values():
            Channel.update_channel(self.channel_name, state=EnumChannelState.CLOSED.name)
        self.next_stage()

    def terminate(self, block_height, *args, **kwargs):
        super(ChannelEndSettleEvent, self).terminate(block_height, *args, **kwargs)
        self.next_stage()


class ChannelHtlcUnlockEvent(ChannelOfflineEventBase):
    def __init__(self, channel_name, is_event_founder=True):
        super(ChannelHtlcUnlockEvent, self).__init__(channel_name, EnumEventType.EVENT_TYPE_HTLC_UNLOCK,
                                                    is_event_founder)

    def prepare(self, block_height, *args, **kwargs):
        super(ChannelHtlcUnlockEvent, self).prepare(block_height, *args, **kwargs)
        self.next_stage()

    def execute(self, block_height, invoker_uri='', channel_name='', hashcode='', rcode='', invoker_key='',
                is_debug=False):
        """

        :param block_height:
        :param invoker_uri:
        :param channel_name:
        :param hashcode:
        :param rcode:
        :param invoker_key:
        :param is_debug:
        :return:
        """
        super(ChannelHtlcUnlockEvent, self).execute(block_height)

        LOG.debug('unlock htlc payment parameter: {}, {}, {}'.format(invoker_uri, channel_name, hashcode))
        LOG.debug('unlock htlc payment event args: {}, kwargs {}' \
                  .format(self.event_arguments.args, self.event_arguments.kwargs))

        # close channel event
        result = Channel.force_release_htlc(
            invoker_uri, channel_name, hashcode, rcode, invoker_key, gwei_coef=self.gwei_coef,
            trigger=self.contract_event_api.htlc_unlock_payment, is_debug=is_debug)

        # Don't close channel
        if result and 'success' in result.values():
            self.next_stage()

    def terminate(self, block_height, *args, **kwargs):
        super(ChannelHtlcUnlockEvent, self).terminate(block_height, *args, **kwargs)
        self.next_stage()


class ChannelPunishHtlcUnlockEvent(ChannelOfflineEventBase):
    def __init__(self, channel_name, is_event_founder=True):
        super(ChannelPunishHtlcUnlockEvent, self).__init__(channel_name, EnumEventType.EVENT_TYPE_PUNISH_HTLC_UNLOCK,
                                                       is_event_founder)

    def prepare(self, block_height, *args, **kwargs):
        super(ChannelPunishHtlcUnlockEvent, self).prepare(block_height, *args, **kwargs)
        self.next_stage()

    def execute(self, block_height, invoker_uri='', channel_name='', nonce='', hashcode='', rcode='', invoker_key=''):
        """

        :param block_height:
        :param invoker_uri:
        :param channel_name:
        :param nonce:
        :param hashcode:
        :param rcode:
        :param invoker_key:
        :return:
        """
        super(ChannelPunishHtlcUnlockEvent, self).execute(block_height)

        # punishment when other want to release the htlc-locked payment
        result = Channel.force_release_htlc(
            invoker_uri, channel_name, hashcode, rcode, invoker_key, gwei_coef=self.gwei_coef,
            trigger=self.contract_event_api.punish_when_htlc_unlock_payment, is_debug=False,
            is_pubnishment=True, nonce=nonce)

        # set channel settling
        if result is not None and 'success' in result.values():
            Channel.update_channel(self.channel_name, state=EnumChannelState.SETTLED.name)

        self.next_stage()

    def terminate(self, block_height, *args, **kwargs):
        super(ChannelPunishHtlcUnlockEvent, self).terminate(block_height, *args, **kwargs)
        self.next_stage()


class ChannelSettleHtlcUnlockEvent(ChannelOfflineEventBase):
    def __init__(self, channel_name, is_event_founder=True):
        super(ChannelSettleHtlcUnlockEvent, self).__init__(channel_name, EnumEventType.EVENT_TYPE_SETTLE_HTLC_UNLOCK,
                                                     is_event_founder)

    def prepare(self, block_height, *args, **kwargs):
        super(ChannelSettleHtlcUnlockEvent, self).prepare(block_height, *args, **kwargs)
        self.next_stage()

    def execute(self, block_height, invoker='', channel_name='', hashcode='', invoker_key=''):
        """

        :param block_height:
        :param invoker:
        :param channel_name:
        :param hashcode:
        :param invoker_key:
        :return:
        """
        super(ChannelSettleHtlcUnlockEvent, self).execute(block_height)

        # close channel event
        result = self.contract_event_api.settle_after_htlc_unlock_payment(invoker_key, channel_name, hashcode, invoker_key)

        # set channel settling
        if result is not None and 'success' in result.values():
            Channel.update_channel(self.channel_name, state=EnumChannelState.CLOSED.name)
        self.next_stage()

    def terminate(self, block_height, *args, **kwargs):
        super(ChannelSettleHtlcUnlockEvent, self).terminate(block_height, *args, **kwargs)
        self.next_stage()
