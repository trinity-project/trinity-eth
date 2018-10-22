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
import json
from common.log import LOG
from wallet.connection.websocket import ws_instance


def eth_websocket(callback):
    def wrapper(*args, **kwargs):
        try:
            payload = callback(*args, **kwargs)
            payload.update({'chainType': 'ETH'})
            if not payload.get('walletAddress'):
                payload.update({'walletAddress': ws_instance.wallet_address})
        except Exception as error:
            LOG.error('Call {} error: {}'.format(callback.__name__, error))
        else:
            # to send the data by wwebsocket connection
            LOG.debug('Register event<{}> to full-node'.format(payload))
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
def event_monitor_tx(tx_id, comments={}):
    assert tx_id, 'Invalid tx_id<{}>.'.format(tx_id)

    payload = {
        'messageType': 'monitorTx',
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


def monitor_channel_event(message_type, channel_id, comments={}):
    """

    :param message_type:
    :param channel_id: which channel name will be used to monitor
    :param asset_type: legal asset type should be in ['TNC', 'ETH'] currently
    :param comments:
    :return:
    """
    assert message_type, 'Invalid message_type<{}>.'.format(message_type)
    assert channel_id, 'Invalid channel_id<{}>.'.format(channel_id)

    return {
        'messageType': message_type,
        'playload': channel_id,
        'comments': comments
    }


@eth_websocket
def event_monitor_deposit(channel_id, comments={}):
    """ refer to details of monitor_channel_event"""
    payload = monitor_channel_event('monitorDeposit', channel_id, comments)
    return payload


@eth_websocket
def event_monitor_update_deposit(channel_id, comments={}):
    """ refer to details of monitor_channel_event"""
    payload = monitor_channel_event('monitorUpdateDeposit', channel_id, comments)
    return payload


@eth_websocket
def event_monitor_quick_close_channel(channel_id, comments={}):
    """ refer to details of monitor_channel_event"""
    payload = monitor_channel_event('monitorQuickCloseChannel', channel_id, comments)
    return payload


@eth_websocket
def event_monitor_close_channel(channel_id, comments={}):
    """ refer to details of monitor_channel_event"""
    payload = monitor_channel_event('monitorCloseChannel', channel_id, comments)
    return payload


@eth_websocket
def event_monitor_settle(channel_id, comments={}):
    """ refer to details of monitor_channel_event"""
    payload = monitor_channel_event('monitorSettle', channel_id, comments)
    return payload


@eth_websocket
def event_monitor_withdraw(channel_id, comments={}):
    """ refer to details of monitor_channel_event"""
    payload = monitor_channel_event('monitorWithdraw', channel_id, comments)
    return payload


@eth_websocket
def event_monitor_withdraw_update(channel_id, comments={}):
    """ refer to details of monitor_channel_event"""
    payload = monitor_channel_event('monitorWithdrawUpdate', channel_id, comments)
    return payload


@eth_websocket
def event_monitor_withdraw_settle(channel_id, comments={}):
    """ refer to details of monitor_channel_event"""
    payload = monitor_channel_event('monitorWithdrawSettle', channel_id, comments)
    return payload


@eth_websocket
def event_cannel_monitor(channel_id, monitor_type, comments={}):
    """ refer to details of monitor_channel_event"""
    payload = monitor_channel_event('cancelMonitor', channel_id, comments)
    payload.update({'monitoryType': monitor_type})
    return payload


@eth_websocket
def event_test_state():
    payload = {
        'messageType':'state'
    }

    return payload
