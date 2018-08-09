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
from enum import IntEnum


class EnumTradeType(IntEnum):
    """
    Define all supported transaction type
    """
    TRADE_TYPE_FOUNDER = 0x0
    TRADE_TYPE_RSMC = 0x10
    TRADE_TYPE_HTLC = 0x20
    TRADE_TYPE_SETTLE = 0x30


class EnumTradeRole(IntEnum):
    """
    Define what role is played in the transaction
    """
    TRADE_ROLE_FOUNDER = 0x1
    TRADE_ROLE_PARTNER = 0x2


class EnumTradeState(IntEnum):
    """
    Define transaction state
    """
    confirming = 0x10
    confirmed = 0x20

    # error transaction state
    stuck_by_error_deposit = 0x80
    failed = 0xFF
