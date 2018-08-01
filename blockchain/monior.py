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
from websocket import create_connection, WebSocketConnectionClosedException, WebSocketTimeoutException
from threading import Lock
import socket
import time
import json

from blockchain.interface import get_block_count, get_block
from log.log import LOG


WS_SERVER_CONFIG = {'ip': '47.104.81.20', 'port': 9000}
EVENT_MESSAGE_TYPE = ['init',
                      'monitorTx',
                      'monitorBlockHeight',
                      'monitorDeposit',
                      'monitorUpdateDeposit',
                      'monitorQuickCloseChannel',
                      'monitorCloseChannel',
                      'monitorCloseChannel',
                      'monitorSettle'
                      ]
EVENT_RESPONSE_TYPE = ['initResponse',
                      'monitorTxResponse',
                      'monitorBlockHeightResponse',
                      'monitorDepositResponse',
                      'monitorUpdateDepositResponse',
                      'monitorQuickCloseChannelResponse',
                      'monitorCloseChannelResponse',
                      'monitorCloseChannelResponse',
                      'monitorSettleResponse'
                      ]


def singleton(cls):
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton


def ucoro(timeout = 0.1):
    def handler(callback):
        def wrapper(*args, **kwargs):
            # use such mode to modulate blocking-mode to received
            while True:
                try:
                    received = yield
                    if received in ['exit']:
                        break

                    callback(*args, received, **kwargs)
                except Exception as error:
                    LOG.error('Co-routine received<{}>, error: {}'.format(received, error))
                finally:
                    time.sleep(timeout)

        return wrapper
    return handler


def ucoro_event(coro, iter_data):
    try:
        coro.send(iter_data)
    except StopIteration:
        print('Coroutine has been killed')


