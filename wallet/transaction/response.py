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
    # Signature error
    RESPONSE_SIGNATURE_VERIFIED_ERROR = 0x7F

    # Founder Message
    RESPONSE_FOUNDER_DEPOSIT_LESS_THAN_PARTNER = 0x80

    # message header error
    RESPONSE_HEADER_ERROR = 0x100
    RESPONSE_ASSET_TYPE_NOT_SUPPORTED = 0x101
    RESPONSE_INVALID_URL_FORMAT = 0x102
    RESPONSE_INVALID_NETWORK_MAGIC = 0x103

    # Channel related error
    RESPONSE_CHANNEL_NOT_FOUND = 0x180
    RESPONSE_CHANNEL_NOT_OPENED = 0x181

    # payment related error
    RESPONSE_PAYMENT_RECORD_NOT_FOUND = 0x200

    # Trade related error
    RESPONSE_TRADE_NOT_FOUND = 0x280
    RESPONSE_TRADE_MISSING_IN_DB = 0x282
    RESPONSE_TRADE_INCORRECT_ROLE = 0x283
    RESPONSE_TRADE_VERIFIED_ERROR = 0x285
    RESPONSE_TRADE_NEGATIVE_PAYMENT = 0x287
    RESPONSE_TRADE_BALANCE_ERROR = 0x288
    RESPONSE_TRADE_BALANCE_UNMATCHED_BETWEEN_PEERS = 0x288
    RESPONSE_TRADE_NO_ENOUGH_BALANCE_FOR_PAYMENT = 0x289
    RESPONSE_TRADE_BALANCE_UPDATE_FAILED = 0x28a
    RESPONSE_TRADE_UNMATCHED_PAYMENT = 0x28b

    RESPONSE_TRADE_HASHR_ALREADY_EXISTED = 0x2FD
    RESPONSE_TRADE_HASHR_NOT_MATCHED_WITH_RCODE=0x2FE
    RESPONSE_TRADE_HASHR_NOT_FOUND = 0x2FF

    # nonce related error
    RESPONSE_FOUNDER_WITH_ILLEGAL_NONCE = 0x300
    RESPONSE_QUICK_CLOSE_CHANNEL_WITH_ILLEGAL_NONCE = 0x381
    RESPONSE_TRADE_WITH_INCORRECT_NONCE = 0x382
    RESPONSE_TRADE_WITH_INCOMPATIBLE_NONCE = 0x383
    RESPONSE_TRADE_LOCKED_ASSET_LESS_THAN_PAYMENT = 0x384

    # router related error
    RESPONSE_ROUTER_VOID_ROUTER = 0x800

    # Common response error
    RESPONSE_ILLEGAL_INPUT_PARAMETER = 0xFFFD
    RESPONSE_EXCEPTION_HAPPENED = 0xFFFE
    RESPONSE_FAIL = 0XFFFF
