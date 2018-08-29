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


class EnumResponseStatus(IntEnum):
    """
    Define all response message status here.

    Suggestion: It's better to define meaningful name for each member which will be displayed to the app, when user
                read the messages, he / she will make clear what happened.
    """
    RESPONSE_OK = 0x0
    """
        Question: Need we define some different response ok to distinguish the transaction type ????
        .e.g:
        RESPONSE_FOUNDER_OK # for creating event message
        RESPONSE_RSMC_OK    # for RSMC transaction message
    """

    # Founder Message
    RESPONSE_FOUNDER_DEPOSIT_LESS_THAN_PARTNER = 0x10
    RESPONSE_FOUNDER_NONCE_NOT_ZERO = 0x11

    # message header error
    RESPONSE_MESSAGE_HEADER_ERROR = 0x79

    # Channel related error
    RESPONSE_CHANNEL_NOT_FOUND = 0x80
<<<<<<< HEAD:wallet/transaction/response.py
=======
    RESPONSE_CHANNEL_NOT_OPENED = 0x81

    # payment related error
    RESPONSE_PAYMENT_NOT_FOUND = 0x9F
>>>>>>> dev:wallet/transaction/response.py

    # Trade related error
    RESPONSE_TRADE_NOT_FOUND = 0xa0
    RESPONSE_TRADE_NOT_ENOUGH_BALANCE = 0xa1
    RESPONSE_TRADE_MISSING_IN_DB = 0xa2
    RESPONSE_TRADE_INCORRECT_ROLE = 0xa3
    RESPONSE_TRADE_INCOMPATIBLE_NONCE = 0xa4
    RESPONSE_TRADE_VERIFIED_ERROR = 0xa5
<<<<<<< HEAD:wallet/transaction/response.py
    RESPONSE_TRADE_HASHR_NOT_FOUND = 0x6
=======
    RESPONSE_TRADE_HASHR_NOT_FOUND = 0xa6
    RESPONSE_TRADE_INCORRECT_PAYMENT = 0xa7
    RESPONSE_TRADE_BALANCE_ERROR = 0xa8
>>>>>>> dev:wallet/transaction/response.py

    # router related error
    RESPONSE_ROUTER_VOID_ROUTER = 0xEF

    # Common response error
    RESPONSE_EXCEPTION_HAPPENED = 0xF0
    RESPONSE_FAIL = 0XFF
