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
from enum import Enum, IntEnum
from common.decorator import ucoro
from common.log import LOG
from .contract_event import ContractEventInterface


class EnumEventAction(Enum):
    EVENT_INIT = 'INIT'
    EVENT_PREPARE = 'prepare'
    EVENT_EXECUTE = 'execute'
    EVENT_TERMINATE = 'terminate'
    EVENT_COMPLETE = 'complete'

    EVENT_TIMEOUT = 'timeout_handler'
    EVENT_ERROR = 'error_handler'


class EnumEventType(IntEnum):
    # both wallet are online
    EVENT_TYPE_DEPOSIT = 0x0
    EVENT_TYPE_RSMC = 0x04
    EVENT_TYPE_HTLC = 0x08
    EVENT_TYPE_QUICK_SETTLE = 0x0c

    # One of Both wallets is online
    EVENT_TYPE_SETTLE = 0x10
    EVENT_TYPE_UPDATE_SETTLE = 0x11
    EVENT_TYPE_END_SETTLE = 0x12
    EVENT_TYPE_END_SETTLE_UPDATE = 0x13

    # Event for htlc lock
    EVENT_TYPE_HTLC_UNLOCK = 0x20
    EVENT_TYPE_PUNISH_HTLC_UNLOCK = 0x21
    EVENT_TYPE_SETTLE_HTLC_UNLOCK = 0x22
    EVENT_TYPE_SETTLE_HTLC_UNLOCK_UPDATE = 0x23

    # test event
    EVENT_TYPE_TEST_STATE = 0xE0


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
        self._event_timeout = 30        # default timeout: 12 block height. it's about 3 minutes
        self.is_event_ready = False

        self.event_stage_list = [EnumEventAction.EVENT_PREPARE, EnumEventAction.EVENT_EXECUTE,
                                 EnumEventAction.EVENT_TERMINATE, EnumEventAction.EVENT_COMPLETE]
        self.event_stage_iterator = iter(self.event_stage_list)
        self.event_stage = self.next_stage()

        self.start_time = 0
        self.need_websocket = False

        self.contract_event_api = ContractEventInterface()
        self.gwei_coef = self.contract_event_api.gwei_coefficient

        self.contract_executed_success = 1

    def retry_event(self):
        self.retry = True
        self.gwei_coef = self.gwei_for_retry
        self._event_timeout += 20       # retry timeout: extra 20 block height. it's about 5 minutes
        self.is_event_ready = False
        self.event_stage_iterator = iter(self.event_stage_list)
        self.event_stage = self.next_stage()

    @property
    def gwei_for_retry(self):
        auto_adaptive_list = [2, 5, 8, 10]

        # gwei_coef in the adaptor
        if self.gwei_coef not in auto_adaptive_list:
            auto_adaptive_list.append(self.gwei_coef)
            auto_adaptive_list.sort()

        # get the index of the gwei_coef
        coef_index = auto_adaptive_list.index(self.gwei_coef)
        try:
            return auto_adaptive_list[coef_index+1]
        except Exception as error:
            return self.gwei_coef + 1

    @property
    def event_timeout(self):
        return self.start_time + self._event_timeout

    def stage_is_changed(self, stage):
        return self.event_stage != stage

    def set_event_state(self, stage):
        self.event_stage = stage

    def set_event_start_time(self, start_time:int):
        """

        :param start_time: use chain block height to record time.
        :return:
        """
        if 0 == self.start_time:
            self.start_time = start_time + 1

    def next_stage(self):
        self.event_stage = next(self.event_stage_iterator)
        return self.event_stage

    def set_timeout_stage(self):
        self.event_stage = EnumEventAction.EVENT_TIMEOUT

    def set_error_stage(self):
        self.event_stage = EnumEventAction.EVENT_ERROR

    def set_event_ready(self, ready=True):
        LOG.debug('set event<{}> ready'.format(self.event_name))
        self.is_event_ready = ready

    def is_event_completed(self):
        return self.event_stage.name == EnumEventAction.EVENT_COMPLETE.name

    @property
    def stage_name(self):
        return self.event_stage.name

    @property
    def stage_action(self):
        return self.event_stage.value

    @property
    def event_type_name(self):
        return self.event_type.name

    def check_transaction_success(self, tx_hash):
        """

        :param tx_hash: transaction id by eth blockchain
        :return:
        """
        if tx_hash:
            result = self.contract_event_api._eth_interface.get_transaction_receipt(tx_hash)

            # check the status is successs or not
            if result:
                if self.contract_executed_success == result.get('status'):
                    # means we will go to next step
                    return True
                else:
                    # need a new transaction
                    return None
            else:
                # continue check this transaction id
                return False
        else:
            return None

    @staticmethod
    def check_valid_action(self, action_type):
        assert EnumEventAction.__contains__(action_type), 'Invalid action_type<{}>'.format(action_type)

    def prepare(self, block_height, *args, **kwargs):
        LOG.debug('{} stage of event<{}-{}> at block-{}'.format(self.stage_action, self.event_name,
                                                                self.event_type_name, block_height))
        self.set_event_start_time(int(block_height))
        return True

    def execute(self, block_height, *args, **kwargs):
        LOG.debug('{} stage of event<{}-{}> at block-{}'.format(self.stage_action, self.event_name,
                                                                self.event_type_name, block_height))
        return True

    def terminate(self, block_height, *args, **kwargs):
        LOG.debug('{} stage of event<{}-{}> at block-{}'.format(self.stage_action, self.event_name,
                                                                self.event_type_name, block_height))
        return True

    def complete(self, block_height, *args, **kwargs):
        LOG.info('{} stage of event<{}-{}> at block-{}'.format(self.stage_action, self.event_name,
                                                                self.event_type_name, block_height))
        return True

    def timeout_handler(self, block_height, *args, **kwargs):
        LOG.warning('Timeout stage of event<{}-{}> at block-{}'.format(self.event_name, self.event_type_name,
                                                                       block_height))

        if not self.retry:
            self.retry_event()
        else:
            self.set_error_stage()
        pass

    def error_handler(self, block_height, *args, **kwargs):
        LOG.error('Error stage of event<{}-{}> at block-{}'.format(self.event_name, self.event_type_name, block_height))
        pass

    def register_args(self, action_type, *args, **kwargs):
        self.is_valid_action(action_type)

        action_name = action_type.name
        self.__dict__.update({action_name: EventArgs(*args, **kwargs)})

    @property
    def event_arguments(self):
        return self.__dict__.get(self.stage_name, EventArgs())

    @staticmethod
    def is_valid_action(action_type):
        assert EnumEventAction.__contains__(action_type), 'Invalid action_type<{}>.'.format(action_type)

    def handle(self, block_height):
        event_args = self.event_arguments
        self.__getattribute__(self.stage_action.__str__())(block_height, *event_args.args, **event_args.kwargs)


