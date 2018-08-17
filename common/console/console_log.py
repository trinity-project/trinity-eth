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
import platform


__platform__ = platform.system().upper() if platform.system() else 'LINUX'


class ConsoleLogBase(object):
    """

    """
    def __init__(self):
        pass

    def debug(self, value):
        print()

    def error(self, value):
        pass

    def info(self, value):
        pass

    def warning(self, value):
        pass

    def warn(self, value):
        pass

    def _log(self, color, value):
        pass

    def _set_cmd_color(self, color):
        pass

    def _reset_color(self):
        pass

if __platform__.__contains__('WINDOWS'):
    import ctypes
    print('WINDOWS')

    class ConsoleLog(ConsoleLogBase):
        """
         In windows, the system will use the three-primary colours to control the display colours,
         here, we define this set here to control the text's colour.
        """
        def __init__(self):

            self._fg_blue = 0x1
            self._fg_green = 0x2
            self._fg_red = 0x4
            self._fg_intensity = 0x8

            self._std_out_handle = ctypes.windll.kernel32.GetStdHandle(-11)
            pass

        def error(self, value):
            self._log(self._fg_red | self._fg_intensity, value)

        def info(self, value):
            self._log(self._fg_green | self._fg_intensity, value)

        def warning(self, value):
            self._log(self._fg_red | self._fg_green | self._fg_intensity, value)

        def warn(self, value):
            self.warning(value)

        def _log(self, color, value):
            self._set_cmd_color(color)
            print(value)
            self._reset_color()

        def _set_cmd_color(self, color):
            return ctypes.windll.kernel32.SetConsoleTextAttribute(self._std_out_handle, color)

        def _reset_color(self):
            self._set_cmd_color(self._fg_red | self._fg_green | self._fg_blue)

else:
    # default Linux system
    class ConsoleLog(ConsoleLogBase):
        """
        for Linux or MacOS
        """
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


console_log = ConsoleLog()

