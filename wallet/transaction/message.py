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
# system and 3rd party libs
# self modules import
from wallet.utils import get_magic
from common.common import uri_parser
from common.log import LOG
from common.exceptions import GoTo
from wallet.channel import Channel, EnumTradeType, Payment
from wallet.Interface.gate_way import send_message
from .response import EnumResponseStatus
from trinity import IS_SUPPORTED_ASSET_TYPE
from wallet.event import event_machine
from wallet.event.contract_event import ContractEventInterface
from common.number import TrinityNumber

class MessageHeader(object):
    """
        Message header is used for event transaction.
    """
    def __init__(self, sender:str, receiver:str, message_type:str, channel_name:str, asset_type:str, nonce:int):
        # here we could use the regex expression to judge the ip format accurately.
        assert sender.__contains__('@'), 'Invalid sender<{}>.'.format(sender)
        assert receiver.__contains__('@'), 'Invalid receiver<{}>.'.format(receiver)
        assert sender != receiver, 'Sender should be different from receiver.'

        self.message_header = {
            'MessageType':message_type,
            'Sender': sender,
            'Receiver': receiver,
            'TxNonce': str(nonce),
            'ChannelName': channel_name,
            'AssetType': asset_type.upper(),
            'NetMagic': get_magic()
        }


class Message(object):
    """
    {
        'MessageType': 'MessageType',
        'Sender': sender,
        'Receiver': receiver,
        'TxNonce': '0',
        'ChannelName': channel_name,
        'AssetType': 'TNC',
        'NetMagic': magic,
    }

    """
    _SETTLE_NONCE = 0
    _FOUNDER_NONCE = 1
    _message_name = None
    _contract_event_api = None

    def __init__(self, message):
        self.message = message

        self.sender = message.get('Sender')
        self.sender_address, _, _ = uri_parser(self.sender)
        self.receiver = message.get('Receiver')
        self.receiver_address, _, _, = uri_parser(self.receiver)

        self.message_type = message.get('MessageType')
        self.message_body = message.get('MessageBody')
        self.channel_name = message.get('ChannelName')
        self.asset_type = message.get('AssetType','INVALID_ASSET').upper()
        self.nonce = int(message.get('TxNonce'))
        self.net_magic = message.get('NetMagic')
        self.status = message.get('Status')
        self.comments = self.message.get('Comments')

    @property
    def network_magic(self):
        return get_magic()

    @staticmethod
    def send(message):
        send_message(message)

    @staticmethod
    def create_message_header(sender:str, receiver:str, message_type:str, channel_name:str, asset_type:str, nonce:int):
        return MessageHeader(sender, receiver, message_type, channel_name, asset_type, nonce)

    def handle(self):
        LOG.info('Received Message<{}>'.format(self.message_type))
        pass

    @classmethod
    def contract_event_api(cls):
        if not cls._contract_event_api:
            cls._contract_event_api = ContractEventInterface()

        return cls._contract_event_api

    @classmethod
    def sign_content(cls, start=3, *args, **kwargs):
        return cls.contract_event_api().sign_content(start, *args, **kwargs)

    @classmethod
    def check_asset_type(cls, asset_type):
        """

        :param asset_type:
        :return:
        """
        if not IS_SUPPORTED_ASSET_TYPE(asset_type):
            raise GoTo(EnumResponseStatus.RESPONSE_ASSET_TYPE_NOT_SUPPORTED,
                       'Unsupported Asset type: \'{}\''.format(asset_type))

        return True, None

    @classmethod
    def check_url_format(cls, wallet_url):
        """

        :param wallet_url:
        :return:
        """
        # TODO: it's better to use regex expression to check the url's validity
        if not wallet_url.__contains__('@'):
            raise GoTo(EnumResponseStatus.RESPONSE_INVALID_URL_FORMAT,
                       'Invalid format of url<{}>. Should be like 0xYYYY@ip:port'.format(wallet_url))

    @classmethod
    def check_both_urls(cls, sender, receiver):
        """

        :param sender:
        :param receiver:
        :return:
        """
        # check whether the sender and receiver are correct url or not
        # TODO: it's better to use regex expression to check the url's validity
        try:
            return sender.__contains__('@') and receiver.__contains__('@')
        except Exception as error:
            LOG.error('Illegal URL is found. Exception: {}'.format(error))
            raise GoTo(EnumResponseStatus.RESPONSE_INVALID_URL_FORMAT,
                       'Invalid format of sender<{}> or receiver<{}>. Should be like 0xYYYY@ip:port' \
                       .format(sender, receiver))

    @classmethod
    def check_network_magic(cls, magic):
        """

        :param magic:
        :return:
        """
        net_magic = get_magic()
        if net_magic != magic:
            raise GoTo(EnumResponseStatus.RESPONSE_INVALID_NETWORK_MAGIC,
                       'Invalid network ID<{}>. should be equal to {}'.format(magic, net_magic))

        return True, net_magic

    @classmethod
    def check_signature(cls):
        return True

    @classmethod
    def check_nonce(cls, nonce, channel_name=''):
        """

        :param channel_name:
        :param nonce:
        :return:
        """
        new_nonce = Channel.new_nonce(channel_name)

        if not (TransactionBase._FOUNDER_NONCE < int(nonce) == new_nonce):
            GoTo(EnumResponseStatus.RESPONSE_TRADE_WITH_INCOMPATIBLE_NONCE,
                 '{}::Channel<{}> has incompatible nonce<self: {}, peer: {}>'.format(cls.__name__,
                                                                                     channel_name, new_nonce, nonce))
        else:
            return True, new_nonce

    @classmethod
    def calculate_balance_after_payment(cls, balance, peer_balance, payment, hlock_to_rsmc=False, is_htlc_type=False):
        """

        :param balance: payer's balance
        :param peer_balance: payee's balance
        :param payment:
        :param hlock_to_rsmc: exchange htlc lock part to rsmc transaction
        :return:
        """
        # if payment has occurred, calculate the balance after payment
        payment = int(payment)
        if 0 < payment <= int(balance):
            if hlock_to_rsmc:
                return True, int(balance), int(peer_balance) + payment
            elif is_htlc_type:
                return True, int(balance) - payment, int(peer_balance)
            else:
                return True, int(balance) - payment, int(peer_balance) + payment
        elif payment > int(balance):
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_NO_ENOUGH_BALANCE_FOR_PAYMENT,
                       'Sender has not enough balance<{}> for payment<{}>'.format(balance, payment))
        else:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_NEGATIVE_PAYMENT,
                       'Payment<{}> should not be negative number.'.format(payment))

    @classmethod
    def check_balance(cls, channel_name, asset_type, address, balance, peer_address, peer_balance,
                      hlock_to_rsmc=False, is_htcl_type=False, **kwargs):
        """

        :param channel_name:
        :param asset_type:
        :param address: payer's address
        :param balance: payer's balance
        :param peer_address: payee's address
        :param peer_balance: payee's balance
        :param payment:
        :return:
        """
        try:
            # get channel if trade has already existed
            channel_set = Channel.query_channel(channel_name)[0]

            expected_balance = int(channel_set.balance.get(address).get(asset_type))
            expected_peer_balance = int(channel_set.balance.get(peer_address).get(asset_type))

            # to calculate the balance after payment
            if kwargs and kwargs.__contains__('payment'):
                _, expected_balance, expected_peer_balance = \
                    cls.calculate_balance_after_payment(expected_balance, expected_peer_balance,
                                                        kwargs.get('payment'), hlock_to_rsmc, is_htcl_type)

            if int(balance) == expected_balance and int(peer_balance) == expected_peer_balance:
                return True, expected_balance, expected_peer_balance
            else:
                raise GoTo(
                    EnumResponseStatus.RESPONSE_TRADE_BALANCE_UNMATCHED_BETWEEN_PEERS,
                    'Channel<{}> balances are unmatched between channel peers<self: {}, expected: {}. peers: {}, expected: {}>' \
                    .format(channel_name, balance, expected_balance, peer_balance, expected_peer_balance))
        except Exception as error:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_BALANCE_ERROR,
                       'Channel<{}> not found or balance error. Exception: {}'.format(channel_name, error))

    @classmethod
    def common_check(cls, sender, receiver, asset_type, net_magic):
        """

        :param sender:
        :param receiver:
        :param asset_type:
        :param net_magic:
        :return:
        """
        cls.check_asset_type(asset_type)
        cls.check_network_magic(net_magic)
        cls.check_both_urls(sender, receiver)

    def verify(self):
        """

        :return:
        """
        self.common_check(self.sender, self.receiver, self.asset_type, self.net_magic)
        return True, None

    @classmethod
    def check_response_status(cls, status):
        """

        :param status:
        :return:
        """
        if EnumResponseStatus.RESPONSE_OK.name != status:
            LOG.error('Message {} with error status<{}>'.format(cls._message_name, status))
            return False

        return True

    @classmethod
    def send_error_response(cls, sender:str, receiver:str, channel_name:str, asset_type:str,
                       nonce:int, status=EnumResponseStatus.RESPONSE_FAIL):
        message = cls.create_message_header(receiver, sender, cls._message_name, channel_name, asset_type, nonce)
        message = message.message_header
        message.update({'MessageBody': {}})

        if status:
            message.update({'Status': status.name})

        cls.send(message)

