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
import time
from common.log import LOG


def ucoro(timeout=0.1, once=False):
    def handler(callback):
        def wrapper(*args, **kwargs):
            received = None
            # use such mode to modulate blocking-mode to received
            while True:
                try:
                    received = yield
                    if received in ['exit', None]:
                        break

                    kwargs.update({'received': received})
                    callback(*args, **kwargs)
                except Exception as error:
                    LOG.exception('Co-routine received<{}>, error: {}'.format(received, error))
                finally:
                    # only run once time
                    if once:
                        break

                    time.sleep(timeout)

        return wrapper
    return handler


def ucoro_event(coro, iter_data):
    try:
        coro.send(iter_data)
    except StopIteration as error:
        LOG.debug('Co-routine has been killed.')
    except Exception as error:
        LOG.exception('Error occurred during using co-routine. error: {}'.format(error))
