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
import binascii
from wallet.utils import get_magic
from common.common import uri_parser
from common.log import LOG
from common.exceptions import GoTo
from wallet.channel import Channel, EnumTradeType, EnumTradeState, EnumTradeRole, Payment
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
    def __init__(self, sender:str, receiver:str, message_type:str, channel_name:str, asset_type:str, nonce:int,
                 nego_nonce=None):
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

        if nego_nonce and nego_nonce < nonce:
            self.message_header.update({'ResetTxNonce': nego_nonce})


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

        self.message_type = message.get('MessageType', '')
        self.message_body = message.get('MessageBody')
        self.resign_body = self.message_body.get('ResignBody')
        self.channel_name = message.get('ChannelName')
        self.asset_type = message.get('AssetType','INVALID_ASSET').upper()
        self.net_magic = message.get('NetMagic')
        self.status = message.get('Status')
        self.comments = self.message.get('Comments')

        self.nonce = int(message.get('TxNonce'))
        try:
            self.nego_nonce = int(message.get('ResetTxNonce'))
        except:
            self.nego_nonce = None

        # transaction is triggered by command cline
        trigger_by_cli = int(self.message_body.get('TriggeredByCLI', 0))
        self.trigger_by_cli = True if trigger_by_cli else False

    @property
    def network_magic(self):
        return get_magic()

    @staticmethod
    def send(message):
        send_message(message)

    @staticmethod
    def create_message_header(sender:str, receiver:str, message_type:str, channel_name:str, asset_type:str, nonce:int,
                              nego_nonce=None):
        return MessageHeader(sender, receiver, message_type, channel_name, asset_type, nonce, nego_nonce).message_header

    def handle(self):
        LOG.info('Received Message<{}> from<{}> by channel<{}>'.format(self.message_type,
                                                                       self.sender_address,
                                                                       self.channel_name))
        pass

    @classmethod
    def contract_event_api(cls):
        if not cls._contract_event_api:
            cls._contract_event_api = ContractEventInterface()

        return cls._contract_event_api

    @classmethod
    def sign_content(cls, wallet, sign_type_list, sign_value_list, *args, start=3, **kwargs):
        """

        :param wallet:
        :param sign_type_list:
        :param sign_value_list:
        :param args:
        :param start:
        :param kwargs:
        :return:
        """
        if not (wallet and sign_type_list and sign_value_list):
            raise GoTo(
                EnumResponseStatus.RESPONSE_ILLEGAL_INPUT_PARAMETER,
                'Lack of mandatory parameters: wallet<{}>, type_list<{}>, value_list<{}>' \
                    .format(wallet, sign_type_list, sign_value_list)
            )

        kwargs.update({
            'typeList': sign_type_list,
            'valueList': sign_value_list,
            'privtKey': wallet._key.private_key_string

        })

        return cls.contract_event_api().sign_content(start, *args, **kwargs)

    @classmethod
    def check_asset_type(cls, asset_type):
        """

        :param asset_type:
        :return:
        """
        if not IS_SUPPORTED_ASSET_TYPE(asset_type):
            raise GoTo(EnumResponseStatus.RESONSE_ASSET_TYPE_NOT_SUPPORTED,
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
    def check_signature(cls, wallet, expected, type_list, value_list, signature):
        """"""
        if not (wallet and type_list and value_list and signature):
            raise GoTo(
                EnumResponseStatus.RESPONSE_ILLEGAL_INPUT_PARAMETER,
                'Illegal input parameters: type_list<{}>, value_list<{}>, signature<{}>' \
                    .format(type_list, value_list, signature)
            )

        sign_hash =  cls.contract_event_api().solidity_hash(type_list, value_list)
        peer_wallet_address = wallet.recoverHash(sign_hash, signature)

        if expected == peer_wallet_address:
            return True
        else:
            LOG.error('Error data hash<{}> with value<{}> by signature<{}>'.format(binascii.b2a_hex(sign_hash),
                                                                                   value_list, signature))
            raise GoTo(
                EnumResponseStatus.RESPONSE_SIGNATURE_VERIFIED_ERROR,
                'Signature verification error: expected<{}>, parsed-address<{}>'.format(expected, peer_wallet_address)
            )

    @classmethod
    def check_wallet(cls, wallet):
        if not wallet:
            raise GoTo(
                EnumResponseStatus.RESPONSE_COMMON_ERROR_VOID_WALLET,
                'Wallet is NoneType.'
            )
        return True

    @classmethod
    def check_nonce(cls, nonce, channel_name='', is_founder=False):
        """

        :param channel_name:
        :param nonce:
        :return:
        """
        nonce = int(nonce)
        nego_trade = Channel.query_trade(channel_name, nonce)
        pre_trade = Channel.query_trade(channel_name, nonce-1)

        # to check whether the nonce is legal one or not
        if not (TransactionBase._FOUNDER_NONCE < nonce
                and pre_trade.state in [EnumTradeState.confirmed.name, EnumTradeState.confirmed_onchain.name]
                and ((nego_trade.state in [EnumTradeState.init.state] and is_founder)
                or (nego_trade.state in [EnumTradeState.confirming.state] and not is_founder))):
            raise GoTo(
                EnumResponseStatus.RESPONSE_TRADE_WITH_INCOMPATIBLE_NONCE,
                '{}::Channel<{}> has incompatible nonce<{}>, state<previous:{}, negotiated: {}>' \
                    .format(cls.__name__, channel_name, nonce, pre_trade.state, nego_trade.state))
        else:
            return True, nego_trade

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
        :param address:
        :param balance:
        :param peer_address:
        :param peer_balance:
        :param hlock_to_rsmc:
        :param is_htcl_type:
        :param kwargs:
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
                       nonce:int, status=EnumResponseStatus.RESPONSE_FAIL, **kwargs):
        message = cls.create_message_header(receiver, sender, cls._message_name, channel_name, asset_type, nonce)
        message.update({'MessageBody': kwargs})

        if status:
            message.update({'Status': status.name})

        cls.send(message)

