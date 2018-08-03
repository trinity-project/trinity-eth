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
import hashlib
import time
from enum import Enum, IntEnum
from model.channel_model import APIChannel
from model.base_enum import EnumChannelState
from model.transaction_model import APITransaction
from wallet.TransactionManagement import message as mg
from wallet.utils import convert_number_auto
from wallet.Interface.gate_way import sync_channel
from common.log import LOG
import json

from blockchain.ethInterface import Interface as EthInterface
from blockchain.web3client import Client as EthWebClient
from lightwallet.Settings import settings
from blockchain.event import *


class Channel(object):
    """

    """
    _interface = None
    _web3_client = None
    _trinity_coef = pow(10, 8)

    def __init__(self, founder, partner):
        self.founder = founder
        self.partner = partner
        self.founder_address = self.founder.strip().split("@")[0]
        self.partner_address = self.partner.strip().split("@")[0]
        self.channel_set = None

    @staticmethod
    def get_channel(address1, address2, state=None):
        channels = []
        filter1 = {"src_addr": address1, "dest_addr": address2, "state": state} if state \
            else {"src_addr": address1, "dest_addr": address2}

        filter2 = {"src_addr": address2, "dest_addr": address1, "state": state} if state \
            else {"src_addr": address2, "dest_addr": address1}

        channel = APIChannel.batch_query_channel(filters=filter1)
        if channel.get("content"):
            channels.extend(channel["content"])

        channel = APIChannel.batch_query_channel(filters=filter2)
        if channel.get("content"):
            channels.extend(channel["content"])

        return channels

    @staticmethod
    def query_channel(address):
        print("Get Channels with Address %s" % address)
        channels = APIChannel.batch_query_channel(filters={"src_addr": address})
        if channels.get("content"):
            for ch in channels["content"]:
                print("==" * 10, "\nChannelName:", ch.channel, "\nState:", ch.state, "\nPeer:", ch.dest_addr,
                      "\nBalance:", json.dumps(ch.balance, indent=1))
        channeld = APIChannel.batch_query_channel(filters={"dest_addr": address})
        if channeld.get("content"):
            for ch in channeld["content"]:
                print("==" * 10, "\nChannelName:", ch.channel, "\nState:", ch.state, "\nPeer:", ch.src_addr,
                      "\nBalance:", json.dumps(ch.balance, indent=1))

    @classmethod
    def channel(cls,channelname):
        try:
            channel = APIChannel.query_channel(channel=channelname)
            cls.channel_set = channel["content"][0]
        except Exception as e:
            LOG.error(e)
            return None
        ch = cls(cls.channel_set.src_addr, cls.channel_set.dest_addr)
        ch.channel_set = cls.channel_set
        ch.channel_name = channelname
        return ch

    def create(self, asset_type, deposit, partner_deposit = None, cli=True, comments=None, channel_name=None, wallet = None):
        if not partner_deposit:
            partner_deposit = deposit

        if Channel.get_channel(self.founder_address, self.partner_address):
            print("Channel already exist")
            return False

        self.start_time = time.time()
        self.asset_type = asset_type
        self.deposit = {}
        subitem = {}
        subitem.setdefault(asset_type, deposit)
        self.deposit[self.founder_address] = subitem

        subitem.setdefault(asset_type, partner_deposit)
        self.deposit[self.partner_address] = subitem
        self.channel_name = self.__new_channel()

        if cli:
            deposit = convert_number_auto(asset_type.upper(), deposit)
            partner_deposit = convert_number_auto(asset_type.upper(), partner_deposit)
            if 0 >= deposit or 0 >= partner_deposit:
                LOG.error('Could not trigger register channel because of illegal deposit<{}:{}>.'.format(deposit, partner_deposit))
                return False

            try:
                mg.FounderMessage.create(self.channel_name, self.founder, self.partner, asset_type,
                                     deposit, partner_deposit, mg.Message.get_magic(), wallet=wallet)
            except Exception as error:
                LOG.info('Create channel<{}> failed'.format(self.channel_name))
                return False

        return True

    def delete(self):
        pass

    def update_channel(self, **kwargs):
        return APIChannel.update_channel(self.channel_name, **kwargs)

    def delete_channel(self):
        return APIChannel.delete_channel(self.channel_name)

    def add_channel(self, **kwargs):
        channel_name = kwargs.get('channel')
        if not channel_name:
            channel_name = self.__new_channel()
        kwargs.update({'channel': channel_name, 'alive_block': 0})
        return APIChannel.add_channel(**kwargs)

    def __new_channel(self):
        timestamp = time.time().__str__().encode()
        md5_part1 = hashlib.md5(self.founder.encode())
        md5_part1.update(timestamp)
        md5_part2 = hashlib.md5(self.partner.encode())
        md5_part2.update(timestamp)

        return '0x' + md5_part1.hexdigest().lower() + md5_part2.hexdigest().lower()

    @property
    def state(self):
        return None

    @property
    def src_addr(self):
        ch = self._get_channel()
        if ch:
            return ch.src_addr
        else:
            return None

    @property
    def dest_addr(self):
        ch = self._get_channel()
        if ch:
            return ch.dest_addr
        else:
            return None

    def _get_channel(self):
        try:
            channel = APIChannel.query_channel(self.channel_name)
            return channel["content"][0]
        except Exception as e:
            LOG.error(e)
            return None

    def get_balance(self):
        ch = self._get_channel()
        if ch:
            return ch.balance
        else:
            return None

    def get_peer(self, url):
        if self.founder == url:
            return self.partner
        elif self.partner == url:
            return self.founder
        else:
            return None

    def get_deposit(self):
        ch = self._get_channel()
        if ch:
            return ch.deposit
        else:
            return None

    def toJson(self):
        jsn = {"ChannelName": self.channel_name,
               "Founder": self.founder,
               "Parterner": self.partner,
               "State": self.state,
               "Deposit": self.get_deposit(),
               "Balance": self.get_balance()}
        return jsn

    def get_role_in_channel(self, url):
        if url == self.src_addr:
            return "Founder"
        elif url == self.dest_addr:
            return "Partner"
        else:
            return None

    @staticmethod
    def add_trade(channel_name, **kwargs):
        return APITransaction('transaction'+channel_name).add_transaction(**kwargs)

    @staticmethod
    def update_trade(channel_name, nonce, **kwargs):
        return APITransaction('transaction'+channel_name).update_transaction(nonce, **kwargs)

    @staticmethod
    def query_trade(channel_name, nonce, *args, **kwargs):
        return APITransaction('transaction'+channel_name).query_transaction(nonce, *args, **kwargs)

    @staticmethod
    def latest_trade(channel_name):
        try:
            trade = APITransaction('transaction' + channel_name).sort(key='nonce')[0]
        except Exception as error:
            LOG.error('No transaction records were found for channel<{}>. Exception: {}'.format(channel_name, error))
            return None
        else:
            return trade

    # transaction related
    def transfer(self, sender, receiver, asset_type, count, hash_random=None, wallet=None):
        """

        :param sender:
        :param receiver:
        :param asset_type:
        :param count:
        :param hash_random:
        :param wallet:
        :return:
        """
        try:
            channel = self.get_channel(sender, receiver, EnumChannelState.OPENED.name)[0]
        except Exception as error:
            # HTLC transaction
            pass
        else:
            # RSMC transaction
            mg.RsmcMessage.create(channel.channel, wallet, sender, receiver, count, asset_type, comments=hash_random)

        return

    @staticmethod
    def quick_close(wallet, channel_name):
        channel = Channel.channel(channel_name)

        try:
            if channel.channel_set:
                mg.SettleMessage.create(wallet, channel_name, channel.src_addr, channel.dest_addr, 'TNC')
            else:
                LOG.error('Could not close channel<{}> since channel not found.'.format(channel_name))
        except Exception as error:
            LOG.error('Could not close channel. error: {}.'.format(error))

        return

    @staticmethod
    def _eth_interface():
        if not Channel._interface:
            Channel._interface = EthInterface(settings.NODEURL,
                                             settings.Eth_Contract_address, settings.Eth_Contract_abi,
                                             settings.TNC, settings.TNC_abi)

        return Channel._interface

    @staticmethod
    def _eth_client():
        if not Channel._web3_client:
            Channel._web3_client = EthWebClient(settings.NODEURL)

        return Channel._web3_client

    @staticmethod
    def sign_content(start=3, *args, **kwargs):
        """

        :return:
        """
        typeList = args[0] if 0 < len(args) else kwargs.get('typeList')
        valueList = args[1] if 1 < len(args) else kwargs.get('valueList')
        privtKey = args[2] if 2 < len(args) else kwargs.get('privtKey')

        for idx in range(start, len(typeList)):
            if typeList[idx] in ['uint256']:
                valueList[idx] = Channel.multiply(valueList[idx])

        content = Channel._eth_client().sign_args(typeList, valueList, privtKey).decode()
        return '0x' + content

    @staticmethod
    def approve(address, deposit, private_key):
        approved_asset = Channel.get_approved_asset(address)
        try:
            if float(approved_asset) < float(deposit):
                Channel._eth_interface().approve(address, Channel.multiply(deposit), private_key)
            else:
                LOG.info('Has been approved asset count: {}'.format(approved_asset))
        except Exception as error:
            LOG.error('approve error: {}'.format(error))

    @staticmethod
    def get_approved_asset(address):
        try:
            return Channel._eth_interface().get_approved_asset(settings.TNC,
                                                                          settings.TNC_abi,
                                                                          address,
                                                                          settings.Eth_Contract_address)
        except Exception as error:
            LOG.error('approve_deposit error: {}'.format(error))
            return 0

    @staticmethod
    def approve_deposit(address, channel_id, nonce, founder, founder_amount, partner, partner_amount,
                founder_sign, partner_sign, private_key):
        try:
            Channel._eth_interface().deposit(address,channel_id, nonce,
                                             founder, Channel.multiply(founder_amount),
                                             partner, Channel.multiply(partner_amount),
                                             founder_sign, partner_sign, private_key)
        except Exception as error:
            LOG.error('approve_deposit error: {}'.format(error))

    @staticmethod
    def quick_settle(invoker, channel_id, nonce, founder, founder_balance,
                     partner, partner_balance, founder_signature, partner_signature, invoker_key):

        try:
            Channel._eth_interface().quick_close_channel(invoker, channel_id, nonce,
                                                         founder, Channel.multiply(founder_balance),
                                                         partner, Channel.multiply(partner_balance),
                                                         founder_signature, partner_signature, invoker_key)
        except Exception as error:
            LOG.error('quick_settle error: {}'.format(error))

    @staticmethod
    def multiply(asset_count):
        return int(asset_count * Channel._trinity_coef)

    @staticmethod
    def divide(asset_count):
        return asset_count / Channel._trinity_coef


