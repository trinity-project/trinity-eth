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


class TrinityException(Exception):
    """
    Description: Basic exception definition for Trinity SW.
        Generally, this exception include 2 parts: error code and messages.

        RECOMMEND to use enum type to define the error code.
        Thus any developers could define his own error code and could be used
        by others.

        If do so, developers could use the error code to control the SW's logic.
        And it will make the debug and maintenance become easier, etc.

    Examples:
         class EnumState(IntEnum):
            STATE_NOT_FOUND = 0x01
            STATE_IS_INCOMPATIBLE = 0x02

        try:
            state = 'error'
            raise TrinityException(
                EnumState.STATE_NOT_FOUND,
                'State<{}> not found.'.format(state)
            )
        except Exception as error:
            status = error.reason
            logging.debug(error)
    """

    def __str__(self):
        return str(self.args[-1]) if 0 < len(self.args) else ''

    reason = property(lambda self: self.args[0])
