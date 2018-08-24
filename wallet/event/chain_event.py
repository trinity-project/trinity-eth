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
import socket
import json
import time
from enum import IntEnum
from common.coroutine import ucoro, ucoro_event
from common.log import LOG
from trinity import EVENT_WS_SERVER


class EnumChainEventReq(IntEnum):
    init = 'init',
    monitorTx = 'monitorTx',
    monitorBlockHeight = 'monitorBlockHeight',
    monitorDeposit = '',
    monitorUpdateDeposit = 'monitorUpdateDeposit',
    monitorQuickCloseChannel = 'monitorQuickCloseChannel',
    monitorCloseChannel = 'monitorCloseChannel',
    monitorSettle = 'monitorSettle'


class EnumChainEventResp(IntEnum):
    initResponse = 'initResponse',
    monitorTxResponse = 'monitorTxResponse',
    monitorBlockHeightResponse = 'monitorBlockHeightResponse',
    monitorDepositResponse = 'monitorDepositResponse',
    monitorUpdateDepositResponse = 'monitorUpdateDepositResponse',
    monitorQuickCloseChannelResponse = 'monitorQuickCloseChannelResponse',
    monitorCloseChannelResponse = 'monitorCloseChannelResponse',
    monitorSettleResponse = 'monitorSettleResponse'


class WebSocketConnection(object):
    """

    """
    def __init__(self):
        """"""
        self.__ws_url = EVENT_WS_SERVER.get('uri')
        self.timeout = EVENT_WS_SERVER.get('timeout')
        self.wallet_address = None

        # create connection
        self._conn = None
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
            self.create_client()
            if self._conn:
                break

            time.sleep(2)
            count += 1

    def handle(self, *args):
        # co-routine handle????
        coro_handler = self.handle_event()
        next(coro_handler)

        try:
            while True:
                response = self.receive()
                if not response:
                    ucoro_event(coro_handler, json.loads(response))

                time.sleep(0.5)
        except Exception:
            pass
        finally:
            ucoro_event(coro_handler, 'exit')

    @ucoro()
    def handle_event(self, received = None):
        if not received:
            LOG.warn('Why send NoneType message to websocket co-routine handler.')
            return
        message_type = received.get('messageType')

        # start to handle the event
        if EnumChainEventResp.__dict__.__contains__(message_type):
            LOG.info('Handle message<{}> status <{}>.'.format(message_type, received.get('state')))
        elif EnumChainEventReq.__dict__.__contains__(message_type):
            self.__getattribute__(message_type)(received)
        else:
            LOG.info('MessageType: {}. Test or invalid message: {}'.format(message_type, received))


def eth_websocket(callback):
    def wrapper(*args, **kwargs):
        try:
            payload = callback(*args, **kwargs)
            if not payload.get('walletAddress'):
                payload.update({'walletAddress': ws_instance.wallet_address})
        except Exception as error:
            LOG.error('Call {} error: {}'.format(callback.__name__, error))
        else:
            # to send the data by wwebsocket connection
            ws_instance.send(json.dumps(payload))
    return wrapper


@eth_websocket
def event_init_wallet(wallet_address):
    assert wallet_address, 'Invalid wallet address<{}>'.format(wallet_address)

    payload = {
        'messageType': 'init',
        'walletAddress': wallet_address}

    return payload


@eth_websocket
def event_monitor_tx(tx_id, asset_type='TNC', comments={}):
    assert tx_id, 'Invalid tx_id<{}>.'.format(tx_id)
    assert asset_type, 'Invalid asset_type <{}>.'.format(asset_type)

    payload = {
        'messageType': 'monitorTx',
        'chainType': asset_type.upper(),
        'playload': tx_id,
        'comments': comments
    }

    return payload


@eth_websocket
def event_monitor_height(height, asset_type='TNC', comments={}):
    assert isinstance(height, int), 'Invalid height<{}>.'.format(height)
    assert asset_type, 'Invalid asset_type <{}>.'.format(asset_type)

    payload = {
        'messageType': 'monitorBlockHeight',
        'chainType': asset_type.upper(),
        'playload': height,
        'comments': comments
    }

    return payload


ws_instance = WebSocketConnection()

@eth_websocket
def event_monitor_deposit(channel_id, asset_type='TNC', comments={}):
    """

    :param channel_id: channel's name
    :param asset_type:
    :param comments:
    :return:
    """
    assert channel_id, 'Invalid channel_id<{}>.'.format(channel_id)
    assert asset_type, 'Invalid asset_type <{}>.'.format(asset_type)

    payload = {
        'messageType': 'monitorDeposit',
        'chainType': asset_type.upper(),
        'playload': channel_id,
        'comments': comments
    }

    return payload


@eth_websocket
def event_monitor_update_deposit(channel_id, asset_type='TNC', comments={}):
    assert channel_id, 'Invalid channel_id<{}>.'.format(channel_id)
    assert asset_type, 'Invalid asset_type <{}>.'.format(asset_type)

    payload = {
        'messageType': 'monitorUpdateDeposit',
        'chainType': asset_type.upper(),
        'playload': channel_id,
        'comments': comments
    }

    return payload


@eth_websocket
def event_monitor_quick_close_channel(channel_id, asset_type='TNC', comments={}):
    assert channel_id, 'Invalid channel_id<{}>.'.format(channel_id)
    assert asset_type, 'Invalid asset_type <{}>.'.format(asset_type)

    payload = {
        'messageType': 'monitorQuickCloseChannel',
        'chainType': asset_type.upper(),
        'playload': channel_id,
        'comments': comments
    }

    return payload


@eth_websocket
def event_monitor_close_channel(channel_id, asset_type='TNC', comments={}):
    assert channel_id, 'Invalid tx_id<{}>.'.format(channel_id)
    assert asset_type, 'Invalid asset_type <{}>.'.format(asset_type)

    payload = {
        'messageType': 'monitorCloseChannel',
        'chainType': asset_type.upper(),
        'playload': channel_id,
        'comments': comments
    }

    return payload


@eth_websocket
def event_monitor_settle(channel_id, asset_type='TNC', comments={}):
    assert channel_id, 'Invalid tx_id<{}>.'.format(channel_id)
    assert asset_type, 'Invalid asset_type <{}>.'.format(asset_type)

    payload = {
        'messageType':'monitorSettle',
        'chainType': asset_type.upper(),
        'playload': channel_id,
        'comments': comments
    }

    return payload


@eth_websocket
def event_test_state():
    payload = {
        'messageType':'state'
    }

    return payload
