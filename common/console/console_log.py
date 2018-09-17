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
from __future__ import unicode_literals, print_function
from prompt_toolkit import print_formatted_text, ANSI
import sys


class ConsoleLog(object):
    """
    for Linux or MacOS
    """
    def __init__(self):
        self._fg_red = '\x1b[31m{}'
        self._fg_green = '\x1b[32m{}'
        self._fg_yellow = '\x1b[33m{}'

        pass

    def console(self, *args):
        print(*args)

    def sample_print(self, *args):
        print(" ".join([str(i).replace("\r"," ").replace("\n", " ") for i in args]))

    def error(self, *args):
        if sys.stdout.isatty():
            print_formatted_text(ANSI(self._fg_red.format(self.text(*args))))
        else:
            self.sample_print(*args)


    def info(self, *args):
        if sys.stdout.isatty():
            print_formatted_text(ANSI(self._fg_green.format(self.text(*args))))
        else:
            self.sample_print(*args)

    def warning(self, *args):
        if sys.stdout.isatty():
            print_formatted_text(ANSI(self._fg_yellow.format(self.text(*args))))
        else:
            self.sample_print(*args)

    def warn(self, value):
        self.warning(value)

    @staticmethod
    def text(*args):
        """

        :param args:
        :return:
        """
        output = ''
        for info in args:
            output += '{} '.format(info)

        return output.strip()


console_log = ConsoleLog()