@singleton
class WebSocketConnection(object):
    """

    """
    def __init__(self, ip, port, timeout=0.2):
        assert ip, 'Must specified the server ip<{}>.'.format(ip)
        assert port, 'Must specified the server port<{}>.'.format(port)

        self.__ws_url = 'ws://{}:{}'.format(ip, port)
        self.timeout = timeout

        self.__event_queue = {}
        self.event_queue_lock = Lock()
        self.__event_ready_queue = {}
        self.__event_monitor_queue = {}

        self.wallet_address = None

        # create connection
        self.create_client()

    def set_timeout(self, timeout=0.2):
        self.timeout = timeout

    def set_wallet(self, wallet_address):
        self.wallet_address = wallet_address

    def notify_wallet_info(self):
        payload = {
            'messageType': 'init',
            'walletAddress': self.wallet_address
        }

        self.send(json.dumps(payload))

    def create_client(self):
        try:
            self._conn = create_connection(self.__ws_url,
                                           sockopt=((socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
                                                    (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),),
                                           timeout=self.timeout)
        except Exception as error:
            LOG.error('Connect to server error. {}'.format(error))
        else:
            if self.wallet_address:
                self.notify_wallet_info()
                pass

    def send(self, payload):
        try:
            self._conn.send(payload)
        except WebSocketConnectionClosedException as error:
            LOG.error('send: Websocket was closed: {}'.format(error))
            self.reconnect()
            # re-send this payload
            self._conn.send(payload)
        except Exception as error:
            LOG.exception('send: Websocket exception: {}'.format(error))

    def receive(self):
        try:
            return self._conn.recv()
        except WebSocketConnectionClosedException as error:
            LOG.error('receive: Websocket was closed: {}'.format(error))
            self.reconnect()
            return self._conn.recv()
        except WebSocketTimeoutException as error:
            pass
        except Exception as error:
            if not self._conn:
                self.reconnect()
            LOG.exception('receive: Websocket exception: {}'.format(error))

        return None

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def reconnect(self):
        self.close()
        self.create_client()

    def register_event(self, key, event):
        self.event_queue_lock.acquire()
        self.__event_queue.update({key: event})
        self.event_queue_lock.release()

    def get_event(self, key):
        return self.__event_queue.get(key)

    @ucoro(0.1)
    def handle(self, *args):
        # assert args, 'Received Invalid message<{}>.'.format(args)
        # message = args[0]
        # assert message, 'Received void message<{}>.'.format(args)
        LOG.debug(args)

        message = self.receive()
        LOG.debug('connection: {} Received: {}.'.format(self._conn, message))
        if message:
            message = json.loads(message)
            message_type = message.get('messageType')

            # start to handle the event
            if message_type in EVENT_RESPONSE_TYPE:
                LOG.info('Handle message<{}> status <{}>.'.format(message_type, message.get('state')))
            elif message_type in EVENT_MESSAGE_TYPE:
                self.handle_message(message)
            else:
                LOG.info('Test message or invalid message {}'.format(message))

    def handle_message(self, message):
        message_type = message.get('messageType')
        channel_id = message.get('channelId')
        if not channel_id:
            LOG.info('Handle message<{}> failed'.format(message_type))
            return

        channel_event = self.__event_monitor_queue.get(channel_id)
        if not channel_event:
            LOG.error('No event for channel<{}>.'.format(channel_id))
            return
        channel_event.terminate()

        # remove from the queue
        self.__event_monitor_queue.pop(channel_id)

    def pre_execution(self):
        try:
            self.event_queue_lock.acquire()
            keys_list = list(self.__event_queue.keys())
            for key in keys_list:
                if self.__event_queue[key].event_is_ready:
                    self.__event_ready_queue[key] = self.__event_queue.pop(key)
            self.event_queue_lock.release()

            event = self.__event_ready_queue.popitem()
        except:
            return
        else:
            event_action = event[1]
            if not event_action:
                LOG.error('Why no action is set? action<{}>'.format(event_action))
                return

            prepare_result = event_action.prepare()
            if event_action.depend_on_prepare:
                if all(prepare_result):
                    event_action.action()
            else:
                event_action.action()

            if event_action.finish_preparation:
                self.__event_monitor_queue.update(dict([event]))
            else:
                self.__event_ready_queue.update(dict([event]))


ws_instance = WebSocketConnection(WS_SERVER_CONFIG.get('ip'), WS_SERVER_CONFIG.get('port'))


class EventMonitor(object):
    GoOn = True
    Wallet = None
    Wallet_Change = None
    BlockHeight = None
    BlockPause = False

    @classmethod
    def stop_monitor(cls):
        cls.GoOn = False

    @classmethod
    def start_monitor(cls, wallet):
        cls.Wallet = wallet
        cls.Wallet_Change = True

        if wallet:
            try:
                ws_instance.set_wallet(wallet.address)
            except Exception as error:
                print('No wallet is opened')
                pass

    @classmethod
    def update_wallet_block_height(cls, height):
        if cls.Wallet_Change:
            return None
        if cls.Wallet:
            cls.Wallet.BlockHeight=height
        else:
            return None

    @classmethod
    def get_wallet_block_height(cls):
        if cls.Wallet:
            block_height = cls.Wallet.BlockHeight
            cls.Wallet_Change = False
            return block_height if block_height else 1
        else:
            return 1

    @classmethod
    def update_block_height(cls, blockheight):
        cls.BlockHeight = blockheight

    @classmethod
    def get_block_height(cls):
        return cls.BlockHeight if cls.BlockHeight else 1


def monitorblock():
    event_coro = ws_instance.handle()
    next(event_coro)

    while EventMonitor.GoOn:
        blockheight_onchain = get_block_count()
        EventMonitor.update_block_height(blockheight_onchain)

        blockheight = EventMonitor.get_wallet_block_height()

        block_delta = int(blockheight_onchain) - int(blockheight)

        # execute prepare and action
        ws_instance.pre_execution()
        ucoro_event(event_coro, blockheight)
        # result = ws_instance.receive()
        # if result:
        #     ucoro_event(event_coro, result)

        if 0 < block_delta:
            try:
                if block_delta < 2000:
                    if EventMonitor.BlockPause:
                        pass
                    else:
                        blockheight += 1
                else:
                    blockheight +=1000
                    pass
                EventMonitor.update_wallet_block_height(blockheight)
            except Exception as e:
                pass
        else:
            #LOG.debug("Not get the blockheight")
            pass

        if blockheight < blockheight_onchain:
            #time.sleep(0.1)
            pass
        else:
            time.sleep(15)

    # stop monitor
    ucoro_event(event_coro, 'exit')


def register_monitor(*args):
    pass


def register_block(*args):
    pass











