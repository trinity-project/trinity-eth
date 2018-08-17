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
import hashlib
import time
from .trade import EnumTradeState
from model.channel_model import APIChannel
from model.base_enum import EnumChannelState
from model.transaction_model import APITransaction
from model.payment_model import APIPayment
from wallet.utils import convert_number_auto
from wallet.Interface.gate_way import sync_channel
from common.console import console_log
from common.common import LOG
import json


class Channel(object):
    """

    """
    def __init__(self, channel_name):
        self.channel_name = channel_name

        # private variables
        self.__channel_set = None

    @property
    def channel_set(self):
        # to decrease times to query database, here do some special operations
        if self.__channel_set:
            return self.__channel_set

        try:
            self.__channel_set = APIChannel.query_channel(channel=self.channel_name)[0]
        except Exception as error:
            LOG.warning('No opened channel exists, Error: {}'.format(error))
            return None

        return self.__channel_set

    def is_founder(self, uri):
        return self.founder_uri == uri

    @staticmethod
    def new_channel_name(founder, partner):
        timestamp = time.time().__str__().encode()

        md5_part1 = hashlib.md5(founder.encode())
        md5_part1.update(timestamp)

        md5_part2 = hashlib.md5(partner.encode())
        md5_part2.update(timestamp)

        return '0x' + md5_part1.hexdigest().lower() + md5_part2.hexdigest().lower()

    @classmethod
    def exists(cls, founder, partner):
        """

        :param founder: URL of channel founder
        :param partner: URL of channel partner
        :return:
        """
        # judge whether the channel exist or not
        if Channel.get_channel(founder, partner, EnumChannelState.OPENED):
            console_log.warning('OPENED channel already exists.')
            return False
        else:
            # creating channel is ongoing
            # channel = Channel.get_channel(founder, partner, EnumChannelState.OPENING)
            # if :
            #     console.warning('Channel {} is on the way. Please try later if failed')
            #     return
            pass

        return True

    @classmethod
    def get_channel(cls, address1, address2, state=None):
        channels = []
        filter_list = [{'src_addr': address1, 'dest_addr': address2},
                       {'src_addr': address2, 'dest_addr': address1}]

        for filter_item in filter_list:
            if state:
                filter_item.update({'state': state.name})

            try:
                temp_channel = APIChannel.batch_query_channel(filters=filter_item)
                print(filter_item, temp_channel)
                channels.extend(APIChannel.batch_query_channel(filters=filter_item))
            except Exception as error:
                LOG.debug('Batch query channels from DB error: {}'.format(error))

        return channels

    @staticmethod
    def get_channel_list(address, **kwargs):
        """

        :param address:
        :param kwargs:
        :return:
        """
        filter_src = {'src_addr':address}
        filter_dest = {'dest_addr':address}

        output_text = ''
        for key, value in kwargs.items():
            if value:
                filter_dest.update({key:value})
                filter_src.update({key:value})

                output_text += ' {} {}'.format(key, value)

        console_log.info('Get Channels with Address {}{}'.format(address, output_text))

        channels = APIChannel.batch_query_channel(filters=filter_src)
        for ch in channels:
            console_log.info('=='*10,'\nChannelName:', ch.channel, '\nState:', ch.state, '\nPeer:', ch.dest_addr,
                  '\nBalance:', json.dumps(ch.balance, indent=1))

        channels = APIChannel.batch_query_channel(filters=filter_dest)
        for ch in channels:
            console_log.info('=='*10,'\nChannelName:', ch.channel, '\nState:', ch.state, '\nPeer:', ch.src_addr,
                  '\nBalance:', json.dumps(ch.balance, indent=1))

    @property
    def state(self):
        return self.channel_set.state

    @property
    def founder_uri(self):
        return self.channel_set.src_addr

    @property
    def partner_uri(self):
        return self.channel_set.dest_addr

    def peer_uri(self, uri):
        return self.partner_uri if self.is_founder(uri) else self.founder_uri

    @property
    def balance(self):
        return self.channel_set.balance

    @property
    def deposit(self):
        return self.channel_set.deposit

    def to_dict(self):
        return {
            'ChannelName': self.channel_name,
            'Founder': self.founder_uri,
            'Parterner': self.partner_uri,
            'State': self.state,
            'Deposit': self.deposit,
            'Balance': self.balance
        }

    @staticmethod
    def add_channel(**kwargs):
        if kwargs.get('channel') is None:
            LOG.error('MUST specified the key parameter \'channel\'')
            return False
        kwargs.update({'alive_block': 0})
        return APIChannel.add_channel(**kwargs)

    @staticmethod
    def query_channel(channel_name, *args, **kwargs):
        return APIChannel.query_channel(channel_name, *args, **kwargs)

    @staticmethod
    def update_channel(channel_name, **kwargs):
        return APIChannel.update_channel(channel_name, **kwargs)

    @staticmethod
    def delete_channel(channel_name):
        return APIChannel.delete_channel(channel_name)

    @staticmethod
    def add_trade(channel_name, *args, **kwargs):
        """"""
        return APITransaction(channel_name).add_transaction(*args, **kwargs)

    @staticmethod
    def update_trade(channel_name, nonce:int or float, **kwargs):
        return APITransaction(channel_name).update_transaction(nonce, **kwargs)

    @staticmethod
    def query_trade(channel_name, nonce, *args, **kwargs):
        return APITransaction(channel_name).query_transaction(int(nonce), *args, **kwargs)

    @staticmethod
    def batch_query_trade(channel_name, filters, *args, **kwargs):
        return APITransaction(channel_name).batch_query_transaction({}, *args, **kwargs)

    @staticmethod
    def add_payment(channel_name, hashcode='', rcode='', payment=0, state=EnumTradeState.confirming, **kwargs):
        return APIPayment(channel_name).add_payment(hashcode=hashcode, rcode=rcode, channel=channel_name,
                                                    payment=payment, state=state.name, **kwargs)

    @staticmethod
    def update_payment(channel_name, hashcode, **kwargs):
        return APIPayment(channel_name).update_payment(hashcode, **kwargs)

    @staticmethod
    def query_payment(channel_name, hashcode, *args, **kwargs):
        return APIPayment(channel_name).query_payment(hashcode, *args, **kwargs)

    @staticmethod
    def latest_trade(channel_name):
        try:
            trade = APITransaction(channel_name).sort(key='nonce')[0]
        except Exception as error:
            LOG.error('No transaction records were found for channel<{}>. Exception: {}'.format(channel_name, error))
            return None
        else:
            return trade

    @classmethod
    def create(cls, wallet, founder, partner, asset_type, deposit, partner_deposit=None, comments=None,
               trigger=None, cli=True):
        """
            Provide one method to be called by the wallet prompt console.
        :param wallet:
        :param partner:
        :param asset_type:
        :param deposit:
        :param partner_deposit:
        :param comments:
        :param cli:
        :return:
        """
        if not (wallet and partner and asset_type and deposit):
            LOG.error('Invalid parameters:',
                      'wallet<{}>, founder<{}>, partner<{}>, asset_type<{}>, deposit<{}>'.format(wallet,
                                                                                                 founder, partner,
                                                                                                 asset_type,
                                                                                                 deposit))
            # here we could use some hooks to register event to handle output console ????
            console_log.error('Illegal mandatory parameters. Please check in your command.')
            return False

        # use deposit as default value for both partners if partner's deposit is not set:
        if not partner_deposit:
            partner_deposit = deposit

        # judge whether the channel exist or not
        if Channel.get_channel(founder, partner, EnumChannelState.OPENED):
            console_log.warning('OPENED channel already exists.')
            return False
        else:
            # creating channel is ongoing
            # channel = Channel.get_channel(founder, partner, EnumChannelState.OPENING)
            # if :
            #     console.warning('Channel {} is on the way. Please try later if failed')
            #     return
            pass

        channel_name = cls.new_channel_name(founder, partner)
        if cli:
            deposit = convert_number_auto(asset_type.upper(), deposit)
            partner_deposit = convert_number_auto(asset_type.upper(), partner_deposit)
            if 0 >= deposit or 0 >= partner_deposit:
                LOG.error('Could not register channel because of illegal deposit<{}:{}>.'.format(deposit,
                                                                                                 partner_deposit))
                return False

            try:
                trigger(channel_name, founder, partner, asset_type, deposit, partner_deposit, wallet, comments)
            except Exception as error:
                LOG.info('Create channel<{}> failed. Exception: {}'.format(channel_name, error))
                return False

        return True

    # transaction related
    @classmethod
    def transfer(cls, channel_name, wallet, receiver, asset_type, count, hashcode=None, cli=False,
                 router=None, next_jump=None, trigger=None):
        """

        :param sender:
        :param receiver:
        :param asset_type:
        :param count:
        :param hash_random:
        :param wallet:
        :return:
        """
        if router:
            # HTLC transaction
            trigger(channel_name, wallet, wallet.url, receiver, asset_type, count, hashcode, router, next_jump)
        else:
            # RSMC transaction
            trigger(channel_name, wallet, wallet.url, receiver, count, asset_type, cli, comments=hashcode)

        return

    @classmethod
    def quick_close(cls, channel_name, wallet=None, cli=False, trigger=None):
        try:
            channel = cls.query_channel(channel_name)[0]
        except Exception as error:
            if cli :
                console_log.error('Channel {} not found'.format(channel_name))
            LOG.error('Failed to close channel<{}>, Exception: {}'.format(channel_name, error))
        else:
            receiver = channel.src_addr
            if wallet.url == receiver:
                receiver = channel.dest_addr
            trigger(wallet, channel_name, wallet.url, receiver, 'TNC')

    @classmethod
    def founder_or_rsmc_trade(cls, role, asset_type, payment, balance, peer_balance, commitment=None, peer_commitment=None,
                              state=EnumTradeState.confirming):
        asset_type = asset_type.upper()
        return {
            'role': role.name,
            'asset_type': asset_type.upper(),
            'payment': float(payment),
            'balance': float(balance),
            'peer_balance': float(peer_balance),
            'commitment': commitment,
            'peer_commitment': peer_commitment,
            'state': state.name
        }

    @classmethod
    def htlc_trade(cls, role, asset_type, hashcode, rcode, payment, delay_block,
                   commitment=None, peer_commitment=None, state=EnumTradeState.confirming):
        asset_type = asset_type.upper()
        return {
            hashcode: {
                'role': role.name,
                'asset_type': asset_type.upper(),
                'rcode': rcode,
                'payment': float(payment),
                'delay_block': float(delay_block),
                'commitment': commitment,
                'peer_commitment': peer_commitment,
                'state': state.name,
            }
        }


