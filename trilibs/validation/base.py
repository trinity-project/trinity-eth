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
from enum import Enum

# Import Trinity Sw libs
from trilibs.exceptions import TrinityException
from .decorators import validate_basic_types


class EnumBasicTypeError(Enum):
    """
    Description: Basic Type error code definition
    """
    TYPE_SHOULD_BE_INTEGER = \
        'Value<{}> should be int type, but {} type!'
    TYPE_SHOULD_BE_FLOAT = \
        'Value<{}> should be float type, but {} type!'
    TYPE_SHOULD_BE_INT_OR_FLOAT = \
        'Value<{}> should be int or float type, but {} type!'

    TYPE_SHOULD_BE_STRING = \
        'Value<{}> should be str type, but {} type!'

    TYPE_SHOULD_BE_DICT = \
        'Value<{}> should be dict type, but {} type!'
    TYPE_SHOULD_BE_LIST_OR_TUPLE = \
        'Value<{}> should be float type, but {} type!'


class TrinityTypeError(TrinityException):
    """Description: Type error"""
    pass


# Basic type validator method
@validate_basic_types(TrinityTypeError,
                      EnumBasicTypeError.TYPE_SHOULD_BE_INTEGER)
def int_validator(value):
    """

    :param value: should be int type
    :return:
    """
    return isinstance(value, int)


@validate_basic_types(TrinityTypeError,
                      EnumBasicTypeError.TYPE_SHOULD_BE_FLOAT)
def float_validator(value):
    """

    :param value: Should be float type
    :return:
    """
    return isinstance(value, float)


@validate_basic_types(TrinityTypeError,
                      EnumBasicTypeError.TYPE_SHOULD_BE_INT_OR_FLOAT)
def int_or_float_validator(value):
    """

    :param value: Should be float or int type
    :return:
    """
    return isinstance(value, (int, float))


@validate_basic_types(TrinityTypeError,
                      EnumBasicTypeError.TYPE_SHOULD_BE_STRING)
def str_validator(value):
    """

    :param value: Should be str type
    :return:
    """
    return isinstance(value, str)


@validate_basic_types(TrinityTypeError,
                      EnumBasicTypeError.TYPE_SHOULD_BE_DICT)
def dict_validator(value):
    """

    :param value: Should be dict type
    :return:
    """
    return isinstance(value, dict)


@validate_basic_types(TrinityTypeError,
                      EnumBasicTypeError.TYPE_SHOULD_BE_LIST_OR_TUPLE)
def list_validator(value):
    """

    :param value: Should be list type
    :return:
    """
    return isinstance(value, (list, tuple))


def tuple_validator(value):
    """

    :param value: should be tuple type
    :return:
    """
    return list_validator(value)