class TransactionBase(Message):
    """
        Descriptions: for RSMC or HTLC transaction
    """
    @classmethod
    def check_rcode(cls, hashcode, rcode):
        """

        :param hashcode:
        :param rcode:
        :return:
        """
        if Payment.verify_hr(hashcode, rcode):
            return True
        else:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_HASHR_NOT_MATCHED_WITH_RCODE,
                       'HashR<{}> is not compatible with Rcode<{}>'.format(hashcode, rcode))

    @classmethod
    def check_channel_state(cls, channel_name):
        channel = Channel(channel_name)

        if not channel.is_opened:
            raise GoTo(EnumResponseStatus.RESPONSE_CHANNEL_NOT_OPENED,
                       'Channel is not OPENED. Current tate<{}>'.format(channel.state))

        return channel

    @classmethod
    def check_payment(cls, channel_name, address, asset_type, payment):
        """

        :param channel_name:
        :param address:
        :param asset_type:
        :param payment:
        :return:
        """
        channel_balance = Channel(channel_name).balance
        balance = channel_balance.get(address).get(asset_type.upper())

        if not 0 < int(payment) <= int(balance):
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_NO_ENOUGH_BALANCE_FOR_PAYMENT,
                       'Invalid payment<{}>, payer balance<{}>'.format(payment, balance))

        return True, int(balance)

    @classmethod
    def update_balance_for_channel(cls, channel_name, asset_type, payer_address, payee_address, payment,
                                   is_hlock_to_rsmc=False, is_htlc_type=False):
        """

        :param channel_name:
        :param payer_address:
        :param payee_address:
        :param asset_type:
        :param payment:
        :param is_hlock_to_rsmc:
        :return:
        """
        channel = Channel(channel_name)

        try:
            asset_type = asset_type.upper()
            channel_balance = channel.balance
            channel_hlock = channel.hlock

            # calculate the left balance
            payer_balance = channel_balance.get(payer_address).get(asset_type)
            payee_balance = channel_balance.get(payee_address).get(asset_type)

            if is_hlock_to_rsmc:
                payer_hlock = channel_hlock.get(payer_address).get(asset_type)
                payer_hlock = cls.big_number_calculate(payer_hlock, payment, False)
                if 0 > payer_hlock:
                    raise GoTo(EnumResponseStatus.RESPONSE_TRADE_LOCKED_ASSET_LESS_THAN_PAYMENT,
                               'Why here? Payment<{}> should less than locked asset'.format(payment))
                channel_hlock.update({payer_address: {asset_type: payer_hlock}})
                payee_balance = cls.big_number_calculate(payee_balance, payment)
            elif is_htlc_type:
                payer_hlock = channel_hlock.get(payer_address).get(asset_type)
                payer_hlock = cls.big_number_calculate(payer_hlock, payment)
                channel_hlock.update({payer_address: {asset_type: payer_hlock}})
                payer_balance = cls.big_number_calculate(payer_balance, payment, False)
            else:
                payer_balance = cls.big_number_calculate(payer_balance, payment, False)
                payee_balance = cls.big_number_calculate(payee_balance, payment)

            if payer_balance >= 0 and payee_balance >= 0:
                Channel.update_channel(channel_name,
                                       balance={payer_address: {asset_type: str(payer_balance)},
                                                payee_address: {asset_type: str(payee_balance)}},
                                       hlock=channel_hlock)
            else:
                raise GoTo(EnumResponseStatus.RESPONSE_TRADE_NO_ENOUGH_BALANCE_FOR_PAYMENT,
                           'Payer has not enough balance for this payment<{}>'.format(payment))

        except Exception as error:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_BALANCE_UPDATE_FAILED,
                       'Update channel<{}> balance error. payment<{}>. Exception: {}'.format(channel_name,
                                                                                             payment, error))

    @classmethod
    def big_number_calculate(cls, balance, payment, add=True):
        # calculate
        if add:
            result = int(balance) + int(payment)
        else:
            result = int(balance) - int(payment)

        return result

    @classmethod
    def hashr_is_valid_format(cls, hashcode):
        return isinstance(hashcode, str) and hashcode.startswith('TN')

    @classmethod
    def get_peer(cls, channel_set, source):
        if not channel_set:
            return None
        peer = channel_set.src_addr

        return peer if peer != source else channel_set.dest_addr

    @classmethod
    def rollback_resource(cls, channel_name, nonce, payment=None, status=None):
        """

        :param channel_name:
        :param nonce:
        :param payment:
        :return:
        """
        # failure action
        # if status == EnumResponseStatus.RESPONSE_TRADE_WITH_INCOMPATIBLE_NONCE.name:
        #     Channel.delete_trade(channel_name, int(nonce))

        if status is not None and status != EnumResponseStatus.RESPONSE_OK.name:
            event_machine.unregister_event(channel_name)

    @classmethod
    def is_hlock_to_rsmc(cls, hashcode):
        return hashcode not in [None, Channel._trade_hash_rcode_default]

    @classmethod
    def get_rcode(cls, channel_name, hashcode):
        """

        :param hashcode:
        :return:
        """
        if cls.is_hlock_to_rsmc(hashcode):
            htlc_trade = Channel.batch_query_trade(channel_name,
                                                   filters={'type': EnumTradeType.TRADE_TYPE_HTLC.name,
                                                            'hashcode': hashcode})
            if not htlc_trade:
                raise GoTo(EnumResponseStatus.RESPONSE_TRADE_HASHR_NOT_FOUND,
                           'Htlc trade with HashR<{}> NOT found'.format(hashcode))
            htlc_trade = htlc_trade[0]
            return hashcode, htlc_trade.rcode
        else:
            return Channel._trade_hash_rcode_default, Channel._trade_hash_rcode_default

    @classmethod
    def get_htlc_trade_by_hashr(cls, channel_name, hashcode):
        """

        :param channel_name:
        :param hashcode:
        :return:
        """
        try:
            return Channel.batch_query_trade(channel_name, filters={'type': EnumTradeType.TRADE_TYPE_HTLC.name,
                                                                    'hashcode': hashcode})[0]
        except Exception as error:
            raise GoTo(EnumResponseStatus.RESPONSE_TRADE_HASHR_NOT_FOUND,
                       'Htlc trade not found by the HashR<{}> in channel<{}>'.format(hashcode, channel_name))