class EventMachine(object):
    """

    """
    def __init__(self):
        self._coro_number = 8

        self.__event_queue = dict()
        self.__event_ordered_list = list()

        self.event_lock = Lock()
        self.total_task_per_poll = 0

    @ucoro(0.1, True)
    def __coroutine_handler(self, block_height:int, **kwargs):
        event_name, current_event = self.get_event()
        old_stage = EnumEventAction.EVENT_INIT

        # execute the event method according to the event stage
        while current_event.stage_is_changed(old_stage):
            old_stage = current_event.event_stage
            current_event.handle(block_height)

        if not self.is_event_completed(current_event.event_stage):
            # insert the event back into the queue
            self.insert_event_back_into_queue(event_name, current_event)

        # to judge whether current event is timeout or not
        if block_height > current_event.event_timeout:
            # set the event timeout
            current_event.set_timeout_stage()

    def coro_grouper(self, block_height):
        while True:
            yield from self.__coroutine_handler(block_height)

    def handle(self, block_height):
        if self.is_queue_empty() or self.is_polling_finished:
            return None
        max_task = min(self._coro_number, len(self.__event_ordered_list))
        self.total_task_per_poll += max_task

        for task_idx in range(max_task):
            coro = self.coro_grouper(block_height)
            next(coro)
            coro.send(block_height)

        pass

    @property
    def is_polling_finished(self):
        return self.total_task_per_poll >= len(self.__event_ordered_list)

    def reset_polling(self):
        if self.is_polling_finished:
            self.total_task_per_poll = 0

    def get_event(self):
        try:
            self.event_lock.acquire()
            name = self.__event_ordered_list.pop(0)
            event = self.__event_queue.pop(name)
        except Exception as error:
            name = None
            event = None
            LOG.error('event machine get_event exception: {}'.format(error))
        finally:
            self.event_lock.release()

        return name, event

    def get_registered_event(self, name):
        return self.__event_queue.get(name)

    def insert_event_back_into_queue(self, name, event):
        try:
            self.event_lock.acquire()
            if not self.has_event(name):
                self.__event_queue.update({name: event})
                self.__event_ordered_list.append(name)
        except Exception as error:
            LOG.error('event machine insert_event_back_into_queue<{}> exception: {}'.format(name, error))
        finally:
            self.event_lock.release()

        return

    def register_event(self, name, event):
        try:
            self.event_lock.acquire()
            self.__event_queue.update({name: event})
        except Exception as error:
            LOG.error('event machine register_event<{}> exception: {}'.format(name, error))
        finally:
            self.event_lock.release()

    def unregister_event(self, name):
        try:
            self.event_lock.acquire()
            if name in self.__event_ordered_list:
                self.__event_ordered_list.remove(name)

            if name in self.__event_queue.keys():
                self.__event_queue.pop(name)
        except Exception as error:
            LOG.error('event machine unregister_event<{}> exception: {}'.format(name, error))
        finally:
            self.event_lock.release()

    def update_event(self, name, event):
        self.register_event(name, event)

    def trigger_start_event(self, name):
        try:
            self.event_lock.acquire()
            if name not in self.__event_ordered_list:
                self.__event_ordered_list.append(name)
        except Exception as error:
            LOG.error('event machine trigger_start_event<{}> exception: {}'.format(name, error))
        finally:
            self.event_lock.release()

    def has_event(self, name):
        return name in self.__event_queue

    @staticmethod
    def is_event_completed(stage):
        return stage in [EnumEventAction.EVENT_COMPLETE, EnumEventAction.EVENT_ERROR]

    def is_queue_empty(self):
        return 0 == len(self.__event_ordered_list)


event_machine = EventMachine()
