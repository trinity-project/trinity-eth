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
from websocket import create_connection, \
    WebSocketConnectionClosedException, \
    WebSocketTimeoutException
from threading import Lock
import socket
import json
import time
from enum import Enum
from common.coroutine import ucoro, ucoro_event
from blockchain.interface import get_block_count
from common.log import LOG
from trinity import EVENT_WS_SERVER
from common.singleton import SingletonClass
from wallet.event import event_machine, EnumEventAction
from wallet.event.offchain_event import ChannelEndSettleEvent, \
    ChannelUpdateSettleEvent


class EnumChainEventReq(Enum):
    init = 'init',
    monitorTx = 'monitorTx',
    monitorBlockHeight = 'monitorBlockHeight',
    monitorDeposit = '',
    monitorUpdateDeposit = 'monitorUpdateDeposit',
    monitorQuickCloseChannel = 'monitorQuickCloseChannel',
    monitorCloseChannel = 'monitorCloseChannel',
    monitorSettle = 'monitorSettle'


class EnumChainEventResp(Enum):
    initResponse = 'initResponse',
    monitorTxResponse = 'monitorTxResponse',
    monitorBlockHeightResponse = 'monitorBlockHeightResponse',
    monitorDepositResponse = 'monitorDepositResponse',
    monitorUpdateDepositResponse = 'monitorUpdateDepositResponse',
    monitorQuickCloseChannelResponse = 'monitorQuickCloseChannelResponse',
    monitorCloseChannelResponse = 'monitorCloseChannelResponse',
    monitorSettleResponse = 'monitorSettleResponse'