def filter_channel_via_address(address1, address2, state=None):
    channel = Channel.get_channel(address1, address2, state)
    return channel


def get_channel_via_name(params):
    print('enter get_channel_via_name', params)
    if params:
        channel_set = APIChannel.batch_query_channel(filters=params[0])
        result = []
        for channel in channel_set:
            result.append({k: v for k, v in channel.__dict__.items() if k in APIChannel.table.required_item})
        print('result is ', result)
        return result
    return None


def sync_channel_info_to_gateway(channel_name, type, asset_type='TNC'):
    LOG.info("Debug sync_channel_info_to_gateway  channel {} type {}".format(channel_name, type))
    ch = Channel(channel_name)
    if not ch:
        return None

    balance = ch.balance
    nb = {}
    for item, value in balance.items():
        if ch.founder_uri.__contains__(item):
            nb[ch.founder_uri] = value
        else:
            nb[ch.partner_uri] = value

    return sync_channel(type, ch.channel_name, ch.founder_uri, ch.partner_uri, nb, asset_type)


def udpate_channel_when_setup(address):
    channels = APIChannel.batch_query_channel(filters={"src_addr": address})
    for ch in channels:
        if ch.state == EnumChannelState.OPENED.name:
            sync_channel_info_to_gateway(ch.channel, "UpdateChannel")

    channeld = APIChannel.batch_query_channel(filters={"dest_addr": address})
    for ch in channeld:
        if ch.state == EnumChannelState.OPENED.name:
            sync_channel_info_to_gateway(ch.channel, "UpdateChannel")

