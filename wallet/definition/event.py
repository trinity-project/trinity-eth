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
from enum import Enum, IntEnum


class EnumEventAction(Enum):
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

    # test event
    EVENT_TYPE_TEST_STATE = 0xE0
