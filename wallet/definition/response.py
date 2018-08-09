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

    # Common response error
    RESPONSE_EXCEPTION_HAPPENED = 0xF0
    RESPONSE_FAIL = 0XFF
