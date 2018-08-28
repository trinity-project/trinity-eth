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

    def execute(self, block_height, invoker_uri='', channel_name='', nonce=None, invoker_key=''):
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
        Channel.force_release_rsmc(invoker_uri, channel_name, nonce, invoker_key, gwei_coef=self.gwei_coef,
                                   trigger=self.contract_event_api.close_channel)

        # set channel settling
        Channel.update_channel(self.channel_name, state=EnumChannelState.SETTLING.name)
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
        Channel.force_release_rsmc(invoker_uri, channel_name, nonce, invoker_key, gwei_coef=self.gwei_coef,
                                   trigger=self.contract_event_api.update_close_channel)

        # set channel settling
        Channel.update_channel(self.channel_name, state=EnumChannelState.CLOSED.name)

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
        self.contract_event_api.end_close_channel(invoker, channel_name, invoker_key, gwei_coef=self.gwei_coef)

        # set channel settling
        Channel.update_channel(self.channel_name, state=EnumChannelState.CLOSED.name)
        self.next_stage()

    def terminate(self, block_height, *args, **kwargs):
        super(ChannelEndSettleEvent, self).terminate(block_height, *args, **kwargs)
        self.next_stage()

