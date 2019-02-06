# --*-- coding : utf-8 --*--
"""
Package : 

Author  : Trinity Core Team

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
FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
# Import System or 3rd-party libs
from enum import IntEnum

# Import Trinity Sw libs
from trig.exceptions import TrinityException


class EnumAssetCode(IntEnum):
    """
    Description: Asset type validation error code definition
    """
    # common error
    ASSET_ID_OR_TYPE_ERROR = 0x0

    # Future asset typ support
    ASSET_TYPE_BE_SUPPORTED_IN_FUTURE = 0x1

    # Asset type or ID error code
    ASSET_ID_OR_TYPE_NOT_FOUND = 0x40
    ASSET_WITH_ERROR_TYPES = 0x41


class AssetException(TrinityException):
    """Description: basic exception for asset validation"""
    pass


class AssetFutureException(TrinityException):
    """Description: Asset will be used in future"""
    pass
