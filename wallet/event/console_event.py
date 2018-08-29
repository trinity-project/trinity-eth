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
# from collections import namedtuple
from enum import Enum
from common.singleton import SingletonClass
<<<<<<< HEAD
from common.coroutine import ucoro
=======
from common.decorator import ucoro
>>>>>>> dev
from common.log import LOG


class EnumConsoleTrigger(Enum):
    CONSOLE_TRIGGER_FOUNDER = 'founder'
    CONSOLE_TRIGGER_RSMC = 'rsmc'
    CONSOLE_TRIGGER_HTLC = 'htlc'
    CONSOLE_TRIGGER_QUICK_CLOSE = 'settle'
    CONSOLE_TRIGGER_CLOSE = 'off_chain_settle'


class ConsoleEventHandler(metaclass=SingletonClass):
    """

    """
    def __init__(self):
        self.coroutine_caller = None
        self.event_type = None
        pass

    @ucoro()
    def __coroutine_handler(self, *args, **kwargs):
        if not args:
            LOG.debug('No event is received.')
            return

        received_event = args[0]
        # for console event, there are 3 parts: EnumConsoleTrigger type, args and kwargs
        self.event_type = received_event[0]
        argument = received_event[1]
        kwargument = received_event[2]

        if not EnumConsoleTrigger.__contains__(self.event_type):
            LOG.error('Console event<{}> type is undefined.'.format(self.event_type))
            return

        # to call the event handler
        self.__dict__.get(self.event_type.name, self.error_handler)(*argument, **kwargument)

        return

    def handle(self, *args, **kwargs):
        self.coroutine_caller = self.__coroutine_handler(*args, **kwargs)

    def trigger_event(self, event_type, *args, **kwargs):
        message = [event_type, args, kwargs]
        self.coroutine_caller.send(message)

    def founder(self, *args, **kwargs):
        pass

    def rsmc(self, *args, **kwargs):
        pass

    def htlc(self, *args, **kwargs):
        pass

    def settle(self, *args, **kwargs):
        pass

    def off_chain_settle(self, *args, **kwargs):
        pass

    def error_handler(self):
        LOG.error('Unsupported event type<{}>'.format(self.event_type))
        return


console_message_event = ConsoleEventHandler()
