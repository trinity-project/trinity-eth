# --*-- coding : utf-8 --*--
"""Author: Trinity Core Team

MIT License

Copyright (c) 2018 Trinity

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the 'Software'), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
import json

from .monior import ws_instance
from common.log import LOG


def eth_websocket(callback):
    def wrapper(*args, **kwargs):
        try:
            payload = callback(*args, **kwargs)
            if not payload.get('walletAddress'):
                payload.update({'walletAddress': ws_instance.wallet_address})
        except Exception as error:
            LOG.exception('Call {} error: {}'.format(callback.__name__, error))
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