class TransactionBase(Message):
    """
        Descriptions: for RSMC or HTLC transaction
    """
    _htlc_sign_type_list = ['bytes32', 'address', 'address', 'uint256', 'uint256', 'bytes32']
    _rsmc_sign_type_list = ['bytes32', 'uint256', 'address', 'uint256', 'address', 'uint256', 'bytes32', 'bytes32']

    def get_payer_and_payee_address(self):
        """"""
        if self.role_index in [-1, 1]:
            self.payer = self.sender
            self.payer_address = self.sender_address
            self.payee = self.receiver
            self.payee_address = self.receiver_address
        else:
            self.payer = self.receiver
            self.payer_address = self.receiver_address
            self.payee = self.sender
            self.payee_address = self.sender_address

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
                channel_hlock.update({payer_address: {asset_type: str(payer_hlock)}})
                payee_balance = cls.big_number_calculate(payee_balance, payment)
            elif is_htlc_type:
                payer_hlock = channel_hlock.get(payer_address).get(asset_type)
                payer_hlock = cls.big_number_calculate(payer_hlock, payment)
                channel_hlock.update({payer_address: {asset_type: str(payer_hlock)}})
                payer_balance = cls.big_number_calculate(payer_balance, payment, False)
            else:
                payer_balance = cls.big_number_calculate(payer_balance, payment, False)
                payee_balance = cls.big_number_calculate(payee_balance, payment)

            if int(payer_balance) >= 0 and int(payee_balance) >= 0:
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
        # For the healthy of the transaction, maybe we need give up the resources roll-back operation

        # if status is not None and status != EnumResponseStatus.RESPONSE_OK.name:
        #     trade = Channel.query_trade(channel_name, nonce)
        #     if trade:
        #         Channel.delete_trade(channel_name, int(nonce))
        pass

    @classmethod
    def is_hlock_to_rsmc(cls, hashcode):
        if isinstance(hashcode, str):
            hashcode = hashcode.strip(' 0x')
        return hashcode not in [None, '']

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
            return cls.get_default_rcode()

    @classmethod
    def get_default_rcode(cls):
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

    @classmethod
    def create_resign_message_body(cls, wallet, channel_name, nonce, is_resign_response=False):
        """

        :param channel_name:
        :param nonce:
        :param is_resign_response: if True, it means has received the peer resign request
        :return:
        """
        if not (channel_name and isinstance(nonce, int)):
            raise GoTo(
                EnumResponseStatus.RESPONSE_ILLEGAL_INPUT_PARAMETER,
                'Illegal parameters: channel_name<{}> or nonce<{}, type:{}>'.format(channel_name, nonce, type(nonce))
            )

        # record the nonce negotiated by partner of the transaction with nonce
        # required is True
        if is_resign_response:
            nego_nonce = nonce
            pre_nonce = nonce
            pre_trade = Channel.query_trade(channel_name, nego_nonce)
        else:
            pre_trade, pre_nonce = Channel.latest_valid_trade(channel_name)
            nego_nonce = pre_nonce + 1 if isinstance(pre_nonce, int) else None

        # does founder practise fraud ???
        if not (pre_trade and nego_nonce) or cls._FOUNDER_NONCE >= nego_nonce:
            raise GoTo(
                EnumResponseStatus.RESPONSE_TRADE_WITH_INCORRECT_NONCE,
                'Could not finish this transaction because '
            )

        # initialize some local variables
        trade_role = pre_trade.role
        trade_type = pre_trade.type
        trade_state = pre_trade.state

        # local variables
        resign_body = {'Nonce' : str(pre_nonce)}
        need_update_balance = False

        # is partner role of this transaction
        if EnumTradeRole.TRADE_ROLE_PARTNER.name == trade_role and EnumTradeState.confirming.name == trade_state:
            # update the resign_body by the different trade type
            if EnumTradeType.TRADE_TYPE_RSMC.name == trade_type:
                if pre_trade.peer_commitment:
                    # update the trade to confirmed state directly
                    Channel.update_trade(channel_name, pre_nonce, state=EnumTradeState.confirmed.name)

                    # need update channel balance
                    need_update_balance = True
                else:
                    # need resign this RSMC transaction by peer
                    resign_body.update({'Commitment': pre_trade.commitment})
            elif EnumTradeType.TRADE_TYPE_HTLC.name == trade_type:
                if pre_trade.peer_commitment and pre_trade.peer_delay_commitment:
                    # update the trade to confirmed state directly
                    Channel.update_trade(channel_name, pre_nonce, state=EnumTradeState.confirming.name)
                    # need update channel balance
                    need_update_balance = True
                else:
                    # need resign this HTLC transaction by peer
                    resign_body.update({'Commitment': pre_trade.commitment})
                    resign_body.update({'DelayCommitment': pre_trade.delay_commitment})
            else:
                LOG.error('Unsupported trade type<{}> to resign in partner<{}> side'
                          .format(trade_type, wallet.url))
                return None, pre_trade

            # need update the channel balance or not???
            if need_update_balance:
                channel = Channel(channel_name)
                self_address, _, _ = uri_parser(wallet.url)
                peer_address, _, _ = uri_parser(channel.peer_uri(wallet.url))

                # ToDo: if need, here need add asset type check in future
                Channel.update_channel(channel_name, balance={
                    self_address: {pre_trade.asset_type: pre_trade.balance},
                    peer_address: {pre_trade.asset_type: pre_trade.peer_balance}
                })
        elif is_resign_response is True and EnumTradeRole.TRADE_ROLE_FOUNDER.name == trade_role and \
                (EnumTradeState.confirmed.name == trade_state or (EnumTradeState.confirming.name == trade_state and
                                                                  EnumTradeType.TRADE_TYPE_HTLC.name == trade_type)):

            if EnumTradeType.TRADE_TYPE_RSMC.name == trade_type:
                if pre_trade.peer_commitment:
                    resign_body.update({'Commitment': pre_trade.commitment})
                else:
                    # stop transaction ????
                    pass
            elif EnumTradeType.TRADE_TYPE_HTLC.name == trade_type:
                if pre_trade.peer_commitment and pre_trade.peer_delay_commitment:
                    resign_body.update({'Commitment': pre_trade.commitment})
                    resign_body.update({'DelayCommitment': pre_trade.delay_commitment})
            else:
                LOG.error('Unsupported trade type<{}> to resign in founder<{}> side'
                          .format(trade_type, wallet.url))
                return None, pre_trade
        else:
            return None, pre_trade

        # Previous transaction need to be resigned by peer
        if 'Commitment' in resign_body:
            return resign_body, pre_trade

        return None, pre_trade

    @classmethod
    def handle_resign_body(cls, wallet, channel_name, resign_body):
        """"""
        if not resign_body:
            return None

        if not (wallet and channel_name):
            raise GoTo(
                EnumResponseStatus.RESPONSE_ILLEGAL_INPUT_PARAMETER,
                'Void wallet<{}> or Illegal channel name<{}>'.format(wallet, channel_name)
            )

        resign_nonce = int(resign_body.get('Nonce'))
        update_channel_db = {}
        update_trade_db = {}

        # get transaction by the resign_nonce
        resign_trade = Channel.query_trade(channel_name, resign_nonce)
        asset_type = resign_trade.asset_type

        channel = Channel(channel_name)
        self_address, _, _ = uri_parser(wallet.url)
        peer_address, _, _ = uri_parser(channel.peer_uri(wallet.url))

        # Is this wallet sender side of this trade ?????
        if EnumTradeRole.TRADE_ROLE_PARTNER.name == resign_trade.role:
            payer_address = peer_address
            payee_address = self_address
            payer_balance = resign_trade.peer_balance
            payee_balance = resign_trade.balance
        elif EnumTradeRole.TRADE_ROLE_FOUNDER.name == resign_trade.role:
            payer_address = self_address
            payee_address = peer_address
            payer_balance = resign_trade.balance
            payee_balance = resign_trade.peer_balance
        else:
            raise GoTo(
                EnumResponseStatus.RESPONSE_DATABASE_ERROR_TRADE_ROLE,
                'Error trade role<{}> for nonce<{}>'.format(resign_trade.role, resign_nonce)
            )

        if EnumTradeType.TRADE_TYPE_HTLC.name == resign_trade.type:
            rsmc_sign_hashcode, rsmc_sign_rcode = cls.get_default_rcode()
        elif EnumTradeType.TRADE_TYPE_RSMC.name == resign_trade.type:
            rsmc_sign_hashcode, rsmc_sign_rcode = resign_trade.hashcode, resign_trade.rcode
        else:
            raise GoTo(
                EnumResponseStatus.RESPONSE_TRADE_RESIGN_NOT_SUPPORTED_TYPE,
                'Only support HTLC and RSMC resign. Current transaction type: {}'.format(resign_trade.type)
            )

        rsmc_list = [channel_name, resign_nonce, payer_address, int(payer_balance),
                     payee_address, int(payee_balance), rsmc_sign_hashcode, rsmc_sign_rcode]

        # self commitment is None
        if not resign_trade.commitment:
            commitment = cls.sign_content( wallet, cls._rsmc_sign_type_list, rsmc_list)
            update_trade_db.update({'commitment': commitment})

        # self lock commitment is none
        htlc_list = None
        if EnumTradeType.TRADE_TYPE_HTLC.name == resign_trade.type:
            htlc_list = [channel_name, payer_address, payee_address, int(resign_trade.delay_block),
                         int(resign_trade.payment), resign_trade.hashcode]
            delay_commitment = cls.sign_content(wallet, cls._htlc_sign_type_list, htlc_list)
            update_trade_db.update({'delay_commitment': delay_commitment})

        # check whether the trade need update or not
        if resign_trade.state not in [EnumTradeState.confirmed.name, EnumTradeState.confirmed_onchain.name]:
            peer_commitment = resign_body.get('Commitment')
            peer_delay_commitment = resign_body.get('DelayCommitment')

            # check peer signature
            cls.check_signature(wallet, peer_address, cls._rsmc_sign_type_list, rsmc_list, peer_commitment)

            # update transaction and channel balance
            update_trade_db.update({'peer_commitment': peer_commitment})
            update_channel_db = {
                'balance': {
                    payer_address: {asset_type: payer_balance},
                    payee_address: {asset_type: payee_balance}
                }
            }

            # check the htlc part signature
            if EnumTradeType.TRADE_TYPE_HTLC.name == resign_trade.type:
                cls.check_signature(wallet, peer_address, cls._htlc_sign_type_list,
                                    htlc_list, peer_delay_commitment)
                update_trade_db.update({'peer_delay_commitment': peer_delay_commitment})
                update_trade_db.update({'state': EnumTradeState.confirming.name})

                # need update the hlock part
                if payer_address == self_address:
                    channel = Channel(channel_name)
                    channel_hlock = channel.hlock
                    if channel_hlock and channel_hlock.get(payer_address):
                        payer_hlock = int(resign_trade.payment) + int(channel_hlock.get(payer_address).get(asset_type))
                        channel_hlock.update({payer_address: {asset_type: str(payer_hlock)}})
                        update_channel_db.update({'hlock': channel_hlock})
            else: # RSMC type transaction
                update_trade_db.update({'state': EnumTradeState.confirmed.name})

            # update transaction
            Channel.update_trade(channel_name, resign_nonce, **update_trade_db)

            # update Channel balance to new one
            Channel.update_channel(channel_name, **update_channel_db)

        # return resign message body
        return cls.create_resign_message_body(channel_name, resign_nonce, True)

    def validate_negotiated_nonce(self):
        """

        :return:
        """
        # to validate the negotiated nonce
        valid_trade, valid_nonce = Channel.latest_valid_trade(self.channel_name)

        if valid_nonce and valid_nonce+1 == self.nego_nonce:
            return valid_trade
        else:
            raise GoTo(
                EnumResponseStatus.RESPONSE_TRADE_COULD_NOT_BE_OVERWRITTEN,
                'Could not use negotiated nonce <{}>, current valid nonce<{}>'.format(self.nego_nonce, valid_nonce)
            )
    
    def record_transaction(self, nonce, **update_args):
        """
        
        :param nonce:
        :param update_args:
        :return:
        """
        # check the trade with nonce existed or not
        try:
            new_trade = Channel.query_trade(self.channel_name, nonce)
        except Exception as error:
            new_trade = None

        # add new transaction
        if new_trade:
            Channel.update_trade(self.channel_name, nonce=nonce, **update_args)
        else:
            Channel.add_trade(self.channel_name, nonce=nonce, **update_args)

        return

    def validate_transaction(self):
        """

        :return:
        """
        # check the trade with nonce existed or not
        try:
            pre_trade = Channel.query_trade(self.channel_name, self.nonce-1)
        except Exception as error:
            # should never go here
            raise(
                EnumResponseStatus.RESPONSE_TRADE_NOT_FOUND,
                'Transaction with nonce<{}> is not found'.format(self.nonce-1)
            )
        else:
            if pre_trade.state in [EnumTradeState.confirmed.name or EnumTradeState.confirmed_onchain.name]:
                return True
            elif pre_trade.state in [EnumTradeState.confirming.name] \
                    and EnumTradeType.TRADE_TYPE_HTLC.name == pre_trade.type \
                    and pre_trade.peer_commitment and pre_trade.peer_delay_commitment:
                return True

            raise GoTo(
                EnumResponseStatus.RESPONSE_TRADE_RESIGN_REQUEST_NOT_IMPLEMENTED,
                'Wait for next resign. current confirmed nonce<{}>, request nonce<{}>'.format(
                    Channel.latest_confirmed_nonce(), self.nonce)
            )
