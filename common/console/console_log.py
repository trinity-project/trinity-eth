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


<<<<<<< HEAD
__platform__ = platform.system().upper() if platform.system() else 'LINUX'

__platform__='Windows'
class ConsoleLogBase(object):
=======
class ConsoleLog(object):
>>>>>>> dev
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

    def error(self, *args):
        print_formatted_text(ANSI(self._fg_red.format(self.text(*args))))

    def info(self, *args):
        print_formatted_text(ANSI(self._fg_green.format(self.text(*args))))

    def warning(self, *args):
        print_formatted_text(ANSI(self._fg_yellow.format(self.text(*args))))

    def warn(self, value):
        self.warning(value)

    @staticmethod
    def text(*args):
        """

        :param args:
        :return:
        """
<<<<<<< HEAD
        def __init__(self):
            self._fg_red = '\033[0;31;0m{}\033[0m'
            self._fg_green = '\033[0;32;0m{}\033[0m'
            self._fg_yellow = '\033[0;33;0m{}\033[0m'

            pass

        def error(self, *args):
            print('\033[0;31;0m', *args, '\033[0m')

        def info(self, *args):
            print('\033[0;32;0m', *args, '\033[0m')

        def warning(self, *args):
            print('\033[0;33;0m', *args, '\033[0m')

        def warn(self, value):
            self.warning(value)
=======
        output = ''
        for info in args:
            output += '{} '.format(info)

        return output.strip()
>>>>>>> dev


console_log = ConsoleLog()