class EventArgs(object):
    """

    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class EnumEventAction(Enum):
    prepare_event = 'prepare'
    action_event = 'action'
    terminate_event = 'terminate'


class EnumEventType(Enum):
    # both wallet are online
    EVENT_TYPE_DEPOSIT = 0x0
    EVENT_TYPE_RSMC = 0x04
    EVENT_TYPE_HTLC = 0x08
    EVENT_TYPE_QUICK_SETTLE = 0x0c

    # One of Both wallets is online
    EVENT_TYPE_SETTLE = 0x10


    # test event
    EVENT_TYPE_TEST_STATE = 0xE0


class ChannelEvent(object):
    """

    """
    def __init__(self, channel_name, asset_type, event_type):
        self.event_name = channel_name
        self.event_type = event_type

        self.channel_name = channel_name
        self.asset_type = asset_type.upper().strip()
        self.channel = Channel.channel(channel_name)

        self.event_is_ready = False
        self.depend_on_prepare = False
        self.finish_preparation = False
        self.is_founder = True

    def register(self, action_type, *args, **kwargs):
        self.is_valid_action(action_type)

        action_name = action_type.name

        LOG.debug('Start to register {}-{} event.'.format(self.event_type.name, action_name))
        self.__dict__.update({action_name: EventArgs(*args, **kwargs)})

    def set_event_ready(self, ready=True):
        LOG.debug('set event of channel<{}> ready'.format(self.channel_name))
        self.event_is_ready = ready

    def is_valid_action(self, action_type):
        assert EnumEventAction.__contains__(action_type), 'Invalid action_type<{}>.'.format(action_type)

    def prepare(self):
        LOG.debug('Start to execute prepare event')
        return [True]

    def action(self):
        LOG.debug('Start to execute action event')
        pass

    def terminate(self):
        LOG.debug('Start to execute terminate event')
        pass


class ChannelTestEvent(ChannelEvent):
    def action(self):
        event_test_state()


class ChannelDepositEvent(ChannelEvent):
    def __init__(self, channel_name, asset_type):
        super(ChannelDepositEvent, self).__init__(channel_name, asset_type, EnumEventType.EVENT_TYPE_DEPOSIT)
        self.depend_on_prepare = True

    def prepare(self):
        super(ChannelDepositEvent, self).prepare()
        if hasattr(self, EnumEventAction.prepare_event.name):
            length_of_args = len(self.prepare_event.args)
            address = self.prepare_event.args[0] if 1 <= length_of_args else self.prepare_event.kwargs.get('address')
            balance = self.prepare_event.args[1] if 2 <= length_of_args else self.prepare_event.kwargs.get('balance')
            peer_address = self.prepare_event.args[2] if 3 <= length_of_args else self.prepare_event.kwargs.get('peer_address')
            peer_balance = self.prepare_event.args[3] if 4 <= length_of_args else self.prepare_event.kwargs.get('peer_balance')

            try:
                # approved balance
                approved_balance = float(self.channel.get_approved_asset(address))
                peer_approved_balance = float(self.channel.get_approved_asset(peer_address))
                if 0 == approved_balance or 0 == peer_approved_balance:
                    return None, None

                LOG.debug('Approved asset: self<{}:{}>, peer<{}:{}>'.format(address, approved_balance,
                                                                            peer_address, peer_approved_balance))
                return approved_balance >= float(balance), peer_approved_balance >= float(peer_balance)
            except Exception as error:
                LOG.error('Action prepare exception: {}'.format(error))
                pass
        else:
            return True, True

        return None, None

    def action(self):
        super(ChannelDepositEvent, self).action()
        self.finish_preparation = True
        if hasattr(self, EnumEventAction.action_event.name):
            try:
                if self.is_founder:
                    self.channel.approve_deposit(*self.action_event.args, **self.action_event.kwargs)
            except Exception as error:
                pass
            else:
                # register monitor deposit event
                event_monitor_deposit(self.channel_name, self.asset_type)

    def terminate(self):
        super(ChannelDepositEvent, self).terminate()
        if hasattr(self, EnumEventAction.terminate_event.name):
            return self.channel.update_channel(**self.terminate_event.kwargs)


class ChannelQuickSettleEvent(ChannelEvent):
    def __init__(self, channel_name, asset_type):
        super(ChannelQuickSettleEvent, self).__init__(channel_name, asset_type, EnumEventType.EVENT_TYPE_QUICK_SETTLE)

    def action(self):
        super(ChannelQuickSettleEvent, self).action()
        self.finish_preparation = True
        if hasattr(self, EnumEventAction.action_event.name):
            if self.is_founder:
                self.channel.quick_settle(*self.action_event.args, **self.action_event.kwargs)

            # register monitor quick settle event
            event_monitor_quick_close_channel(self.channel_name, self.asset_type)

    def terminate(self):
        super(ChannelQuickSettleEvent, self).terminate()
        if hasattr(self, EnumEventAction.terminate_event.name):
            return self.channel.update_channel(**self.terminate_event.kwargs)


def create_channel(founder, partner, asset_type, depoist: float, partner_deposit = None, cli=True,
                   comments=None, channel_name=None, wallet = None):
    return Channel(founder, partner).create(asset_type, depoist, partner_deposit, cli, comments, channel_name, wallet= wallet)


def filter_channel_via_address(address1, address2, state=None):
    channel = Channel.get_channel(address1, address2, state)
    return channel


def get_channel_via_address(address):
    Channel.query_channel(address)
    return


def get_channel_via_name(params):
    print('enter get_channel_via_name', params)
    if params:
        print('params is ', params)
        channel_set = APIChannel.batch_query_channel(filters=params[0]).get('content')
        print('channel_set is ', channel_set)
        result = []
        for channel in channel_set:
            result.append({k: v for k, v in channel.__dict__.items() if k in APIChannel.table.required_item})
        print('result is ', result)
        return result
    return None


def chose_channel(channels, publick_key, tx_count, asset_type):
    for ch in channels:
        balance = ch.balance
        LOG.debug("balance {}".format(balance))
        if balance:
            try:
                balance_value = balance.get(publick_key).get(asset_type.upper())
            except:
                continue
            if float(balance_value) >= float(tx_count):
                return ch
            else:
                continue


def close_channel(channel_name, wallet):
    ch = Channel.channel(channel_name)
    peer = ch.get_peer(wallet.url)
    # tx = trans.TrinityTransaction(channel_name, wallet)
    # tx.realse_transaction()
    mg.SettleMessage.create(wallet, channel_name, wallet.url, peer, "TNC")  # ToDo


def sync_channel_info_to_gateway(channel_name, type):
    LOG.info("Debug sync_channel_info_to_gateway  channelname {} type {}".format(channel_name, type))
    ch = Channel.channel(channel_name)
    balance = ch.get_balance()
    nb = {}
    for item, value in balance.items():
        if item in ch.founder:
            nb[ch.founder] = value
        else:
            nb[ch.partner] = value

    return sync_channel(type, ch.channel_name, ch.founder, ch.partner, nb)


def udpate_channel_when_setup(address):
    channels = APIChannel.batch_query_channel(filters={"src_addr": address})
    if channels.get("content"):
        for ch in channels["content"]:
            if ch.state == EnumChannelState.OPENED.name:
                sync_channel_info_to_gateway(ch.channel, "UpdateChannel")

    channeld = APIChannel.batch_query_channel(filters={"dest_addr": address})
    if channeld.get("content"):
        for ch in channeld["content"]:
            if ch.state == EnumChannelState.OPENED.name:
                sync_channel_info_to_gateway(ch.channel, "UpdateChannel")


# test state
ws_instance.register_event('test_event', ChannelTestEvent('state', 'TNC', EnumEventType.EVENT_TYPE_TEST_STATE))

if __name__ == "__main__":
    result = APIChannel.query_channel(channel="1BE0FCD56A27AD46C22B8EEDC4E835EA")
    print(result)
    print(dir(result["content"][0]))
    print(result["content"][0].dest_addr)
    print(result["content"][0].src_addr)

    result = APIChannel.batch_query_channel(
        filters={"dest_addr": "022a38720c1e4537332cd6e89548eedb0afbb93c1fdbade42c1299601eaec897f4",
                 "src_addr": "02cebf1fbde4786f031d6aa0eaca2f5acd9627f54ff1c0510a18839946397d3633"})
    print(result)