class WebSocketConnection(metaclass=SingletonClass):
    """

    """
    _websocket_listening = True
    def __init__(self, uri=None, timeout=5):
        """"""
        self.__ws_url = EVENT_WS_SERVER.get('uri') if not uri else uri
        self.timeout = EVENT_WS_SERVER.get('timeout') if not timeout else timeout
        self.wallet = None
        self.wallet_address = None

        # create connection
        self._conn = None
        self.create_client()

        # queue
        self.__monitor_queue = {}
        self.event_lock = Lock()

    def set_timeout(self, timeout=0.2):
        self.timeout = timeout

    def stop_websocket(self):
        WebSocketConnection._websocket_listening = False
        self.close()

    def set_wallet(self, wallet):
        if wallet:
            self.wallet = wallet
            self.wallet_address = wallet.address

    def notify_wallet_info(self):
        payload = {
            'messageType': 'init',
            'walletAddress': self.wallet_address
        }

        self.send(json.dumps(payload))

    def create_client(self, retry=False):
        try:
            self._conn = create_connection(self.__ws_url,
                                           sockopt=((socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
                                                    (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),),
                                           timeout=self.timeout)
        except Exception as error:
            LOG.error('Connect to server error. {}'.format(error))
        else:
            if self.wallet_address and retry:
                self.notify_wallet_info()
                pass

    def send(self, payload):
        try:
            self._conn.send(payload)
        except WebSocketConnectionClosedException as error:
            LOG.error('send: Websocket was closed: {}'.format(error))
            self.reconnect()
            # re-send this payload
            if self._conn:
                self._conn.send(payload)
        except Exception as error:
            LOG.error('send: Websocket exception: {}'.format(error))

    def receive(self):
        try:
            return self._conn.recv()
        except WebSocketConnectionClosedException as error:
            LOG.error('receive: Websocket was closed: {}'.format(error))
            self.reconnect()

            return self._conn.recv() if self._conn else None
        except WebSocketTimeoutException as error:
            pass
        except Exception as error:
            if not self._conn:
                self.reconnect()
            LOG.error('receive: Websocket exception: {}'.format(error))

        return None

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def reconnect(self, retry = 5):
        self.close()

        count = 0
        while count < retry:
            self.create_client(True)
            if self._conn:
                break

            time.sleep(2)
            count += 1

    def handle(self):
        """

        :return:
        """
        old_block = get_block_count() - 1
        _event_coroutine = self.timer_event()
        next(_event_coroutine)
        self.prepare_handle_event()

        while WebSocketConnection._websocket_listening:
            try:
                response = self.receive()
                block_height = get_block_count()

                # handle response
                self.handle_event(block_height, response)

                # handle timer event
                if old_block != block_height:
                    for block in range(old_block+1, block_height+1):
                        ucoro_event(_event_coroutine, block)

                    # set new value to old_block
                    old_block = block_height

                time.sleep(0.5)
            except Exception as error:
                LOG.debug('websocket handle: {}'.format(error))
                time.sleep(1)

        ucoro_event(_event_coroutine, None)

    def handle_event(self, block_height, received = None):
        if not received:
            return

        try:
            message = json.loads(received)
            message_type = message.get('messageType')
        except Exception:
            message = received
            message_type = None
        finally:
            # start to handle the event
            if EnumChainEventResp.__dict__.__contains__(message_type):
                LOG.info('Handle message<{}> status <{}> at block<{}>.'.format(message_type, message.get('state'), block_height))
            elif EnumChainEventReq.__dict__.__contains__(message_type):
                LOG.info('Handle message<{}> at block<{}>'.format(message_type, block_height))
                self.__getattribute__(message_type)(message)
            else:
                LOG.info('MessageType: {}. Test or invalid message: {} at block<{}>'.format(message_type, message, block_height))

    @ucoro(0.2)
    def timer_event(self, received=None):
        if not received:
            return
        LOG.debug('Handle timer event at block<{}>'.format(received))

        event_list = self.get_event(received)
        for event in event_list:
            # move this event to event machine
            event_machine.register_event(event.channel_name, event)
            event_machine.trigger_start_event(event.channel_name)
            # event.execute(received)

    def prepare_handle_event(self):
        pass

    def register_event(self, event, end_block=None):

        if not end_block:
            block_height = get_block_count() + 1
        else:
            block_height = end_block

        self.event_lock.acquire()
        event_list = self.__monitor_queue.get(block_height, [])
        event_list.append(event)
        self.__monitor_queue.update({block_height:event_list})
        self.event_lock.release()

    def get_event(self, key):
        self.event_lock.acquire()
        event =  self.__monitor_queue.pop(key, [])
        self.event_lock.release()

        return event

    def monitorTx(self):
        pass

    def monitorBlockHeight(self):
        pass

    def monitorDeposit(self):
        pass

    def monitorUpdateDeposit(self):
        pass

    def monitorQuickCloseChannel(self):

        pass

    def monitorCloseChannel(self, message):
        """

        :param message:
        :return:

        message like below format:
            {
                'playload': '0xabf328663edff39bfa3f157556afa52bdcb14fda32d35c70e6e3386e954e7995',
                'txId': '0xc0461c9a92a295eec4dd1060e4abd34bbb1c8139e2b9bc5e35e7c2daa1dccfc5',
                'channelId': '0xabf328663edff39bfa3f157556afa52bdcb14fda32d35c70e6e3386e954e7995',
                'invoker': '0x23cca051bfedb5e17d3aad2038ba0a5155d1b1b7',
                'nounce': 5,
                'blockNumber': 3924231,
                'messageType': 'monitorCloseChannel'
            }

        """
        if not message:
            LOG.error('Invalid message: {}'.format(message))
            return
        try:
            invoker = message.get('invoker').strip()
            channel_name = message.get('channelId')
            nonce = message.get('nounce')
            end_time = int(message.get('blockNumber'))
        except Exception as error:
            LOG.error('Invalid message: {}. Exception: {}'.format(message, error))
        else:
            if not (self.wallet_address and invoker):
                LOG.error('Wallet address<{}> or invoker<{}> should not be none'.format(self.wallet_address, invoker))
                return

            if invoker != self.wallet_address:
                channel_event = ChannelUpdateSettleEvent(channel_name)
                channel_event.register_args(EnumEventAction.EVENT_EXECUTE,
                                            self.wallet.url, channel_name, self.wallet._key.private_key_string)
                event_machine.trigger_start_event(channel_name)
            else:
                channel_event = ChannelEndSettleEvent(channel_name)
                channel_event.register_args(EnumEventAction.EVENT_EXECUTE,
                                            invoker, channel_name, self.wallet._key.private_key_string)
                self.register_event(channel_event, end_time)

        pass

    def monitorSettle(self):
        pass


ws_instance = WebSocketConnection()
