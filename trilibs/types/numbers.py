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

    # operator error definition
    TRINITY_OPERATOR_WITH_INVALID_TYPE = \
        'Number<{}> should be int or TrinityNumber type, but {} type!'

    TRINITY_ADD_WITH_ERROR_TYPE = \
        'Operator "+" should be with int or TrinityNumber type, but {} type!'

    TRINITY_SUB_WITH_ERROR_TYPE = \
        'Operator "-" should be with int or TrinityNumber type, but {} type!'

    TRINITY_EQUAL_WITH_ERROR_TYPE = \
        'Operator "==" should be with int or TrinityNumber type, but {} type!'

    TRINITY_NOT_EQUAL_WITH_ERROR_TYPE = \
        'Operator "!=" should be with int or TrinityNumber type, but {} type!'

    TRINITY_GREATER_EQUAL_WITH_ERROR_TYPE = \
        'Operator ">=" should be with int or TrinityNumber type, but {} type!'

    TRINITY_GREATER_THAN_WITH_ERROR_TYPE = \
        'Operator ">" should be with int or TrinityNumber type, but {} type!'

    TRINITY_LESS_EQUAL_WITH_ERROR_TYPE = \
        'Operator "<=" should be with int or TrinityNumber type, but {} type!'

    TRINITY_LESS_THAN_WITH_ERROR_TYPE = \
        'Operator "<" should be with int or TrinityNumber type, but {} type!'


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
        """ Return self.number + other or self.number + other.number """
        other = self.__other__(
            other, EnumTrinityNumberError.TRINITY_ADD_WITH_ERROR_TYPE
        )

        return self.number.__add__(other)

    def __sub__(self, other):
        """ Return self.number - other or self.number - other.number """
        other = self.__other__(
            other, EnumTrinityNumberError.TRINITY_SUB_WITH_ERROR_TYPE
        )

        return self.number.__sub__(other)

    def __eq__(self, other):
        """ Return self.number == other or self.number == other.number """
        other = self.__other__(
            other, EnumTrinityNumberError.TRINITY_EQUAL_WITH_ERROR_TYPE
        )

        return self.number.__eq__(other)

    def __ne__(self, other):
        """ Return self.number != other or self.number != other.number """
        other = self.__other__(
            other, EnumTrinityNumberError.TRINITY_NOT_EQUAL_WITH_ERROR_TYPE
        )

        return self.number.__ne__(other)

    def __le__(self, other):
        """ Return self.number <= other or self.number <= other.number """
        other = self.__other__(
            other, EnumTrinityNumberError.TRINITY_LESS_EQUAL_WITH_ERROR_TYPE
        )

        return self.number.__le__(other)

    def __lt__(self, other):
        """" Return self.number < other or self.number < other.number """
        other = self.__other__(
            other, EnumTrinityNumberError.TRINITY_LESS_THAN_WITH_ERROR_TYPE
        )

        return self.number.__lt__(other)

    def __ge__(self, other):
        """ Return self.number >= other or self.number > other.number """
        other = self.__other__(
            other, EnumTrinityNumberError.TRINITY_GREATER_EQUAL_WITH_ERROR_TYPE
        )

        return self.number.__ge__(other)

    def __gt__(self, other):
        """ Return self.number > other or self.number > other.number """
        other = self.__other__(
            other, EnumTrinityNumberError.TRINITY_GREATER_THAN_WITH_ERROR_TYPE
        )

        return self.number.__gt__(other)

    @classmethod
    def __other__(cls, other, error_code=None):
        """
        Description: pre-process the other number before operating with
                     TrinityNumber.

        :param other: the number is used to operate with self
        :param error_code: Defined in EnumTrinityNumberError
        :return:
        """
        if isinstance(other, int):
            return other
        elif isinstance(other, TrinityNumber):
            return other.number

        # raise error or return 0
        if error_code:
            raise TrinityNumberException(
                error_code, error_code.value.format(other, type(other))
            )
        else:
            LOG.error(
                'Number<{}> should be int or TrinityNumber type, but {} type'
                .format(other, type(other))
            )
            return 0
