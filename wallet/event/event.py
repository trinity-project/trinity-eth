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
from threading import Lock
from wallet.definition import EnumEventAction
from common.coroutine import ucoro
from common.log import LOG


class EventArgs(object):
    """

    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class EventBase(object):
    """

    """
    def __init__(self, event_name, event_type, is_event_founder=True):
        self.event_name = event_name
        self.event_type = event_type

        self.is_event_founder = is_event_founder
        self.retry = False
        self._event_timeout = 12        # default timeout: 12 block height. it's about 3 minutes
        self.is_event_ready = False
        self.event_stage = EnumEventAction.EVENT_PREPARE

        self.start_time = 0
        self.need_websocket = False

    def retry_event(self):
        self.retry = True
        self._event_timeout += 20       # retry timeout: extra 20 block height. it's about 5 minutes
        self.is_event_ready = False
        self.event_stage = EnumEventAction.EVENT_PREPARE

    @property
    def event_timeout(self):
        return self.start_time + self._event_timeout

    def stage_is_changed(self, stage):
        return self.event_stage != stage

    def set_event_start_time(self, start_time:int):
        """

        :param start_time: use chain block height to record time.
        :return:
        """
        if 0 == self.start_time:
            self.start_time = start_time + 1

    def set_event_stage(self, stage=EnumEventAction.EVENT_PREPARE):
        self.event_stage = stage

    def set_event_ready(self, ready=True):
        LOG.debug('set event<{}> ready'.format(self.event_name))
        self.is_event_ready = ready

    def is_event_completed(self):
        return self.event_stage.name == EnumEventAction.EVENT_COMPLETE.name

    @property
    def stage_name(self):
        return self.event_stage.name

    @staticmethod
    def check_valid_action(self, action_type):
        assert EnumEventAction.__contains__(action_type), 'Invalid action_type<{}>'.format(action_type)

    def prepare(self, *args, **kwargs):
        LOG.debug('Start preparing stage of event<{}-{}>'.format(self.event_name, self.event_type))
        self.set_event_start_time(int(args[0]))
        pass

    def execute(self, *args, **kwargs):
        LOG.debug('Start executing stage of event<{}-{}>'.format(self.event_name, self.event_type))
        pass

    def terminate(self, *args, **kwargs):
        LOG.debug('Start terminating stage of event<{}-{}>'.format(self.event_name, self.event_type))
        pass

    def complete(self, *args, **kwargs):
        LOG.debug('Complete event<{}-{}>'.format(self.event_name, self.event_type))
        pass

    def timeout_handler(self, *args, **kwargs):
        LOG.warning('Timeout occurred for event<{}-{}>'.format(self.event_name, self.event_type))

        if not self.retry:
            self.retry_event()
        else:
            self.set_event_stage(EnumEventAction.EVENT_ERROR)
        pass

    def error_handler(self, *args, **kwargs):
        LOG.error('Error to execute event<{}-{}>'.format(self.event_name, self.event_type))
        pass

    def register_args(self, action_type, *args, **kwargs):
        self.is_valid_action(action_type)

        action_name = action_type.name
        self.__dict__.update({action_name: EventArgs(*args, **kwargs)})

    def is_valid_action(self, action_type):
        assert EnumEventAction.__contains__(action_type), 'Invalid action_type<{}>.'.format(action_type)


class EventMachine(object):
    """

    """
    def __init__(self):
        self._coro_number = 8

        self.__event_queue = dict()
        self.__event_ordered_list = list()

        self.event_lock = Lock()

    @ucoro(0.1, True)
    def __coroutine_handler(self, block_height:int):
        event_name, current_event = self.get_event()
        old_stage = EnumEventAction.EVENT_PREPARE

        # to judge whether current event is timeout or not
        if block_height > current_event.event_timeout:
            # set the event timeout
            current_event.set_event_stage(EnumEventAction.EVENT_TIMEOUT)

        # execute the event method according to the event stage
        while current_event.stage_is_changed(old_stage):
            current_event.__dict__[current_event.stage_name](block_height)
            old_stage = current_event.event_stage

        #
        if not self.is_event_completed(current_event.event_stage):
            # insert the event back into the queue
            self.insert_event_back_into_queue(event_name, current_event)

    def coro_grouper(self, block_height):
        while True:
            yield from self.__coroutine_handler(block_height)

    def handle(self, block_height):
        if self.is_queue_empty():
            return None
        max_task = min(self._coro_number, len(self.__event_ordered_list))

        for task_idx in range(max_task):
            coro = self.coro_grouper(block_height)
            next(coro)
            coro.send(block_height)

        pass

    def get_event(self):
        self.event_lock.acquire()
        name = self.__event_ordered_list.pop(0)
        event = self.__event_queue.pop(name)
        self.event_lock.release()

        return name, event

    def insert_event_back_into_queue(self, name, event):
        self.event_lock.acquire()
        if not self.has_event(name):
            self.__event_queue.update({name: event})
            self.__event_ordered_list.append(name)
        self.event_lock.release()

    def register_event(self, name, event):
        self.event_lock.acquire()
        self.__event_queue.update({name: event})
        self.event_lock.release()

    def register_event_key(self, name):
        self.event_lock.acquire()
        self.__event_ordered_list.append(name)
        self.event_lock.release()

    def has_event(self, name):
        return name in self.__event_queue

    @staticmethod
    def is_event_completed(stage):
        return stage in [EnumEventAction.EVENT_COMPLETE, EnumEventAction.EVENT_ERROR]

    def is_queue_empty(self):
        return 0 == len(self.__event_ordered_list)


event_machine = EventMachine()
