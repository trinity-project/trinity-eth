# --*-- coding : utf-8 --*--
"""
Package : Trinity basic numbers

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
# System or 3rd party libraries
import re
import logging
from enum import Enum

# Trinity SW packages
from trilibs.validation.base import str_validator
from trilibs.exceptions import TrinityException


LOG = logging.getLogger(__name__)


class EnumTrinityNumberError(Enum):
    """
    Description: Trinity number error code definition
    """
    TRINITY_NUMBER_WITH_ILLEGAL_FORMAT = \
        '{} number<{}> not match to the regexp {}!'

    TRINITY_OPERATOR_WITH_INVALID_TYPE = \
        'Number<{}> should be int or TrinityNumber Type, but {} Type!'


class TrinityNumberException(TrinityException):
    """Description: Trinity number base exception class"""
    pass


class TrinityNumber(object):
    """
    Description: Number Type of the Trinity SW packages.

        This class will not focus on the length of the fragment, if it exceeds
    the max length, it will be cut off by the max length.
    """
    def __init__(self, number: str, asset_type='TNC'):
        """

        :param number:
        :param asset_type:
        """
        # validate the input parameters
        str_validator(number)
        str_validator(asset_type)

        self.asset_type = asset_type.upper()
        self.pattern, self.exponent, self.coefficient = \
            self.get_triple_unit(self.asset_type)

        # check whether this number is matched with the regular expression
        if not re.match(self.pattern, number):
            raise TrinityNumberException(
                EnumTrinityNumberError.TRINITY_NUMBER_WITH_ILLEGAL_FORMAT,
                EnumTrinityNumberError.TRINITY_NUMBER_WITH_ILLEGAL_FORMAT.value
                .format(self.asset_type, number, self.pattern)
            )

        # convert this number to the list with 1 or 2 members
        number_list = number.split('.')

        # Split the number to the integer and fragment parts
        self.integer = int(number_list[0].strip())
        self.fragment = 0

        # The number has fragment
        if number.__contains__('.'):
            # padding 0 behind the fragment
            fragment = number_list[1].strip().ljust(self.exponent, '0')
            self.fragment = int(fragment[0: self.exponent])

        # Set the number
        self.number = self.integer * self.coefficient + self.fragment

    def __str__(self):
        """Description: change the number to the string format"""
        if self.fragment:
            fragment = self.fragment.__str__().rjust(self.exponent, '0')
            return '{}.{}'.format(self.integer, fragment.rstrip('0'))

        return '{}'.format(self.integer)

    @classmethod
    def get_triple_unit(cls, asset_type):
        """
        Description: triple-unit property of the trinity number:
                     regular expression;
                     number exponent;
                     number multiply coefficient
        :return:
        """
        if asset_type in ['ETH']:
            # TODO: replace the return value in the future
            return None, 18, pow(10, 18)
        elif asset_type in ['NEO']:
            # TODO: replace the return value in the future
            return None, 1, pow(10, 0)
        else:
            # Default: TNC type
            return r'1[0]{9}$|\d{1,9}$|\d{1,9}\.\d+$', 8, pow(10, 8)

    def __add__(self, other):
        """
        Description: Add operators
        :param other: int or TrinityNumber type
        :return:
        """
        if isinstance(other, int):
            return self.number + other
        elif isinstance(other, TrinityNumber):
            return self.number + other.number
        else:
            raise TrinityNumberException(
                EnumTrinityNumberError.TRINITY_OPERATOR_WITH_INVALID_TYPE.value
                .format(other, type(other))
            )

    def __sub__(self, other):
        """
        Description: subtract operators
        :param other: int or TrinityNumber type
        :return:
        """
        if isinstance(other, int):
            return self.number - other
        elif isinstance(other, TrinityNumber):
            return self.number - other.number
        else:
            raise TrinityNumberException(
                EnumTrinityNumberError.TRINITY_OPERATOR_WITH_INVALID_TYPE.value
                .format(other, type(other))
            )


if '__main__' == __name__:
    a = TrinityNumber('100884.001')
    print(type(a-TrinityNumber('1')))
