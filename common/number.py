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
from .exceptions import UnsupportedTrinityNumber
from .log import LOG
import re


def trinity_operator(callback):
    def wrapper(*args):
        if not (isinstance(args[0], TrinityNumber) or isinstance(args[0], int)):
            raise UnsupportedTrinityNumber('number<{}> should be TrinityNumber type. Type<{}>'.format(args[0], type(args[0])))
        result = callback(*args)

        if 0 == result:
            return str(result)

        integer = int(result // TrinityNumber._trinity_unit)
        fragment = int(result % TrinityNumber._trinity_unit)

        return '{}.{}'.format(integer, fragment).strip()
    return wrapper


class TrinityNumber(object):
    """

    """
    _trinity_coef = 8
    _trinity_unit = 1e+8

    def __init__(self, number: str, asset_type='TNC'):
        """

        :param number:
        """
        self.number = None

        if not number:
            return

        if not isinstance(number, str) or not re.match(r'1[0]{9}$|\d{1,9}$|\d{1,9}\.\d+$', number):
            LOG.warn('Number must be string type<{}>. Current is {}'.format(number, type(number)))
            return

        number_list = number.split('.')

        integer = int(number_list[0]) if number_list[0].strip() else 0
        if number.__contains__('.'):
            fragment = number_list[1].strip() + '0' * self._trinity_coef
            fragment = int(fragment[0:8])
        else:
            fragment = 0

        # calulate
        self.number = integer * pow(10, self._trinity_coef) + fragment

    @trinity_operator
    def add(self, number):
        """

        :param number:
        :return:
        """
        return self.number + number.number

    @trinity_operator
    def substract(self, number):
        """

        :param number:
        :return:
        """
        return self.number - number.number

    def cmp(self, number):
        if self.number > number.number:
            return 1
        elif self.number > number.number:
            return 0
        else:
            return -1

    @staticmethod
    @trinity_operator
    def restore_number(number):
        return number

    @classmethod
    def convert_to_number(cls, number, asset_type='TNC'):
        return int(number) / cls._trinity_unit


